"""User-specific event views (favorites, feed, etc.)."""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.events.models import Event
from apps.events.serializers import EventListSerializer


class UserFavoriteEventsView(generics.ListAPIView):
    """
    List all events favorited by the authenticated user.

    GET /users/me/favorite-events/ - List user's favorite events
    """

    serializer_class = EventListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return events favorited by the current user."""
        return (
            Event.objects.filter(favorites=self.request.user, is_deleted=False)
            .select_related(
                "organizer",
                "organization",
                "category",
                "location",
            )
            .prefetch_related("tags")
            .order_by("-start_date")
        )
