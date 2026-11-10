from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from issues.models import Issue, IssueStatusHistory
from issues.priority import refresh_priority
from teams.models import MaintenanceTeam

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo users, teams, and sample issues for CityFix evaluation."

    @transaction.atomic
    def handle(self, *args, **options):
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@cityfix.local",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "first_name": "Ada",
                "last_name": "Admin",
            },
        )
        if not admin.has_usable_password():
            admin.set_password("admin123")
            admin.save()
        else:
            # Ensure password for demos
            admin.set_password("admin123")
            admin.role = User.Role.ADMIN
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()

        citizen1, _ = User.objects.get_or_create(
            username="citizen1",
            defaults={
                "email": "citizen1@cityfix.local",
                "role": User.Role.CITIZEN,
                "first_name": "Priya",
                "last_name": "Shah",
            },
        )
        citizen1.set_password("citizen123")
        citizen1.role = User.Role.CITIZEN
        citizen1.save()

        citizen2, _ = User.objects.get_or_create(
            username="citizen2",
            defaults={
                "email": "citizen2@cityfix.local",
                "role": User.Role.CITIZEN,
                "first_name": "Ravi",
                "last_name": "Kumar",
            },
        )
        citizen2.set_password("citizen123")
        citizen2.role = User.Role.CITIZEN
        citizen2.save()

        staff1, _ = User.objects.get_or_create(
            username="staff1",
            defaults={
                "email": "staff1@cityfix.local",
                "role": User.Role.MAINTENANCE,
                "first_name": "Maya",
                "last_name": "Crew",
            },
        )
        staff1.set_password("staff123")
        staff1.role = User.Role.MAINTENANCE
        staff1.save()

        staff2, _ = User.objects.get_or_create(
            username="staff2",
            defaults={
                "email": "staff2@cityfix.local",
                "role": User.Role.MAINTENANCE,
                "first_name": "Leo",
                "last_name": "Crew",
            },
        )
        staff2.set_password("staff123")
        staff2.role = User.Role.MAINTENANCE
        staff2.save()

        road_team, _ = MaintenanceTeam.objects.get_or_create(
            name="Road Repair Unit",
            defaults={
                "description": "Handles potholes and road surface damage",
                "specialization": "POTHOLE",
            },
        )
        road_team.members.set([staff1])

        lights_team, _ = MaintenanceTeam.objects.get_or_create(
            name="Streetlight Crew",
            defaults={
                "description": "Electrical and lighting repairs",
                "specialization": "STREETLIGHT",
            },
        )
        lights_team.members.set([staff2])

        sanitation, _ = MaintenanceTeam.objects.get_or_create(
            name="Sanitation Squad",
            defaults={
                "description": "Garbage and waste accumulation",
                "specialization": "GARBAGE",
            },
        )
        sanitation.members.set([staff1, staff2])

        samples = [
            {
                "title": "Large pothole on MG Road",
                "description": "Deep pothole near the bus stop on MG Road causing traffic slowdown and vehicle damage risk.",
                "category": Issue.Category.POTHOLE,
                "severity": Issue.Severity.MAJOR,
                "latitude": "12.971600",
                "longitude": "77.594600",
                "address": "MG Road, Bengaluru",
                "reporter": citizen1,
                "status": Issue.Status.VERIFIED,
            },
            {
                "title": "Broken streetlight near park",
                "description": "Streetlight pole #42 has been dark for a week near the children's park entrance.",
                "category": Issue.Category.STREETLIGHT,
                "severity": Issue.Severity.MODERATE,
                "latitude": "12.975000",
                "longitude": "77.599000",
                "address": "Cubbon Park East Gate",
                "reporter": citizen2,
                "status": Issue.Status.REPORTED,
            },
            {
                "title": "Garbage pile behind market",
                "description": "Uncollected garbage bags piled up behind the vegetable market creating foul smell.",
                "category": Issue.Category.GARBAGE,
                "severity": Issue.Severity.MAJOR,
                "latitude": "12.968000",
                "longitude": "77.590000",
                "address": "KR Market rear lane",
                "reporter": citizen1,
                "status": Issue.Status.UNDER_REVIEW,
            },
        ]

        for sample in samples:
            exists = Issue.objects.filter(title=sample["title"], reporter=sample["reporter"]).exists()
            if exists:
                continue
            status = sample.pop("status")
            reporter = sample.pop("reporter")
            issue = Issue.objects.create(reporter=reporter, status=status, **sample)
            refresh_priority(issue)
            IssueStatusHistory.objects.create(
                issue=issue,
                previous_status="",
                new_status=Issue.Status.REPORTED,
                actor=reporter,
                comment="Seeded issue",
            )
            if status != Issue.Status.REPORTED:
                IssueStatusHistory.objects.create(
                    issue=issue,
                    previous_status=Issue.Status.REPORTED,
                    new_status=status,
                    actor=admin,
                    comment="Seeded status progression",
                )

        self.stdout.write(self.style.SUCCESS("Seed data ready."))
        self.stdout.write("  admin / admin123")
        self.stdout.write("  citizen1 / citizen123")
        self.stdout.write("  citizen2 / citizen123")
        self.stdout.write("  staff1 / staff123")
        self.stdout.write("  staff2 / staff123")
