from django.contrib.auth import get_user_model
from django.test import TestCase
from issues.lifecycle import InvalidTransition, apply_transition, can_transition
from issues.models import Issue
from issues.services import assign_team
from teams.models import MaintenanceTeam, TeamAssignment

User = get_user_model()


class LifecycleTests(TestCase):
    def setUp(self):
        self.citizen = User.objects.create_user(username="cit", password="x", role="CITIZEN")
        self.admin = User.objects.create_user(username="adm", password="x", role="ADMIN")
        self.issue = Issue.objects.create(
            title="Leak",
            description="Water leak on street",
            category=Issue.Category.WATER_LEAK,
            latitude="12.97",
            longitude="77.59",
            reporter=self.citizen,
        )

    def test_allowed_path(self):
        self.assertTrue(can_transition("REPORTED", "UNDER_REVIEW"))
        self.assertFalse(can_transition("REPORTED", "RESOLVED"))

    def test_apply_transition_records_history(self):
        apply_transition(self.issue, "UNDER_REVIEW", self.admin, "looking")
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.status, "UNDER_REVIEW")
        self.assertEqual(self.issue.status_history.count(), 1)

    def test_invalid_transition_raises(self):
        with self.assertRaises(InvalidTransition):
            apply_transition(self.issue, "RESOLVED", self.admin)


class AssignmentConcurrencyTests(TestCase):
    def setUp(self):
        self.citizen = User.objects.create_user(username="cit2", password="x", role="CITIZEN")
        self.admin = User.objects.create_user(username="adm2", password="x", role="ADMIN")
        self.team_a = MaintenanceTeam.objects.create(name="Team A")
        self.team_b = MaintenanceTeam.objects.create(name="Team B")
        self.issue = Issue.objects.create(
            title="Pothole",
            description="Road damage",
            category=Issue.Category.POTHOLE,
            latitude="12.97",
            longitude="77.59",
            reporter=self.citizen,
            status=Issue.Status.VERIFIED,
        )

    def test_assign_creates_active_assignment(self):
        assignment = assign_team(issue=self.issue, team=self.team_a, actor=self.admin)
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.status, Issue.Status.ASSIGNED)
        self.assertTrue(assignment.is_active)
        self.assertEqual(TeamAssignment.objects.filter(issue=self.issue, is_active=True).count(), 1)

    def test_reassign_keeps_single_active(self):
        assign_team(issue=self.issue, team=self.team_a, actor=self.admin)
        assign_team(issue=self.issue, team=self.team_b, actor=self.admin)
        self.assertEqual(TeamAssignment.objects.filter(issue=self.issue, is_active=True).count(), 1)
        self.assertEqual(
            TeamAssignment.objects.get(issue=self.issue, is_active=True).team_id,
            self.team_b.id,
        )
