from django.test import TestCase
from rest_framework import status

from apps.events.models import Event
from apps.events.tests.factories import EventFactory
from apps.users.tests.helpers import auth_client, verified_user


class RegistrationIntegrationTests(TestCase):
    def test_register_then_list_my_registrations(self):
        organizer = verified_user(email="organizer@example.com")
        attendee = verified_user(email="attendee@example.com")
        event = EventFactory(
            organizer=organizer, status=Event.Status.PUBLISHED
        )
        client = auth_client(attendee)

        register = client.post(
            f"/api/v2/events/{event.slug}/register/", {}, format="json"
        )
        self.assertEqual(register.status_code, status.HTTP_201_CREATED)
        self.assertEqual(register.data["status"], "confirmed")

        mine = client.get("/api/v2/users/me/registrations/")
        self.assertEqual(mine.status_code, status.HTTP_200_OK)
        results = mine.data["results"] if "results" in mine.data else mine.data
        self.assertEqual(len(results), 1)

    def test_unauthenticated_register_returns_401(self):
        event = EventFactory(status=Event.Status.PUBLISHED)
        response = auth_client().post(
            f"/api/v2/events/{event.slug}/register/", {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_double_register_returns_400(self):
        attendee = verified_user()
        event = EventFactory(status=Event.Status.PUBLISHED)
        client = auth_client(attendee)

        first = client.post(
            f"/api/v2/events/{event.slug}/register/", {}, format="json"
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second = client.post(
            f"/api/v2/events/{event.slug}/register/", {}, format="json"
        )
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
