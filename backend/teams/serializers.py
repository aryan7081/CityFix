from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import MaintenanceTeam, TeamAssignment

User = get_user_model()


class MaintenanceTeamSerializer(serializers.ModelSerializer):
    member_ids = serializers.PrimaryKeyRelatedField(
        source="members",
        many=True,
        queryset=User.objects.filter(role=User.Role.MAINTENANCE),
        required=False,
    )
    member_count = serializers.IntegerField(source="members.count", read_only=True)

    class Meta:
        model = MaintenanceTeam
        fields = (
            "id",
            "name",
            "description",
            "specialization",
            "is_active",
            "member_ids",
            "member_count",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class TeamAssignmentSerializer(serializers.ModelSerializer):
    team = MaintenanceTeamSerializer(read_only=True)
    issue_public_id = serializers.UUIDField(source="issue.public_id", read_only=True)
    issue_title = serializers.CharField(source="issue.title", read_only=True)

    class Meta:
        model = TeamAssignment
        fields = (
            "id",
            "issue_public_id",
            "issue_title",
            "team",
            "is_active",
            "notes",
            "assigned_at",
            "accepted_at",
            "completed_at",
        )
