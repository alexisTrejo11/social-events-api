"""Comment serializers."""

from rest_framework import serializers
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field

from apps.comments.models import Comment
from apps.users.serializers import PublicUserProfileSerializer


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for viewing individual comments with author details and engagement metrics."""

    author = PublicUserProfileSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    content_display = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "content",
            "content_display",
            "parent",
            "is_pinned",
            "is_deleted",
            "likes_count",
            "is_liked",
            "replies_count",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(serializers.IntegerField())
    def get_likes_count(self, obj):
        """Count total likes on this comment."""
        return obj.likes.count()

    @extend_schema_field(serializers.BooleanField())
    def get_is_liked(self, obj):
        """Check if the current authenticated user has liked this comment."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    @extend_schema_field(serializers.IntegerField())
    def get_replies_count(self, obj):
        """Count direct replies to this comment (excluding deleted replies)."""
        return obj.replies.filter(is_deleted=False).count()

    @extend_schema_field(serializers.CharField())
    def get_content_display(self, obj):
        """Return comment content or placeholder text if the comment has been deleted."""
        if obj.is_deleted:
            return "[Comment deleted]"
        return obj.content


class CommentListSerializer(serializers.ModelSerializer):
    """Serializer for listing comments with nested replies (one level deep)."""

    author = PublicUserProfileSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    content_display = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "content",
            "content_display",
            "parent",
            "is_pinned",
            "is_deleted",
            "likes_count",
            "is_liked",
            "replies",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(serializers.IntegerField())
    def get_likes_count(self, obj):
        """Count total likes on this comment."""
        return obj.likes.count()

    @extend_schema_field(serializers.BooleanField())
    def get_is_liked(self, obj):
        """Check if the current authenticated user has liked this comment."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    @extend_schema_field(CommentSerializer(many=True))
    def get_replies(self, obj):
        """Get nested replies to this comment (one level deep)."""
        # Only include non-deleted replies or show placeholder
        replies = obj.replies.all().order_by("created_at")
        return CommentSerializer(replies, many=True, context=self.context).data

    @extend_schema_field(serializers.CharField())
    def get_content_display(self, obj):
        """Return comment content or placeholder text if the comment has been deleted."""
        if obj.is_deleted:
            return "[Comment deleted]"
        return obj.content


class CommentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating comments with validation for threading and content."""

    parent_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Comment
        fields = ["content", "parent_id"]

    def validate_content(self, value):
        """Validate comment content."""
        if not value or not value.strip():
            raise serializers.ValidationError("Comment content cannot be empty.")

        if len(value) > 2000:
            raise serializers.ValidationError(
                "Comment content cannot exceed 2000 characters."
            )

        return value.strip()

    def validate_parent_id(self, value):
        """Validate parent comment exists and belongs to same event."""
        if value is None:
            return value

        event = self.context.get("event")
        try:
            parent = Comment.objects.get(id=value, event=event)
        except Comment.DoesNotExist:
            raise serializers.ValidationError(
                "Parent comment not found or does not belong to this event."
            )

        # Don't allow replying to deleted comments
        if parent.is_deleted:
            raise serializers.ValidationError("Cannot reply to a deleted comment.")

        # Don't allow replying to a reply (only one level deep)
        if parent.parent is not None:
            raise serializers.ValidationError(
                "Cannot reply to a reply. Please reply to the parent comment instead."
            )

        return value

    def create(self, validated_data):
        """Create comment."""
        parent_id = validated_data.pop("parent_id", None)
        event = self.context.get("event")
        user = self.context.get("request").user

        parent = None
        if parent_id:
            parent = Comment.objects.get(id=parent_id, event=event)

        comment = Comment.objects.create(
            event=event, author=user, parent=parent, **validated_data
        )

        return comment

    def update(self, instance, validated_data):
        """Update comment content only."""
        # Remove parent_id from validated_data if present (can't change parent)
        validated_data.pop("parent_id", None)

        instance.content = validated_data.get("content", instance.content)
        instance.save(update_fields=["content", "updated_at"])

        return instance
