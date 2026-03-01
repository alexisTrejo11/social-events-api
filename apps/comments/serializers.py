"""Comment serializers."""

from rest_framework import serializers
from django.utils import timezone

from apps.comments.models import Comment
from apps.users.serializers import PublicUserProfileSerializer


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for viewing comments."""

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

    def get_likes_count(self, obj):
        """Count total likes."""
        return obj.likes.count()

    def get_is_liked(self, obj):
        """Check if current user has liked this comment."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    def get_replies_count(self, obj):
        """Count direct replies (not deleted)."""
        return obj.replies.filter(is_deleted=False).count()

    def get_content_display(self, obj):
        """Return content or placeholder if deleted."""
        if obj.is_deleted:
            return "[Comment deleted]"
        return obj.content


class CommentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing comments with threading."""

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

    def get_likes_count(self, obj):
        """Count total likes."""
        return obj.likes.count()

    def get_is_liked(self, obj):
        """Check if current user has liked this comment."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    def get_replies(self, obj):
        """Get nested replies (one level deep for now)."""
        # Only include non-deleted replies or show placeholder
        replies = obj.replies.all().order_by("created_at")
        return CommentSerializer(replies, many=True, context=self.context).data

    def get_content_display(self, obj):
        """Return content or placeholder if deleted."""
        if obj.is_deleted:
            return "[Comment deleted]"
        return obj.content


class CommentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating comments."""

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
