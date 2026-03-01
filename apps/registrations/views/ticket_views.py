"""Ticket tier views."""

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from apps.registrations.models import TicketTier
from apps.registrations.serializers import (
    TicketTierSerializer,
    TicketTierCreateUpdateSerializer,
)
from apps.registrations.permissions import CanManageTicketTiers
from apps.events.models import Event


class TicketTierViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ticket tier management.

    List: GET /events/{slug}/ticket-tiers/ - List all ticket tiers for an event
    Create: POST /events/{slug}/ticket-tiers/ - Create a new ticket tier (organizer only)
    Retrieve: GET /events/{slug}/ticket-tiers/{id}/ - Get ticket tier details
    Update: PATCH /events/{slug}/ticket-tiers/{id}/ - Update ticket tier (organizer only)
    Delete: DELETE /events/{slug}/ticket-tiers/{id}/ - Delete ticket tier (organizer only)
    """

    serializer_class = TicketTierSerializer
    lookup_field = "pk"

    def get_queryset(self):
        """Filter ticket tiers by event slug."""
        event_slug = self.kwargs.get("event_slug")
        event = get_object_or_404(Event, slug=event_slug, is_deleted=False)
        return TicketTier.objects.filter(event=event)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ["create", "update", "partial_update"]:
            return TicketTierCreateUpdateSerializer
        return TicketTierSerializer

    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), CanManageTicketTiers()]
        return [IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):
        """Create ticket tier for the event."""
        event_slug = self.kwargs.get("event_slug")
        event = get_object_or_404(Event, slug=event_slug, is_deleted=False)
        serializer.save(event=event)
