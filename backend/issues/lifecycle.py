"""Validated issue status transitions — single source of truth for the state machine."""

from django.utils import timezone

from .models import Issue, IssueStatusHistory

# Allowed directed edges in the lifecycle graph.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    Issue.Status.REPORTED: {
        Issue.Status.UNDER_REVIEW,
        Issue.Status.REJECTED,
    },
    Issue.Status.UNDER_REVIEW: {
        Issue.Status.VERIFIED,
        Issue.Status.REJECTED,
        Issue.Status.REPORTED,  # send back for clarification
    },
    Issue.Status.VERIFIED: {
        Issue.Status.ASSIGNED,
        Issue.Status.REJECTED,
    },
    Issue.Status.ASSIGNED: {
        Issue.Status.IN_PROGRESS,
        Issue.Status.VERIFIED,  # unassign / reassign path resets via service
    },
    Issue.Status.IN_PROGRESS: {
        Issue.Status.RESOLVED,
        Issue.Status.ASSIGNED,
    },
    Issue.Status.RESOLVED: set(),  # terminal
    Issue.Status.REJECTED: set(),  # terminal
}


class InvalidTransition(Exception):
    def __init__(self, current: str, target: str):
        self.current = current
        self.target = target
        super().__init__(f"Cannot transition from {current} to {target}.")


def can_transition(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def apply_transition(
    issue: Issue,
    new_status: str,
    actor,
    comment: str = "",
    *,
    save_issue: bool = True,
) -> IssueStatusHistory:
    """
    Validate and apply a status change, appending history.
    Caller should wrap in transaction.atomic() when combining with other writes.
    """
    previous = issue.status
    if previous == new_status:
        raise InvalidTransition(previous, new_status)
    if not can_transition(previous, new_status):
        raise InvalidTransition(previous, new_status)

    issue.status = new_status
    if new_status == Issue.Status.RESOLVED:
        issue.resolved_at = timezone.now()
    if save_issue:
        issue.save(update_fields=["status", "resolved_at", "updated_at"])

    return IssueStatusHistory.objects.create(
        issue=issue,
        previous_status=previous,
        new_status=new_status,
        actor=actor,
        comment=comment,
    )
