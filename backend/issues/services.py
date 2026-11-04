"""
Issue domain services — business logic lives here, not in views/serializers.
"""

from __future__ import annotations

import logging

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from analytics.cache_metrics import invalidate_dashboard_caches
from notifications.dispatch import dispatch_notification
from teams.models import TeamAssignment

from .duplicates import draft_fingerprint, find_duplicates, persist_candidates
from .lifecycle import InvalidTransition, apply_transition
from .models import Issue, IssueImage, IssueStatusHistory, IssueSupport
from .priority import refresh_priority

logger = logging.getLogger("cityfix")


def check_duplicates_for_draft(data: dict) -> list[dict]:
    candidates = find_duplicates(
        category=data["category"],
        title=data["title"],
        description=data["description"],
        latitude=float(data["latitude"]),
        longitude=float(data["longitude"]),
    )
    fp = draft_fingerprint(
        data["category"],
        data["title"],
        data["description"],
        float(data["latitude"]),
        float(data["longitude"]),
    )
    persist_candidates(candidates, fingerprint=fp)
    return [
        {
            "public_id": str(c.issue.public_id),
            "title": c.issue.title,
            "status": c.issue.status,
            "category": c.issue.category,
            "address": c.issue.address,
            "support_count": c.issue.support_count,
            "score": c.score,
            "distance_meters": c.distance_meters,
            "text_similarity": c.text_similarity,
        }
        for c in candidates
    ]


@transaction.atomic
def create_issue(*, reporter, data: dict, image=None, force: bool = False) -> tuple[Issue, list[dict]]:
    suggestions = check_duplicates_for_draft(data)
    if suggestions and not force:
        return None, suggestions  # type: ignore[return-value]

    issue = Issue.objects.create(
        title=data["title"],
        description=data["description"],
        category=data["category"],
        severity=data.get("severity", Issue.Severity.MODERATE),
        latitude=data["latitude"],
        longitude=data["longitude"],
        address=data.get("address", ""),
        reporter=reporter,
        status=Issue.Status.REPORTED,
    )
    refresh_priority(issue)

    IssueStatusHistory.objects.create(
        issue=issue,
        previous_status="",
        new_status=Issue.Status.REPORTED,
        actor=reporter,
        comment="Issue reported by citizen",
    )

    if image:
        IssueImage.objects.create(
            issue=issue,
            image=image,
            kind=IssueImage.Kind.EVIDENCE,
            uploaded_by=reporter,
        )

    # Link duplicate candidates to the new issue if forced create
    if suggestions:
        candidates = find_duplicates(
            category=issue.category,
            title=issue.title,
            description=issue.description,
            latitude=float(issue.latitude),
            longitude=float(issue.longitude),
            exclude_issue_id=issue.id,
        )
        persist_candidates(candidates, source_issue=issue)

    invalidate_dashboard_caches()
    dispatch_notification(
        recipient_id=reporter.id,
        kind="ISSUE_REPORTED",
        title="Issue reported",
        message=f"Your report '{issue.title}' was submitted successfully.",
        issue_id=issue.id,
    )
    return issue, suggestions


@transaction.atomic
def support_issue(*, issue: Issue, user, note: str = "") -> IssueSupport:
    if issue.status in (Issue.Status.RESOLVED, Issue.Status.REJECTED):
        raise ValidationError("Cannot support a closed issue.")
    if issue.reporter_id == user.id:
        raise ValidationError("You cannot support your own issue.")

    support, created = IssueSupport.objects.get_or_create(
        issue=issue,
        user=user,
        defaults={"note": note},
    )
    if not created:
        raise ValidationError("You already support this issue.")

    issue.support_count = issue.supports.count()
    issue.save(update_fields=["support_count", "updated_at"])
    refresh_priority(issue)
    invalidate_dashboard_caches()

    dispatch_notification(
        recipient_id=issue.reporter_id,
        kind="SUPPORT_ADDED",
        title="Someone supported your issue",
        message=f"{user.username} supported '{issue.title}'.",
        issue_id=issue.id,
    )
    return support


@transaction.atomic
def transition_issue(*, issue: Issue, new_status: str, actor, comment: str = "") -> Issue:
    try:
        apply_transition(issue, new_status, actor, comment)
    except InvalidTransition as exc:
        raise ValidationError(str(exc)) from exc

    invalidate_dashboard_caches()
    dispatch_notification(
        recipient_id=issue.reporter_id,
        kind="STATUS_UPDATED",
        title="Issue status updated",
        message=f"'{issue.title}' is now {new_status}.",
        issue_id=issue.id,
    )
    if new_status == Issue.Status.VERIFIED:
        dispatch_notification(
            recipient_id=issue.reporter_id,
            kind="ISSUE_VERIFIED",
            title="Issue verified",
            message=f"Your report '{issue.title}' was verified.",
            issue_id=issue.id,
        )
    if new_status == Issue.Status.RESOLVED:
        dispatch_notification(
            recipient_id=issue.reporter_id,
            kind="ISSUE_RESOLVED",
            title="Issue resolved",
            message=f"Your report '{issue.title}' has been marked resolved.",
            issue_id=issue.id,
        )
    return issue


