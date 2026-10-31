import uuid

from django.conf import settings
from django.db import models


class Issue(models.Model):
    class Category(models.TextChoices):
        POTHOLE = "POTHOLE", "Pothole / Road Damage"
        STREETLIGHT = "STREETLIGHT", "Broken Streetlight"
        GARBAGE = "GARBAGE", "Garbage Accumulation"
        WATER_LEAK = "WATER_LEAK", "Water Leakage"
        OTHER = "OTHER", "Other Infrastructure"

    class Status(models.TextChoices):
        REPORTED = "REPORTED", "Reported"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        VERIFIED = "VERIFIED", "Verified"
        ASSIGNED = "ASSIGNED", "Assigned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"
        REJECTED = "REJECTED", "Rejected"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class Severity(models.TextChoices):
        MINOR = "MINOR", "Minor"
        MODERATE = "MODERATE", "Moderate"
        MAJOR = "MAJOR", "Major"
        SEVERE = "SEVERE", "Severe"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, db_index=True)
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MODERATE,
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REPORTED,
        db_index=True,
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True,
    )
    priority_score = models.FloatField(default=0.0)
    support_count = models.PositiveIntegerField(default=0)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reported_issues",
    )
    assigned_team = models.ForeignKey(
        "teams.MaintenanceTeam",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issues",
    )
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            # Admin filters: status + priority together
            models.Index(fields=["status", "priority"], name="issue_status_priority_idx"),
            # Category dashboards and duplicate candidate narrowing
            models.Index(fields=["category", "status"], name="issue_category_status_idx"),
            # Citizen "my issues" lists
            models.Index(fields=["reporter", "created_at"], name="issue_reporter_created_idx"),
            # Proximity bounding-box prefilter for duplicates
            models.Index(fields=["latitude", "longitude"], name="issue_lat_lng_idx"),
            # Assigned workload queries for maintenance staff
            models.Index(fields=["assigned_team", "status"], name="issue_team_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.public_id} – {self.title}"


class IssueImage(models.Model):
    class Kind(models.TextChoices):
        EVIDENCE = "EVIDENCE", "Report Evidence"
        COMPLETION = "COMPLETION", "Completion Evidence"

    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="issues/%Y/%m/")
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.EVIDENCE)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_images",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.kind} for {self.issue.public_id}"


class IssueStatusHistory(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="status_history")
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="status_changes",
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["issue", "created_at"], name="status_hist_issue_time_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.issue.public_id}: {self.previous_status} → {self.new_status}"


class IssueSupport(models.Model):
    """Citizen support for an existing issue (anti-duplicate path)."""

    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="supports")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="issue_supports",
    )
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["issue", "user"], name="unique_issue_support"),
        ]
        indexes = [
            models.Index(fields=["issue", "created_at"], name="support_issue_time_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} supports {self.issue.public_id}"


class IssueDuplicate(models.Model):
    class Relation(models.TextChoices):
        CANDIDATE = "CANDIDATE", "Candidate"
        CONFIRMED = "CONFIRMED", "Confirmed"
        REJECTED = "REJECTED", "Rejected as duplicate"

    source_issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name="duplicate_of",
        null=True,
        blank=True,
        help_text="New report that may be a duplicate; null when only a suggestion was stored.",
    )
    target_issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name="duplicates",
    )
    score = models.FloatField()
    distance_meters = models.FloatField(null=True, blank=True)
    text_similarity = models.FloatField(null=True, blank=True)
    relation = models.CharField(
        max_length=20,
        choices=Relation.choices,
        default=Relation.CANDIDATE,
    )
    detected_at = models.DateTimeField(auto_now_add=True)
    # Store draft payload fingerprint for suggestions before an issue exists
    draft_fingerprint = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["target_issue", "relation"], name="dup_target_relation_idx"),
        ]

    def __str__(self) -> str:
        return f"dup score={self.score:.2f} → {self.target_issue.public_id}"
