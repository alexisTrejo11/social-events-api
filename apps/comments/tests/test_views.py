from django.test import TestCase
from rest_framework import status

from apps.events.models import Event
from apps.events.tests.factories import EventFactory
from apps.users.tests.helpers import auth_client, verified_user


class CommentIntegrationTests(TestCase):
    def test_create_then_list_comments(self):
        organizer = verified_user(email="host@example.com")
        commenter = verified_user(email="fan@example.com")
        event = EventFactory(
            organizer=organizer, status=Event.Status.PUBLISHED
        )
        client = auth_client(commenter)

        create = client.post(
            f"/api/v2/events/{event.slug}/comments/",
            {"content": "Looking forward to it!"},
            format="json",
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create.data["content"], "Looking forward to it!")

        listing = client.get(f"/api/v2/events/{event.slug}/comments/")
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        results = listing.data["results"] if "results" in listing.data else listing.data
        self.assertEqual(len(results), 1)

    def test_comment_on_draft_event_returns_403(self):
        organizer = verified_user(email="draft-host@example.com")
        commenter = verified_user(email="draft-fan@example.com")
        event = EventFactory(organizer=organizer, status=Event.Status.DRAFT)
        client = auth_client(commenter)

        response = client.post(
            f"/api/v2/events/{event.slug}/comments/",
            {"content": "Too early"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_content_returns_400(self):
        event = EventFactory(status=Event.Status.PUBLISHED)
        client = auth_client(verified_user())

        response = client.post(
            f"/api/v2/events/{event.slug}/comments/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
