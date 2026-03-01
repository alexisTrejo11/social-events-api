import logging
import re
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import UserFollow, UserPreferences

User = get_user_model()
logger = logging.getLogger(__name__)


def validate_password_strength(password):
    """
    Validate password strength with custom rules:
    - At least 8 characters
    - Contains uppercase and lowercase letters
    - Contains at least one digit
    - Contains at least one special character
    """
    if len(password) < 8:
        raise serializers.ValidationError(
            "Password must be at least 8 characters long."
        )

    if not re.search(r"[A-Z]", password):
        raise serializers.ValidationError(
            "Password must contain at least one uppercase letter."
        )

    if not re.search(r"[a-z]", password):
        raise serializers.ValidationError(
            "Password must contain at least one lowercase letter."
        )

    if not re.search(r"\d", password):
        raise serializers.ValidationError("Password must contain at least one digit.")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise serializers.ValidationError(
            "Password must contain at least one special character."
        )

    return password


# Auth Serializers


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""

    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "first_name",
            "last_name",
            "username",
            "phone_number",
        ]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate_email(self, value):
        """Check if email already exists"""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate_username(self, value):
        """Validate username if provided"""
        if value and User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate(self, data):
        """Validate passwords match and strength"""
        # Validate password strength
        validate_password_strength(data["password"])

        return data

    def create(self, validated_data):
        """Create user account"""
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)

        logger.info(f"New user registered: {user.email}")

        # TODO: Send verification email
        # from apps.users.tasks import send_verification_email
        # send_verification_email.delay(user.id)

        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    tokens = serializers.SerializerMethodField(read_only=True)
    user = serializers.SerializerMethodField(read_only=True)

    def validate(self, data):
        """Authenticate user"""
        email = data.get("email", "").lower()
        password = data.get("password")

        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        data["user"] = user
        return data

    def get_tokens(self, obj):
        """Generate JWT tokens"""
        user = obj.get("user")
        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    def get_user(self, obj):
        """Return user data"""
        user = obj.get("user")
        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email_verified": user.email_verified,
        }


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing password"""

    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)

    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, data):
        """Validate new passwords match and strength"""
        validate_password_strength(data["new_password"])
        return data

    def save(self):
        """Change password"""
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()

        logger.info(f"Password changed for user: {user.email}")

        # TODO: Send password changed notification
        # from apps.notifications.tasks import send_notification
        # send_notification.delay(user.id, 'password_changed')

        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting password reset"""

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Check if user exists"""
        try:
            User.objects.get(email=value.lower())
        except User.DoesNotExist:
            # Don't reveal if user exists or not for security
            pass
        return value.lower()

    def save(self):
        """Send password reset email"""
        email = self.validated_data["email"]

        try:
            user = User.objects.get(email=email)
            logger.info(f"Password reset requested for: {email}")

            # TODO: Generate reset token and send email
            # from apps.users.tasks import send_password_reset_email
            # send_password_reset_email.delay(user.id)

        except User.DoesNotExist:
            logger.warning(f"Password reset requested for non-existent email: {email}")
            pass


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password reset"""

    token = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        """Validate passwords match and strength"""
        validate_password_strength(data["new_password"])

        # TODO: Validate token
        # decoded_token = decode_reset_token(data['token'])
        # if not decoded_token:
        #     raise serializers.ValidationError({"token": "Invalid or expired token."})
        # data['user_id'] = decoded_token['user_id']

        return data


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification"""

    token = serializers.CharField(required=True)

    def validate_token(self, value):
        """Validate verification token"""
        # TODO: Validate token and get user
        # decoded = decode_verification_token(value)
        # if not decoded:
        #     raise serializers.ValidationError("Invalid or expired token.")
        # return decoded
        return value


# User Profile Serializers


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
