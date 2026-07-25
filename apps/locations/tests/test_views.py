from django.test import TestCase
from rest_framework import status

from apps.locations.tests.factories import LocationFactory
from apps.users.tests.helpers import auth_client, verified_user


class LocationIntegrationTests(TestCase):
    def test_get_location_after_orm_seed(self):
        location = LocationFactory()
        client = auth_client(verified_user())

        detail = client.get(f"/api/v2/locations/{location.id}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["city"], location.city)

    def test_unauthenticated_list_returns_401(self):
        response = auth_client().get("/api/v2/locations/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_admin_create_returns_403(self):
        client = auth_client(verified_user())
        response = client.post(
            "/api/v2/locations/",
            {
                "address_line_1": "1 Main",
                "city": "Austin",
                "country": "US",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
