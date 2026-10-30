from django.conf import settings
from django.db import models


class MaintenanceTeam(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="maintenance_teams",
        blank=True,
        limit_choices_to={"role": "MAINTENANCE"},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class TeamAssignment(models.Model):
    """
    One active assignment per issue is enforced by a partial unique constraint
    on (issue) where is_active=True — concurrency safety for admin assigns.
    """

    issue = models.ForeignKey(
        "issues.Issue",
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    team = models.ForeignKey(
        MaintenanceTeam,
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assignments_made",
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assignments_accepted",
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-assigned_at"]
        constraints = [
            # At most one active assignment per issue — prevents conflicting assigns
            models.UniqueConstraint(
                fields=["issue"],
                condition=models.Q(is_active=True),
                name="unique_active_assignment_per_issue",
            ),
        ]
        indexes = [
            models.Index(fields=["team", "is_active"], name="assign_team_active_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.team.name} → issue {self.issue_id} (active={self.is_active})"
