import logging
from django.contrib.auth import get_user_model
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view
from apps.users.models import UserPreferences
from apps.users.serializers import (
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    PublicUserProfileSerializer,
    UserPreferencesSerializer,
)
from common.serializers import (
    ErrorResponseSerializer,
    MessageResponseSerializer,
    ValidationErrorSerializer,
)
from common.throttling import ReadHeavyThrottle, WriteSensitiveThrottle

User = get_user_model()
logger = logging.getLogger(__name__)


@extend_schema_view(
    get=extend_schema(
        tags=["Users"],
        summary="Get own profile",
        description="Retrieve the authenticated user's profile with full details including email and private information.",
        responses={
            200: UserProfileSerializer,
            401: ErrorResponseSerializer,
        },
    ),
    put=extend_schema(
        tags=["Users"],
        summary="Update own profile (full)",
        description="Fully update the authenticated user's profile.",
        request=UserProfileUpdateSerializer,
        responses={
            200: UserProfileSerializer,
            400: ValidationErrorSerializer,
            401: ErrorResponseSerializer,
        },
    ),
    patch=extend_schema(
        tags=["Users"],
        summary="Update own profile (partial)",
        description="Partially update the authenticated user's profile with provided fields.",
        request=UserProfileUpdateSerializer,
        responses={
            200: UserProfileSerializer,
            400: ValidationErrorSerializer,
            401: ErrorResponseSerializer,
        },
    ),
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /users/me/ - Get own profile
    PATCH /users/me/ - Update own profile
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [ReadHeavyThrottle, WriteSensitiveThrottle]

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


@extend_schema(
    tags=["Users"],
    summary="Deactivate account",
    description="Soft delete the user account by marking it as inactive. This action cannot be undone via API.",
    responses={
        200: MessageResponseSerializer,
        401: ErrorResponseSerializer,
    },
)
class DeactivateAccountView(generics.GenericAPIView):
    """
    DELETE /users/me/
    Deactivate user account
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [WriteSensitiveThrottle]

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
            MessageResponseSerializer(
                {"message": "Account deactivated successfully"}
            ).data,
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Users"],
    summary="Get public user profile",
    description="Retrieve the public profile of any user by username. Only shows publicly visible information.",
    responses={
        200: PublicUserProfileSerializer,
        404: ErrorResponseSerializer,
    },
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
    throttle_classes = [ReadHeavyThrottle]

    def retrieve(self, request, *args, **kwargs):
        """Get public user profile"""
        logger.info(f"Fetching public profile for: {kwargs.get('username')}")
        return super().retrieve(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        tags=["Users"],
        summary="Get user preferences",
        description="Retrieve notification and privacy preferences for the authenticated user.",
        responses={
            200: UserPreferencesSerializer,
            401: ErrorResponseSerializer,
        },
    ),
    put=extend_schema(
        tags=["Users"],
        summary="Update user preferences (full)",
        description="Fully update notification and privacy preferences.",
        request=UserPreferencesSerializer,
        responses={
            200: UserPreferencesSerializer,
            400: ValidationErrorSerializer,
            401: ErrorResponseSerializer,
        },
    ),
    patch=extend_schema(
        tags=["Users"],
        summary="Update user preferences (partial)",
        description="Partially update notification and privacy preferences with provided fields.",
        request=UserPreferencesSerializer,
        responses={
            200: UserPreferencesSerializer,
            400: ValidationErrorSerializer,
            401: ErrorResponseSerializer,
        },
    ),
)
class UserPreferencesView(generics.RetrieveUpdateAPIView):
    """
    GET /users/me/preferences/ - Get preferences
    PUT/PATCH /users/me/preferences/ - Update preferences
    """

    serializer_class = UserPreferencesSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ReadHeavyThrottle, WriteSensitiveThrottle]

    def get_object(self):
        """Get or create user preferences"""
        preferences, created = UserPreferences.objects.get_or_create(
            user=self.request.user
        )
        if created:
            logger.info(f"Created preferences for user: {self.request.user.email}")
        return preferences
