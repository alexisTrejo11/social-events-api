"""
OAuth/Social Authentication Serializers
"""

import logging
from rest_framework import serializers
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class GoogleLoginSerializer(SocialLoginSerializer):
    """
    Serializer for Google OAuth2 login
    Accepts an access_token from Google and authenticates the user
    """

    adapter_class = GoogleOAuth2Adapter

    def validate(self, attrs):
        """
        Validate the Google access token
        """
        logger.info("Validating Google OAuth login")
        return super().validate(attrs)


class GitHubLoginSerializer(SocialLoginSerializer):
    """
    Serializer for GitHub OAuth2 login
    Accepts an access_token from GitHub and authenticates the user
    """

    adapter_class = GitHubOAuth2Adapter

    def validate(self, attrs):
        """
        Validate the GitHub access token
        """
        logger.info("Validating GitHub OAuth login")
        return super().validate(attrs)


class SocialAuthCallbackSerializer(serializers.Serializer):
    """
    Serializer for OAuth callback with authorization code
    """

    code = serializers.CharField(
        required=True, help_text="Authorization code from OAuth provider"
    )
    state = serializers.CharField(
        required=False, help_text="State parameter for CSRF protection"
    )


class SocialAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying connected social accounts
    """

    provider = serializers.CharField(source="provider.upper")
    provider_account_id = serializers.CharField(source="uid")

    class Meta:
        model = SocialAccount
        fields = ["id", "provider", "provider_account_id", "date_joined"]
        read_only_fields = fields


class OAuthLoginResponseSerializer(serializers.Serializer):
    """
    Response serializer for successful OAuth login
    """

    access = serializers.CharField(help_text="JWT access token")
    refresh = serializers.CharField(help_text="JWT refresh token")
    user = serializers.DictField(help_text="User information")

    class Meta:
        fields = ["access", "refresh", "user"]


class ConnectSocialAccountSerializer(serializers.Serializer):
    """
    Serializer for connecting a social account to existing user
    """

    access_token = serializers.CharField(
        required=True, help_text="Access token from OAuth provider (Google or GitHub)"
    )

    def validate_access_token(self, value):
        """
        Validate that access token is provided
        """
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid access token")
        return value


class DisconnectSocialAccountSerializer(serializers.Serializer):
    """
    Serializer for disconnecting a social account
    """

    provider = serializers.ChoiceField(
        choices=["google", "github"],
        required=True,
        help_text="Social provider to disconnect (google or github)",
    )
