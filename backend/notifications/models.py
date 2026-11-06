from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Kind(models.TextChoices):
        ISSUE_REPORTED = "ISSUE_REPORTED", "Issue Reported"
        ISSUE_VERIFIED = "ISSUE_VERIFIED", "Issue Verified"
        ISSUE_REJECTED = "ISSUE_REJECTED", "Issue Rejected"
        TEAM_ASSIGNED = "TEAM_ASSIGNED", "Team Assigned"
        STATUS_UPDATED = "STATUS_UPDATED", "Status Updated"
        ISSUE_RESOLVED = "ISSUE_RESOLVED", "Issue Resolved"
        DUPLICATE_SUGGESTED = "DUPLICATE_SUGGESTED", "Duplicate Suggested"
        SUPPORT_ADDED = "SUPPORT_ADDED", "Support Added"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(max_length=40, choices=Kind.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    issue = models.ForeignKey(
        "issues.Issue",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["recipient", "is_read", "created_at"],
                name="notif_recipient_read_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.kind} → {self.recipient_id}"
