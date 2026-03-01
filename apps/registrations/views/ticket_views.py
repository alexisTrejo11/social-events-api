"""Ticket tier views."""

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema_view, extend_schema

from apps.registrations.models import TicketTier
from apps.registrations.serializers import (
    TicketTierSerializer,
    TicketTierCreateUpdateSerializer,
)
from apps.registrations.permissions import CanManageTicketTiers
from apps.events.models import Event
from common.serializers import (
    ErrorResponseSerializer,
    ValidationErrorSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=["Ticket Tiers"],
        summary="List ticket tiers for an event",
        description="Returns a list of all ticket tiers available for a specific event. "
        "Includes pricing, capacity, and availability information.",
        responses={
            200: TicketTierSerializer(many=True),
            404: ErrorResponseSerializer,
        },
    ),
    create=extend_schema(
        tags=["Ticket Tiers"],
        summary="Create a ticket tier",
        description="Create a new ticket tier for an event. "
        "Only accessible by event organizers. Allows setting name, price, capacity, and sales period.",
        request=TicketTierCreateUpdateSerializer,
        responses={
            201: TicketTierSerializer,
            400: ValidationErrorSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    retrieve=extend_schema(
        tags=["Ticket Tiers"],
        summary="Get ticket tier details",
        description="Returns detailed information for a specific ticket tier, "
        "including current availability and number of tickets sold.",
        responses={
            200: TicketTierSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    update=extend_schema(
        tags=["Ticket Tiers"],
        summary="Update a ticket tier (full update)",
        description="Update all fields of a ticket tier. Only accessible by event organizers.",
        request=TicketTierCreateUpdateSerializer,
        responses={
            200: TicketTierSerializer,
            400: ValidationErrorSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    partial_update=extend_schema(
        tags=["Ticket Tiers"],
        summary="Update a ticket tier (partial update)",
        description="Update specific fields of a ticket tier. Only accessible by event organizers.",
        request=TicketTierCreateUpdateSerializer,
        responses={
            200: TicketTierSerializer,
            400: ValidationErrorSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    destroy=extend_schema(
        tags=["Ticket Tiers"],
        summary="Delete a ticket tier",
        description="Delete a ticket tier from an event. "
        "Only accessible by event organizers. Cannot delete tiers with existing registrations.",
        responses={
            204: None,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
)
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
