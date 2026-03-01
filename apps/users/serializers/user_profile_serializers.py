import logging
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.models import UserFollow, UserPreferences

User = get_user_model()
logger = logging.getLogger(__name__)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile (own profile)"""

    full_name = serializers.SerializerMethodField()
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "bio",
            "avatar",
            "date_of_birth",
            "phone_number",
            "email_verified",
            "follower_count",
            "following_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "email", "email_verified", "created_at", "updated_at"]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_follower_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "bio",
            "avatar",
            "date_of_birth",
            "phone_number",
        ]

    def validate_username(self, value):
        """Validate username uniqueness"""
        if (
            value
            and User.objects.filter(username=value)
            .exclude(id=self.instance.id)
            .exists()
        ):
            raise serializers.ValidationError("This username is already taken.")
        return value


class PublicUserProfileSerializer(serializers.ModelSerializer):
    """Serializer for public user profile"""

    full_name = serializers.SerializerMethodField()
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "bio",
            "avatar",
            "follower_count",
            "following_count",
            "is_following",
            "created_at",
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_follower_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def get_is_following(self, obj):
        """Check if current user follows this user"""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return UserFollow.objects.filter(
                follower=request.user, following=obj
            ).exists()
        return False


class UserPreferencesSerializer(serializers.ModelSerializer):
    """Serializer for user preferences"""

    class Meta:
        model = UserPreferences
        fields = [
            "notification_frequency",
            "email_notifications",
            "push_notifications",
            "private_profile",
            "language",
            "timezone",
        ]


class UserFollowSerializer(serializers.ModelSerializer):
    """Serializer for user follow relationship"""

    user = PublicUserProfileSerializer(source="following", read_only=True)

    class Meta:
        model = UserFollow
        fields = ["id", "user", "created_at"]
        read_only_fields = fields


class UserFollowerSerializer(serializers.ModelSerializer):
    """Serializer for user followers"""

    user = PublicUserProfileSerializer(source="follower", read_only=True)

    class Meta:
        model = UserFollow
        fields = ["id", "user", "created_at"]
        read_only_fields = fields
