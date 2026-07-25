from django.test import TestCase
from rest_framework import status

from apps.organizations.models import Organization
from apps.users.tests.helpers import auth_client, verified_user


class OrganizationIntegrationTests(TestCase):
    def test_create_then_get_organization(self):
        user = verified_user()
        client = auth_client(user)

        create = client.post(
            "/api/v2/organizations/",
            {"name": "Acme Events", "description": "We host things"},
            format="json",
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)

        org = Organization.objects.get(name="Acme Events")
        detail = client.get(f"/api/v2/organizations/{org.slug}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["name"], "Acme Events")

    def test_get_unknown_organization_returns_404(self):
        client = auth_client(verified_user())
        response = client.get("/api/v2/organizations/does-not-exist/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
