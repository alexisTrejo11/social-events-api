import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from apps.locations.models import Location
from apps.locations.serializers import (
    LocationListSerializer,
    LocationDetailSerializer,
    LocationCreateUpdateSerializer,
)
from apps.locations.filters import LocationFilter
from common.serializers import (
    LocationDeletionErrorSerializer,
    ErrorResponseSerializer,
    ValidationErrorSerializer,
)
from common.throttling import ReadHeavyThrottle, WriteSensitiveThrottle

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="List all locations",
        description="Returns a paginated list of all locations. Supports filtering, search, and ordering. "
        "Search is performed on name, city, country, and address fields.",
        tags=["Locations"],
        responses={
            200: LocationListSerializer(many=True),
            401: ErrorResponseSerializer,
        },
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search term to filter locations by name, city, country, or address",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Order results by field. Prefix with '-' for descending. "
                "Options: name, city, country",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Get location details",
        description="Returns detailed information for a specific location including geographic coordinates.",
        tags=["Locations"],
        responses={
            200: LocationDetailSerializer,
            401: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    create=extend_schema(
        summary="Create a new location",
        description="Admin only. Creates a new location. Validates that virtual locations have URLs "
        "and physical locations have required address fields.",
        tags=["Locations"],
        request=LocationCreateUpdateSerializer,
        responses={
            201: LocationDetailSerializer,
            400: ValidationErrorSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
        },
    ),
    update=extend_schema(
        summary="Update a location",
        description="Admin only. Fully updates a location with new data.",
        tags=["Locations"],
        request=LocationCreateUpdateSerializer,
        responses={
            200: LocationDetailSerializer,
            400: ValidationErrorSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    partial_update=extend_schema(
        summary="Partially update a location",
        description="Admin only. Partially updates a location with provided fields.",
        tags=["Locations"],
        request=LocationCreateUpdateSerializer,
        responses={
            200: LocationDetailSerializer,
            400: ValidationErrorSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    destroy=extend_schema(
        summary="Delete a location",
        description="Admin only. Deletes a location. Cannot delete if the location is "
        "associated with any organizations or events.",
        tags=["Locations"],
        responses={
            204: None,
            400: LocationDeletionErrorSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
)
class LocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing physical and virtual event locations.

    Locations can be either physical (with address and coordinates) or virtual (with URL).
    Admins can create, update, and delete locations. Authenticated users can view locations.
    Locations cannot be deleted if they are in use by organizations or events.

    Actions:
    - list: Get all locations with filtering, search, and ordering
    - create: Create a new location (admin only)
    - retrieve: Get location details by ID
    - update: Fully update a location (admin only, PUT)
    - partial_update: Partially update a location (admin only, PATCH)
    - destroy: Delete a location (admin only, fails if in use)
    """

    queryset = Location.objects.all()
    filterset_class = LocationFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["name", "city", "country", "address_line_1"]
    ordering_fields = ["name", "city", "country"]
    ordering = ["city", "name"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "list":
            return LocationListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return LocationCreateUpdateSerializer
        return LocationDetailSerializer

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_throttles(self):
        """Return appropriate throttles based on action."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [WriteSensitiveThrottle()]
        return [ReadHeavyThrottle()]

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
            error_data = {
                "error": "Cannot delete location that is being used by organizations or events.",
                "organizations_count": location.organizations.count(),
                "events_count": location.events.count(),
            }
            serializer = LocationDeletionErrorSerializer(error_data)
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)

        return super().destroy(request, *args, **kwargs)
