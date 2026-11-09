from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from issues.models import Issue
from issues.priority import compute_priority_score, refresh_priority, score_to_priority

User = get_user_model()


class PriorityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="p1", password="x", role="CITIZEN")

    def test_severe_water_leak_scores_high(self):
        issue = Issue.objects.create(
            title="Severe leak",
            description="Major pipe burst",
            category=Issue.Category.WATER_LEAK,
            severity=Issue.Severity.SEVERE,
            latitude="12.97",
            longitude="77.59",
            reporter=self.user,
            support_count=8,
        )
        Issue.objects.filter(pk=issue.pk).update(created_at=timezone.now() - timedelta(days=10))
        issue.refresh_from_db()
        score = compute_priority_score(issue)
        self.assertGreaterEqual(score, 0.55)
        self.assertIn(score_to_priority(score), ["HIGH", "CRITICAL"])

    def test_refresh_persists(self):
        issue = Issue.objects.create(
            title="Minor light",
            description="Dim light",
            category=Issue.Category.STREETLIGHT,
            severity=Issue.Severity.MINOR,
            latitude="12.97",
            longitude="77.59",
            reporter=self.user,
        )
        refresh_priority(issue)
        issue.refresh_from_db()
        self.assertGreater(issue.priority_score, 0)
        self.assertIn(issue.priority, Issue.Priority.values)