@transaction.atomic
def assign_team(*, issue: Issue, team, actor, notes: str = "") -> TeamAssignment:
    """
    Concurrency-safe assignment using select_for_update + unique active constraint.

    Two admins racing will serialize on the row lock; the second either updates
    via deactivate+create or hits IntegrityError which we surface cleanly.
    """
    locked = Issue.objects.select_for_update().get(pk=issue.pk)

    if locked.status not in (
        Issue.Status.VERIFIED,
        Issue.Status.ASSIGNED,
        Issue.Status.UNDER_REVIEW,
    ):
        # Allow assign from VERIFIED primarily; UNDER_REVIEW can be verified+assigned
        if locked.status == Issue.Status.REPORTED:
            apply_transition(locked, Issue.Status.UNDER_REVIEW, actor, "Auto-review before assign", save_issue=True)
            locked.refresh_from_db()
        if locked.status == Issue.Status.UNDER_REVIEW:
            apply_transition(locked, Issue.Status.VERIFIED, actor, "Verified during assignment", save_issue=True)
            locked.refresh_from_db()

    if locked.status not in (Issue.Status.VERIFIED, Issue.Status.ASSIGNED):
        raise ValidationError(
            f"Cannot assign team while issue is in status {locked.status}."
        )

    # Deactivate any existing active assignment (reassign path)
    TeamAssignment.objects.filter(issue=locked, is_active=True).update(is_active=False)

    try:
        assignment = TeamAssignment.objects.create(
            issue=locked,
            team=team,
            assigned_by=actor,
            notes=notes,
            is_active=True,
        )
    except IntegrityError as exc:
        raise ValidationError(
            "Another administrator already assigned this issue. Refresh and try again."
        ) from exc

    locked.assigned_team = team
    locked.save(update_fields=["assigned_team", "updated_at"])

    if locked.status == Issue.Status.VERIFIED:
        apply_transition(locked, Issue.Status.ASSIGNED, actor, f"Assigned to {team.name}")
    elif locked.status == Issue.Status.ASSIGNED:
        IssueStatusHistory.objects.create(
            issue=locked,
            previous_status=Issue.Status.ASSIGNED,
            new_status=Issue.Status.ASSIGNED,
            actor=actor,
            comment=f"Reassigned to {team.name}",
        )

    invalidate_dashboard_caches()

    # Notify team members
    for member in team.members.all():
        dispatch_notification(
            recipient_id=member.id,
            kind="TEAM_ASSIGNED",
            title="New assignment",
            message=f"Team '{team.name}' was assigned to '{locked.title}'.",
            issue_id=locked.id,
        )
    dispatch_notification(
        recipient_id=locked.reporter_id,
        kind="TEAM_ASSIGNED",
        title="Maintenance team assigned",
        message=f"Team '{team.name}' was assigned to your report '{locked.title}'.",
        issue_id=locked.id,
    )
    return assignment


@transaction.atomic
def accept_assignment(*, issue: Issue, user) -> TeamAssignment:
    if not user.maintenance_teams.filter(pk=issue.assigned_team_id).exists():
        raise PermissionDenied("You are not a member of the assigned team.")

    locked = Issue.objects.select_for_update().get(pk=issue.pk)
    assignment = (
        TeamAssignment.objects.select_for_update()
        .filter(issue=locked, is_active=True)
        .first()
    )
    if not assignment:
        raise ValidationError("No active assignment found.")

    assignment.accepted_by = user
    assignment.accepted_at = timezone.now()
    assignment.save(update_fields=["accepted_by", "accepted_at"])

    if locked.status == Issue.Status.ASSIGNED:
        apply_transition(locked, Issue.Status.IN_PROGRESS, user, "Assignment accepted")

    invalidate_dashboard_caches()
    return assignment


@transaction.atomic
def resolve_issue(*, issue: Issue, user, notes: str = "", image=None) -> Issue:
    locked = Issue.objects.select_for_update().get(pk=issue.pk)

    if user.role == "MAINTENANCE":
        if not user.maintenance_teams.filter(pk=locked.assigned_team_id).exists():
            raise PermissionDenied("Not assigned to this issue's team.")
    elif user.role not in ("ADMIN",) and not user.is_superuser:
        raise PermissionDenied("Only maintenance staff or admins can resolve.")

    locked.resolution_notes = notes
    locked.save(update_fields=["resolution_notes", "updated_at"])

    if image:
        IssueImage.objects.create(
            issue=locked,
            image=image,
            kind=IssueImage.Kind.COMPLETION,
            uploaded_by=user,
        )

    apply_transition(locked, Issue.Status.RESOLVED, user, notes or "Marked resolved")

    assignment = TeamAssignment.objects.filter(issue=locked, is_active=True).first()
    if assignment:
        assignment.completed_at = timezone.now()
        assignment.is_active = False
        assignment.save(update_fields=["completed_at", "is_active"])

    invalidate_dashboard_caches()
    return locked


def set_priority_manual(*, issue: Issue, priority: str, actor) -> Issue:
    if priority not in Issue.Priority.values:
        raise ValidationError("Invalid priority.")
    issue.priority = priority
    issue.save(update_fields=["priority", "updated_at"])
    IssueStatusHistory.objects.create(
        issue=issue,
        previous_status=issue.status,
        new_status=issue.status,
        actor=actor,
        comment=f"Priority manually set to {priority}",
    )
    invalidate_dashboard_caches()
    return issue
