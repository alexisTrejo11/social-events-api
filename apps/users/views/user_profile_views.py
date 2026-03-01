import logging
from django.contrib.auth import get_user_model
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.users.models import UserPreferences
from apps.users.serializers import (
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    PublicUserProfileSerializer,
    UserPreferencesSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


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
