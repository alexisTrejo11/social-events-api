import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.locations.models import Location
from apps.locations.serializers import (
    LocationListSerializer,
    LocationDetailSerializer,
    LocationCreateUpdateSerializer,
)

logger = logging.getLogger(__name__)


class LocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing locations.

    list: Get all locations
    create: Create a new location
    retrieve: Get location details
    update: Update location (PATCH/PUT)
    destroy: Delete location
    """

    queryset = Location.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["name", "city", "country", "address_line_1"]
    ordering_fields = ["name", "city", "country"]
    ordering = ["city", "name"]
    filterset_fields = ["city", "country", "is_virtual"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "list":
            return LocationListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return LocationCreateUpdateSerializer
        return LocationDetailSerializer

    def list(self, request, *args, **kwargs):
        """List all locations"""
        logger.info("Fetching location list")
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Create a new location"""
        logger.info(f"Creating new location")
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Get location details"""
        logger.info(f"Fetching location {kwargs.get('pk')}")
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Update location"""
        logger.info(f"Updating location {kwargs.get('pk')}")
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Partially update location"""
        logger.info(f"Partially updating location {kwargs.get('pk')}")
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete location"""
        location = self.get_object()
        logger.info(f"Deleting location {location.id}")

        # Check if location is being used
        if location.organizations.exists() or location.events.exists():
            logger.warning(f"Attempt to delete location {location.id} that is in use")
            return Response(
                {
                    "error": "Cannot delete location that is being used by organizations or events.",
                    "organizations_count": location.organizations.count(),
                    "events_count": location.events.count(),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().destroy(request, *args, **kwargs)
