"""Shared helpers for API integration tests."""

from rest_framework.test import APIClient

from apps.users.tests.factories import UserFactory

DEFAULT_PASSWORD = "Str0ng!Pass"


def verified_user(**kwargs):
    """Create a user with email_verified=True (required for many write endpoints)."""
    kwargs.setdefault("email_verified", True)
    kwargs.setdefault("password", DEFAULT_PASSWORD)
    return UserFactory(**kwargs)


def unverified_user(**kwargs):
    """Create a user that has not verified email."""
    kwargs.setdefault("email_verified", False)
    kwargs.setdefault("password", DEFAULT_PASSWORD)
    return UserFactory(**kwargs)


def auth_client(user=None):
    """Return an APIClient, optionally force-authenticated as ``user``."""
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client
