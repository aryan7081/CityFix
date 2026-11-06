from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    issue_public_id = serializers.UUIDField(
        source="issue.public_id", read_only=True, allow_null=True
    )

    class Meta:
        model = Notification
        fields = (
            "id",
            "kind",
            "title",
            "message",
            "issue_public_id",
            "is_read",
            "created_at",
        )
