"""
OAuth/Social Authentication Views
"""

import logging
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from allauth.socialaccount.models import SocialAccount, SocialApp
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

from apps.users.serializers import (
    GoogleLoginSerializer,
    GitHubLoginSerializer,
    SocialAccountSerializer,
    OAuthLoginResponseSerializer,
    ConnectSocialAccountSerializer,
    DisconnectSocialAccountSerializer,
)
from common.serializers import ErrorResponseSerializer, MessageResponseSerializer
from common.throttling import AuthActionsThrottle

User = get_user_model()
logger = logging.getLogger(__name__)


def get_tokens_for_user(user):
    """
    Generate JWT tokens for a user
    """
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


@extend_schema(
    tags=["OAuth"],
    summary="Login with Google",
    description="""
    Authenticate user with Google OAuth2.
    
    **How to use:**
    1. Redirect user to Google OAuth URL
    2. After user authorizes, Google redirects back with an access_token
    3. Send that access_token to this endpoint
    4. Receive JWT tokens for API authentication
    
    **Frontend implementation:**
    - Use Google Sign-In SDK or redirect to Google OAuth URL
    - Exchange the authorization code for an access_token
    - Send access_token to this endpoint
    """,
    request=GoogleLoginSerializer,
    responses={
        200: OAuthLoginResponseSerializer,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
    },
)
class GoogleLoginView(SocialLoginView):
    """
    POST /auth/oauth/google/
    Login or register with Google OAuth
    """

    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.FRONTEND_URL
    client_class = OAuth2Client
    serializer_class = GoogleLoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AuthActionsThrottle]

    def post(self, request, *args, **kwargs):
        """
        Process Google OAuth login
        """
        try:
            response = super().post(request, *args, **kwargs)

            # If successful, the response contains user data
            if response.status_code == 200:
                user = self.request.user
                tokens = get_tokens_for_user(user)

                return Response(
                    {
                        "access": tokens["access"],
                        "refresh": tokens["refresh"],
                        "user": {
                            "id": user.id,
                            "email": user.email,
                            "username": user.username,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                        },
                    },
                    status=status.HTTP_200_OK,
                )

            return response

        except Exception as e:
            logger.error(f"Google OAuth error: {e}")
            return Response(
                {"error": "Failed to authenticate with Google"},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(
    tags=["OAuth"],
    summary="Login with GitHub",
    description="""
    Authenticate user with GitHub OAuth2.
    
    **How to use:**
    1. Redirect user to GitHub OAuth URL
    2. After user authorizes, GitHub redirects back with an access_token
    3. Send that access_token to this endpoint
    4. Receive JWT tokens for API authentication
    
    **Frontend implementation:**
    - Use GitHub OAuth App
    - Exchange the authorization code for an access_token
    - Send access_token to this endpoint
    """,
    request=GitHubLoginSerializer,
    responses={
        200: OAuthLoginResponseSerializer,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
    },
)
class GitHubLoginView(SocialLoginView):
    """
    POST /auth/oauth/github/
    Login or register with GitHub OAuth
    """

    adapter_class = GitHubOAuth2Adapter
    callback_url = settings.FRONTEND_URL
    client_class = OAuth2Client
    serializer_class = GitHubLoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AuthActionsThrottle]

    def post(self, request, *args, **kwargs):
        """
        Process GitHub OAuth login
        """
        try:
            response = super().post(request, *args, **kwargs)

            # If successful, the response contains user data
            if response.status_code == 200:
                user = self.request.user
                tokens = get_tokens_for_user(user)

                return Response(
                    {
                        "access": tokens["access"],
                        "refresh": tokens["refresh"],
                        "user": {
                            "id": user.id,
                            "email": user.email,
                            "username": user.username,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                        },
                    },
                    status=status.HTTP_200_OK,
                )

            return response

        except Exception as e:
            logger.error(f"GitHub OAuth error: {e}")
            return Response(
                {"error": "Failed to authenticate with GitHub"},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(
    tags=["OAuth"],
    summary="List connected social accounts",
    description="Get list of social accounts (Google, GitHub) connected to the authenticated user.",
    responses={
        200: SocialAccountSerializer(many=True),
        401: ErrorResponseSerializer,
    },
)
class ListSocialAccountsView(generics.ListAPIView):
    """
    GET /auth/oauth/accounts/
    List all social accounts connected to the current user
    """

    serializer_class = SocialAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get social accounts for authenticated user"""
        return SocialAccount.objects.filter(user=self.request.user)


@extend_schema(
    tags=["OAuth"],
    summary="Disconnect social account",
    description="""
    Disconnect a social account (Google or GitHub) from the authenticated user.
    
    **Note:** You must have a password set or at least one other social account 
    connected before disconnecting, to ensure you can still log in.
    """,
    request=DisconnectSocialAccountSerializer,
    responses={
        200: MessageResponseSerializer,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
class DisconnectSocialAccountView(APIView):
    """
    POST /auth/oauth/disconnect/
    Disconnect a social account from current user
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Disconnect social account"""
        serializer = DisconnectSocialAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = serializer.validated_data["provider"]
        user = request.user

        try:
            # Get the social account
            social_account = SocialAccount.objects.get(user=user, provider=provider)

            # Check if user has password or other social accounts
            has_password = user.has_usable_password()
            other_social_accounts = (
                SocialAccount.objects.filter(user=user)
                .exclude(provider=provider)
                .exists()
            )

            if not has_password and not other_social_accounts:
                return Response(
                    {
                        "error": "Cannot disconnect last login method. "
                        "Set a password first or connect another social account."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Delete the social account
            social_account.delete()
            logger.info(f"User {user.email} disconnected {provider} account")

            return Response(
                {"message": f"{provider.title()} account disconnected successfully"},
                status=status.HTTP_200_OK,
            )

        except SocialAccount.DoesNotExist:
            return Response(
                {"error": f"No {provider} account connected"},
                status=status.HTTP_404_NOT_FOUND,
            )
