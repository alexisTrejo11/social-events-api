from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status

from apps.events.models import Event
from apps.organizations.models import Organization
from apps.users.tests.helpers import auth_client, unverified_user, verified_user


def _future_event_payload(**overrides):
    start = timezone.now() + timedelta(days=5)
    end = start + timedelta(hours=3)
    payload = {
        "title": "Community Meetup",
        "description": "Come hang out",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    payload.update(overrides)
    return payload


class EventIntegrationTests(TestCase):
    def test_create_get_publish_happy_path(self):
        user = verified_user()
        client = auth_client(user)

        create = client.post(
            "/api/v2/events/", _future_event_payload(), format="json"
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)

        event = Event.objects.get(title="Community Meetup")
        self.assertEqual(event.status, Event.Status.DRAFT)

        detail = client.get(f"/api/v2/events/{event.slug}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["title"], "Community Meetup")

        publish = client.post(
            f"/api/v2/events/{event.slug}/publish/", {}, format="json"
        )
        self.assertEqual(publish.status_code, status.HTTP_200_OK)
        self.assertEqual(publish.data["status"], "published")

    def test_unverified_user_cannot_create_event(self):
        client = auth_client(unverified_user())
        response = client.post(
            "/api/v2/events/", _future_event_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_dates_return_400(self):
        client = auth_client(verified_user())
        start = timezone.now() + timedelta(days=5)
        response = client.post(
            "/api/v2/events/",
            _future_event_payload(
                start_date=start.isoformat(),
                end_date=(start - timedelta(hours=1)).isoformat(),
            ),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_event_returns_404(self):
        client = auth_client(verified_user())
        response = client.get("/api/v2/events/missing-event/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class EndToEndFlowTests(TestCase):
    """verified user → org → event → publish → register → comment"""

    def test_org_event_register_comment_chain(self):
        host = verified_user(email="host@example.com")
        guest = verified_user(email="guest@example.com")
        host_client = auth_client(host)
        guest_client = auth_client(guest)

        org_resp = host_client.post(
            "/api/v2/organizations/",
            {"name": "Chain Org"},
            format="json",
        )
        self.assertEqual(org_resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Organization.objects.filter(name="Chain Org").exists())

        event_resp = host_client.post(
            "/api/v2/events/",
            _future_event_payload(title="Chain Event"),
            format="json",
        )
        self.assertEqual(event_resp.status_code, status.HTTP_201_CREATED)
        event = Event.objects.get(title="Chain Event")

        publish = host_client.post(
            f"/api/v2/events/{event.slug}/publish/", {}, format="json"
        )
        self.assertEqual(publish.status_code, status.HTTP_200_OK)

        register = guest_client.post(
            f"/api/v2/events/{event.slug}/register/", {}, format="json"
        )
        self.assertEqual(register.status_code, status.HTTP_201_CREATED)

        comment = guest_client.post(
            f"/api/v2/events/{event.slug}/comments/",
            {"content": "See you there!"},
            format="json",
        )
        self.assertEqual(comment.status_code, status.HTTP_201_CREATED)
        self.assertEqual(comment.data["content"], "See you there!")
