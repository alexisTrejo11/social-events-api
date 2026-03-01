import logging
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.models import UserFollow, UserPreferences
from apps.users.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    PublicUserProfileSerializer,
    UserPreferencesSerializer,
    UserFollowSerializer,
    UserFollowerSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


# ============================================================================
# Authentication Views
# ============================================================================


class RegisterView(generics.CreateAPIView):
    """
    POST /auth/register/
    Register a new user account
    """

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Create user and return user data"""
        logger.info(f"Registration attempt for email: {request.data.get('email')}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "message": "User registered successfully. Please check your email to verify your account.",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(generics.GenericAPIView):
    """
    POST /auth/login/
    Login and receive JWT tokens
    """

    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Authenticate and return tokens"""
        logger.info(f"Login attempt for email: {request.data.get('email')}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        logger.info(f"User logged in: {serializer.validated_data['user'].email}")

        return Response(
            {"tokens": serializer.data["tokens"], "user": serializer.data["user"]},
            status=status.HTTP_200_OK,
        )


class LogoutView(generics.GenericAPIView):
    """
    POST /auth/logout/
    Logout and blacklist refresh token
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Blacklist refresh token"""
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            logger.info(f"User logged out: {request.user.email}")

            return Response(
                {"message": "Logged out successfully"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )


class VerifyEmailView(generics.GenericAPIView):
    """
    POST /auth/verify-email/
    Verify email with token
    """

    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Verify email"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: Decode token and verify user
        # user_id = decoded_token['user_id']
        # user = User.objects.get(id=user_id)
        # user.email_verified = True
        # user.save()

        logger.info("Email verification placeholder")

        return Response(
            {"message": "Email verified successfully"}, status=status.HTTP_200_OK
        )


class ResendVerificationView(generics.GenericAPIView):
    """
    POST /auth/resend-verification/
    Resend verification email
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Resend verification email"""
        user = request.user

        if user.email_verified:
            return Response(
                {"message": "Email is already verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"Resending verification email to: {user.email}")

        # TODO: Send verification email
        # from apps.users.tasks import send_verification_email
        # send_verification_email.delay(user.id)

        return Response(
            {"message": "Verification email sent"}, status=status.HTTP_200_OK
        )


class PasswordChangeView(generics.GenericAPIView):
    """
    POST /auth/password/change/
    Change password for authenticated user
    """

    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Change password"""
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Password changed successfully"}, status=status.HTTP_200_OK
        )


class PasswordResetRequestView(generics.GenericAPIView):
    """
    POST /auth/password/reset/
    Request password reset email
    """

    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Send password reset email"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "If an account exists with this email, a password reset link has been sent."
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    POST /auth/password/reset/confirm/
    Confirm password reset with token
    """

    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Reset password"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: Reset password
        # user = User.objects.get(id=serializer.validated_data['user_id'])
        # user.set_password(serializer.validated_data['new_password'])
        # user.save()

        logger.info("Password reset placeholder")

        return Response(
            {"message": "Password reset successfully"}, status=status.HTTP_200_OK
        )


# ============================================================================
# User Profile Views
# ============================================================================


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /users/me/ - Get own profile
    PATCH /users/me/ - Update own profile
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return UserProfileUpdateSerializer
        return UserProfileSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        """Get user profile"""
        logger.info(f"Fetching profile for user: {request.user.email}")
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Update user profile"""
        logger.info(f"Updating profile for user: {request.user.email}")
        return super().update(request, *args, **kwargs)


class DeactivateAccountView(generics.GenericAPIView):
    """
    DELETE /users/me/
    Deactivate user account
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        """Deactivate account (soft delete)"""
        user = request.user
        user.is_active = False
        user.save()

        logger.info(f"Account deactivated: {user.email}")

        # TODO: Send account deactivation notification
        # from apps.notifications.tasks import send_notification
        # send_notification.delay(user.id, 'account_deactivated')

        return Response(
            {"message": "Account deactivated successfully"}, status=status.HTTP_200_OK
        )


class PublicUserProfileView(generics.RetrieveAPIView):
    """
    GET /users/{username}/
    Get public profile of another user
    """

    queryset = User.objects.filter(is_active=True)
    serializer_class = PublicUserProfileSerializer
    lookup_field = "username"
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        """Get public user profile"""
        logger.info(f"Fetching public profile for: {kwargs.get('username')}")
        return super().retrieve(request, *args, **kwargs)


class UserPreferencesView(generics.RetrieveUpdateAPIView):
    """
    GET /users/me/preferences/ - Get preferences
    PUT/PATCH /users/me/preferences/ - Update preferences
    """

    serializer_class = UserPreferencesSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Get or create user preferences"""
        preferences, created = UserPreferences.objects.get_or_create(
            user=self.request.user
        )
        if created:
            logger.info(f"Created preferences for user: {self.request.user.email}")
        return preferences


# ============================================================================
# Social Views
# ============================================================================


class UserFollowersView(generics.ListAPIView):
    """
    GET /users/{username}/followers/
    Get list of user's followers
    """

    serializer_class = UserFollowerSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Get followers for the specified user"""
        username = self.kwargs.get("username")
        user = get_object_or_404(User, username=username, is_active=True)
        logger.info(f"Fetching followers for: {username}")
        return UserFollow.objects.filter(following=user).select_related("follower")


class UserFollowingView(generics.ListAPIView):
    """
    GET /users/{username}/following/
    Get list of users that this user follows
    """

    serializer_class = UserFollowSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Get following for the specified user"""
        username = self.kwargs.get("username")
        user = get_object_or_404(User, username=username, is_active=True)
        logger.info(f"Fetching following for: {username}")
        return UserFollow.objects.filter(follower=user).select_related("following")


class FollowUserView(generics.GenericAPIView):
    """
    POST /users/{username}/follow/
    Follow a user
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, username=None):
        """Follow user"""
        user_to_follow = get_object_or_404(User, username=username, is_active=True)

        if user_to_follow == request.user:
            return Response(
                {"error": "You cannot follow yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        follow, created = UserFollow.objects.get_or_create(
            follower=request.user, following=user_to_follow
        )

        if created:
            logger.info(
                f"{request.user.email} started following {user_to_follow.username}"
            )

            # TODO: Send notification to followed user
            # from apps.notifications.tasks import create_notification
            # create_notification.delay(
            #     user_id=user_to_follow.id,
            #     notification_type='new_follower',
            #     actor_id=request.user.id
            # )

            return Response(
                {"message": f"You are now following {user_to_follow.username}"},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"message": f"You are already following {user_to_follow.username}"},
                status=status.HTTP_200_OK,
            )


class UnfollowUserView(generics.GenericAPIView):
    """
    DELETE /users/{username}/follow/
    Unfollow a user
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, username=None):
        """Unfollow user"""
        user_to_unfollow = get_object_or_404(User, username=username, is_active=True)

        try:
            follow = UserFollow.objects.get(
                follower=request.user, following=user_to_unfollow
            )
            follow.delete()

            logger.info(f"{request.user.email} unfollowed {user_to_unfollow.username}")

            return Response(
                {"message": f"You have unfollowed {user_to_unfollow.username}"},
                status=status.HTTP_200_OK,
            )
        except UserFollow.DoesNotExist:
            return Response(
                {"error": f"You are not following {user_to_unfollow.username}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserFeedView(generics.GenericAPIView):
    """
    GET /users/me/feed/
    Get events from followed users and organizations
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get personalized feed"""
        user = request.user

        # Get users that current user follows
        following_users = user.following.values_list("id", flat=True)

        # Get organizations that current user follows
        # (members of organizations they belong to)
        user_orgs = user.organizations.values_list("id", flat=True)

        logger.info(f"Fetching feed for user: {user.email}")

        # Get events from followed users and organizations
        from apps.events.models import Event

        feed_events = (
            Event.objects.filter(
                Q(organizer_id__in=following_users) | Q(organization_id__in=user_orgs),
                status="published",
                is_deleted=False,
            )
            .select_related("organizer", "organization", "location", "category")
            .order_by("-created_at")[:50]
        )

        # Return simplified event data
        events_data = [
            {
                "id": str(event.id),
                "title": event.title,
                "slug": event.slug,
                "description": (
                    event.description[:200] + "..."
                    if len(event.description) > 200
                    else event.description
                ),
                "event_type": event.event_type,
                "start_date": event.start_date,
                "end_date": event.end_date,
                "organizer": event.organizer.get_full_name(),
                "organization": event.organization.name if event.organization else None,
                "location": event.location.name if event.location else None,
                "category": event.category.name if event.category else None,
            }
            for event in feed_events
        ]

        return Response(
            {"count": len(events_data), "events": events_data},
            status=status.HTTP_200_OK,
        )
