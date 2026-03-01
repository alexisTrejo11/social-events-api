"""Category and Tag serializers."""

from rest_framework import serializers
from apps.events.models import Category, Tag


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for event categories."""

    event_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "icon",
            "event_count",
            "created_at",
        ]
        read_only_fields = ["slug", "created_at"]

    def get_event_count(self, obj):
        """Count published events in this category."""
        return obj.events.filter(status="published", is_deleted=False).count()


class TagSerializer(serializers.ModelSerializer):
    """Serializer for event tags."""

    event_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "event_count"]
        read_only_fields = ["slug"]

    def get_event_count(self, obj):
        """Count published events with this tag."""
        return obj.events.filter(status="published", is_deleted=False).count()
