from unittest.mock import patch

from django.test import TestCase
from rest_framework import status

from apps.users.tests.helpers import (
    DEFAULT_PASSWORD,
    auth_client,
    verified_user,
)


class UserAuthIntegrationTests(TestCase):
    @patch("apps.users.tasks.send_verification_email")
    def test_register_login_me_happy_path(self, _mock_email):
        client = auth_client()
        email = "newuser@example.com"

        register = client.post(
            "/api/v2/auth/register/",
            {
                "email": email,
                "password": DEFAULT_PASSWORD,
                "first_name": "New",
                "last_name": "User",
            },
            format="json",
        )
        self.assertEqual(register.status_code, status.HTTP_201_CREATED)
        self.assertEqual(register.data["user"]["email"], email)

        login = client.post(
            "/api/v2/auth/login/",
            {"email": email, "password": DEFAULT_PASSWORD},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn("access", login.data["tokens"])

        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['tokens']['access']}"
        )
        me = client.get("/api/v2/users/me/")
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["email"], email)

    @patch("apps.users.tasks.send_verification_email")
    def test_register_weak_password_returns_400(self, _mock_email):
        client = auth_client()
        response = client.post(
            "/api/v2/auth/register/",
            {
                "email": "weak@example.com",
                "password": "weak",
                "first_name": "Weak",
                "last_name": "Pass",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_wrong_credentials_returns_400(self):
        verified_user(email="known@example.com")
        client = auth_client()
        response = client.post(
            "/api/v2/auth/login/",
            {"email": "known@example.com", "password": "WrongPass1!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
