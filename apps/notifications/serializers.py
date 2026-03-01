"""Notification serializers."""

from rest_framework import serializers
from apps.notifications.models import Notification
from apps.users.serializers import PublicUserProfileSerializer


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for viewing notifications."""

    actor = PublicUserProfileSerializer(read_only=True)
    event_title = serializers.CharField(source="event.title", read_only=True)
    event_slug = serializers.CharField(source="event.slug", read_only=True)
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    organization_slug = serializers.CharField(
        source="organization.slug", read_only=True
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "body",
            "is_read",
            "read_at",
            "actor",
            "event_title",
            "event_slug",
            "organization_name",
            "organization_slug",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "read_at"]


class NotificationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for notification list."""

    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "body",
            "is_read",
            "actor_name",
            "created_at",
        ]

    def get_actor_name(self, obj):
        """Get actor's full name if available."""
        if obj.actor:
            return obj.actor.get_full_name()
        return None


class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read."""

    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of notification IDs to mark as read. If not provided, marks all as read.",
    )
