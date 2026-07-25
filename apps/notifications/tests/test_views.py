from django.test import TestCase
from rest_framework import status

from apps.notifications.tests.factories import NotificationFactory
from apps.users.tests.helpers import auth_client, verified_user


class NotificationIntegrationTests(TestCase):
    def test_list_and_mark_read_after_orm_seed(self):
        user = verified_user()
        notification = NotificationFactory(recipient=user)
        client = auth_client(user)

        listing = client.get("/api/v2/notifications/")
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        results = listing.data["results"] if "results" in listing.data else listing.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], notification.title)

        mark = client.post(f"/api/v2/notifications/{notification.id}/read/")
        self.assertEqual(mark.status_code, status.HTTP_200_OK)
        self.assertTrue(mark.data["is_read"])

    def test_unauthenticated_list_returns_401(self):
        response = auth_client().get("/api/v2/notifications/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
