"""
Allauth custom adapters for social authentication
"""

import logging
from typing import Any
from django.conf import settings
from django.http import HttpRequest
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_field, user_username

logger = logging.getLogger(__name__)


class AccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter to handle user registration and email verification
    """

    def is_open_for_signup(self, request: HttpRequest) -> bool:
        """
        Whether to allow sign ups.
        """
        return True

    def save_user(self, request, user, form, commit=True):
        """
        Saves a new `User` instance using information provided in the
        signup form.
        """
        data = form.cleaned_data
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        email = data.get("email")
        username = data.get("username")

        user_email(user, email)
        user_username(user, username)
        if first_name:
            user_field(user, "first_name", first_name)
        if last_name:
            user_field(user, "last_name", last_name)

        if "password1" in data:
            user.set_password(data["password1"])
        else:
            user.set_unusable_password()

        if commit:
            user.save()
            logger.info(f"New user registered: {user.email}")

        return user


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter to handle OAuth login/signup
    """

    def is_open_for_signup(self, request: HttpRequest, sociallogin: Any) -> bool:
        """
        Whether social sign ups are allowed.
        """
        return True

    def populate_user(self, request: HttpRequest, sociallogin: Any, data: dict):
        """
        Populate user information from social provider data
        """
        user = super().populate_user(request, sociallogin, data)

        # Get provider-specific data
        provider = sociallogin.account.provider
        extra_data = sociallogin.account.extra_data

        # Set user fields from social data
        if provider == "google":
            user.first_name = extra_data.get("given_name", "")
            user.last_name = extra_data.get("family_name", "")
            # Google provides verified emails
            if extra_data.get("email_verified", False):
                user.email_verified = True

        elif provider == "github":
            # GitHub may provide name as a single field
            name = extra_data.get("name", "")
            if name:
                name_parts = name.split(" ", 1)
                user.first_name = name_parts[0]
                if len(name_parts) > 1:
                    user.last_name = name_parts[1]

            # Set bio if available
            if extra_data.get("bio"):
                user.bio = extra_data.get("bio", "")[:500]  # Limit length

        logger.info(f"OAuth user created/updated via {provider}: {user.email}")
        return user

    def pre_social_login(self, request: HttpRequest, sociallogin: Any) -> None:
        """
        Invoked just after a user successfully logged in using social authentication.
        Connect social account to existing user if email matches.
        """
        # If the user is already logged in, just connect the account
        if request.user.is_authenticated:
            return

        # If the social account is already connected to a user, skip
        if sociallogin.is_existing:
            return

        # Try to connect to existing user with same email
        try:
            email = sociallogin.account.extra_data.get("email", "").lower()
            if not email:
                return

            # Look for existing user with this email
            from django.contrib.auth import get_user_model

            User = get_user_model()

            try:
                user = User.objects.get(email__iexact=email)
                # Connect this social account to the existing user
                sociallogin.connect(request, user)
                logger.info(
                    f"Connected social account {sociallogin.account.provider} "
                    f"to existing user: {email}"
                )
            except User.DoesNotExist:
                # No existing user, will create new one
                pass

        except Exception as e:
            logger.error(f"Error in pre_social_login: {e}")

    def save_user(self, request: HttpRequest, sociallogin: Any, form=None):
        """
        Save the user object after social login
        """
        user = super().save_user(request, sociallogin, form)

        # Mark email as verified for OAuth users
        if sociallogin.account.provider in ["google", "github"]:
            from allauth.account.models import EmailAddress

            EmailAddress.objects.filter(user=user, email__iexact=user.email).update(
                verified=True, primary=True
            )

        return user
