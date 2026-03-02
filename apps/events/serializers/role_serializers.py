"""Event role serializers for managing hosts, speakers, volunteers, etc."""

from rest_framework import serializers
from apps.events.models import EventRole
from apps.users.serializers import PublicUserProfileSerializer


class EventRoleSerializer(serializers.ModelSerializer):
    """Serializer for viewing event roles."""

    user = PublicUserProfileSerializer(read_only=True)
    assigned_by_user = PublicUserProfileSerializer(source="assigned_by", read_only=True)

    class Meta:
        model = EventRole
        fields = [
            "id",
            "user",
            "role",
            "bio_override",
            "assigned_at",
            "assigned_by_user",
        ]


class EventRoleCreateSerializer(serializers.ModelSerializer):
    """Serializer for assigning event roles."""

    user_id = serializers.UUIDField()

    class Meta:
        model = EventRole
        fields = ["user_id", "role", "bio_override"]

    def validate_user_id(self, value):
        """Validate that user exists."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User not found.")
        return value

    def validate(self, attrs):
        """Validate role assignment."""
        from django.contrib.auth import get_user_model

        event = self.context.get("event")
        user_id = attrs.get("user_id")
        role = attrs.get("role")

        User = get_user_model()
        user = User.objects.get(id=user_id)

        # Check if user already has this role
        if EventRole.objects.filter(event=event, user=user, role=role).exists():
            raise serializers.ValidationError(
                f"User already has the {role} role for this event."
            )

        return attrs

    def create(self, validated_data):
        """Create event role assignment."""
        from django.contrib.auth import get_user_model

        user_id = validated_data.pop("user_id")
        User = get_user_model()
        user = User.objects.get(id=user_id)

        event = self.context.get("event")
        assigned_by = self.context.get("request").user

        return EventRole.objects.create(
            event=event, user=user, assigned_by=assigned_by, **validated_data
        )


class EventRoleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating event role bio."""

    class Meta:
        model = EventRole
        fields = ["bio_override"]
