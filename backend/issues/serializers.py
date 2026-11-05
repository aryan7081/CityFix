from django.conf import settings
from rest_framework import serializers

from accounts.serializers import UserSerializer
from teams.serializers import MaintenanceTeamSerializer

from .models import Issue, IssueDuplicate, IssueImage, IssueStatusHistory, IssueSupport


class IssueImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueImage
        fields = ("id", "image", "kind", "created_at")


class IssueStatusHistorySerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)

    class Meta:
        model = IssueStatusHistory
        fields = (
            "id",
            "previous_status",
            "new_status",
            "actor",
            "comment",
            "created_at",
        )


class IssueListSerializer(serializers.ModelSerializer):
    reporter_name = serializers.CharField(source="reporter.username", read_only=True)
    assigned_team_name = serializers.CharField(
        source="assigned_team.name", read_only=True, default=None
    )

    class Meta:
        model = Issue
        fields = (
            "public_id",
            "title",
            "category",
            "severity",
            "status",
            "priority",
            "priority_score",
            "support_count",
            "latitude",
            "longitude",
            "address",
            "reporter_name",
            "assigned_team_name",
            "created_at",
            "updated_at",
            "resolved_at",
        )


class IssueDetailSerializer(serializers.ModelSerializer):
    reporter = UserSerializer(read_only=True)
    assigned_team = MaintenanceTeamSerializer(read_only=True)
    images = IssueImageSerializer(many=True, read_only=True)
    status_history = IssueStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Issue
        fields = (
            "public_id",
            "title",
            "description",
            "category",
            "severity",
            "status",
            "priority",
            "priority_score",
            "support_count",
            "latitude",
            "longitude",
            "address",
            "reporter",
            "assigned_team",
            "resolution_notes",
            "images",
            "status_history",
            "created_at",
            "updated_at",
            "resolved_at",
        )


class IssueCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    category = serializers.ChoiceField(choices=Issue.Category.choices)
    severity = serializers.ChoiceField(
        choices=Issue.Severity.choices, default=Issue.Severity.MODERATE
    )
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    address = serializers.CharField(max_length=500, required=False, allow_blank=True)
    image = serializers.ImageField(required=False)
    force = serializers.BooleanField(default=False, required=False)

    def validate_image(self, image):
        if image is None:
            return image
        if image.size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise serializers.ValidationError("Image must be 5 MB or smaller.")
        content_type = getattr(image, "content_type", None)
        if content_type and content_type not in settings.ALLOWED_IMAGE_CONTENT_TYPES:
            raise serializers.ValidationError("Only JPEG, PNG, or WebP images are allowed.")
        return image


class DuplicateCheckSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    category = serializers.ChoiceField(choices=Issue.Category.choices)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)


class SupportSerializer(serializers.Serializer):
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)


class TransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Issue.Status.choices)
    comment = serializers.CharField(required=False, allow_blank=True)


class AssignSerializer(serializers.Serializer):
    team_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)


class PrioritySerializer(serializers.Serializer):
    priority = serializers.ChoiceField(choices=Issue.Priority.choices)


class ResolveSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)
    image = serializers.ImageField(required=False)


class IssueDuplicateSerializer(serializers.ModelSerializer):
    target_public_id = serializers.UUIDField(source="target_issue.public_id", read_only=True)
    target_title = serializers.CharField(source="target_issue.title", read_only=True)

    class Meta:
        model = IssueDuplicate
        fields = (
            "id",
            "target_public_id",
            "target_title",
            "score",
            "distance_meters",
            "text_similarity",
            "relation",
            "detected_at",
        )


class IssueSupportSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = IssueSupport
        fields = ("id", "user", "note", "created_at")
