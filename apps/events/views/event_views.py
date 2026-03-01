"""Event views for CRUD and event-specific actions."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.utils import timezone
from django.db.models import Q, Prefetch

from apps.events.models import Event, EventRole
from apps.events.serializers import (
    EventListSerializer,
    EventDetailSerializer,
    EventCreateUpdateSerializer,
    EventPublishSerializer,
    EventCancelSerializer,
    EventRoleSerializer,
    EventRoleCreateSerializer,
    EventRoleUpdateSerializer,
)
from apps.events.permissions import (
    IsEventOrganizer,
    IsEventHost,
    CanManageEventStaff,
    IsPublishedAndPublicOrHost,
)
from apps.users.permissions import IsVerifiedUser
from apps.events.filters import EventFilter


class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for event CRUD and management.

    List: GET /events/ - List all published events (with filtering)
    Create: POST /events/ - Create a new event (authenticated users only)
    Retrieve: GET /events/{slug}/ - Get event details
    Update: PATCH /events/{slug}/ - Update event (organizer/host only)
    Delete: DELETE /events/{slug}/ - Soft delete event (organizer only)

    Custom actions:
    - POST /events/{slug}/publish/ - Publish draft event
    - POST /events/{slug}/cancel/ - Cancel event
    - POST /events/{slug}/favorite/ - Favorite event
    - DELETE /events/{slug}/favorite/ - Unfavorite event
    - GET /events/{slug}/roles/ - List event roles
    - POST /events/{slug}/roles/ - Assign event role
    - PATCH /events/{slug}/roles/{id}/ - Update role bio
    - DELETE /events/{slug}/roles/{id}/ - Remove role
    - GET /events/{slug}/occurrences/ - List recurring event occurrences
    """

    queryset = Event.objects.select_related(
        "organizer",
        "organization",
        "category",
        "location",
        "recurrence",
    ).prefetch_related("tags", "favorites")
    lookup_field = "slug"
    filterset_class = EventFilter

    def get_queryset(self):
        """Filter events based on permissions."""
        queryset = super().get_queryset()

        # Exclude soft-deleted events
        queryset = queryset.filter(is_deleted=False)

        # For list view, only show published events unless user is organizer/host
        if self.action == "list":
            user = self.request.user
            if user.is_authenticated:
                # Show published events + user's own events + events they host
                queryset = queryset.filter(
                    Q(status=Event.Status.PUBLISHED)
                    | Q(organizer=user)
                    | Q(roles__user=user)
                ).distinct()
            else:
                # Anonymous users see only published public events
                queryset = queryset.filter(
                    status=Event.Status.PUBLISHED, is_private=False
                )

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return EventListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return EventCreateUpdateSerializer
        elif self.action == "publish":
            return EventPublishSerializer
        elif self.action == "cancel":
            return EventCancelSerializer
        return EventDetailSerializer

    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action == "create":
            return [IsAuthenticated(), IsVerifiedUser()]
        elif self.action in ["update", "partial_update"]:
            return [IsAuthenticated(), IsEventHost()]
        elif self.action == "destroy":
            return [IsAuthenticated(), IsEventOrganizer()]
        elif self.action in ["publish", "cancel"]:
            return [IsAuthenticated(), IsEventOrganizer()]
        elif self.action == "retrieve":
            return [IsPublishedAndPublicOrHost()]
        elif self.action in ["favorite", "unfavorite"]:
            return [IsAuthenticated()]
        elif self.action == "list_roles":
            return [IsAuthenticatedOrReadOnly()]
        elif self.action in ["assign_role", "update_role", "remove_role"]:
            return [IsAuthenticated(), CanManageEventStaff()]
        return [IsAuthenticatedOrReadOnly()]

    def perform_destroy(self, instance):
        """Soft delete instead of hard delete."""
        instance.soft_delete()

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, slug=None):
        """Publish a draft event."""
        event = self.get_object()

        serializer = self.get_serializer(data={})
        serializer.context["event"] = event
        serializer.is_valid(raise_exception=True)

        event.status = Event.Status.PUBLISHED
        event.save(update_fields=["status"])

        return Response(
            EventDetailSerializer(event, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, slug=None):
        """Cancel an event."""
        event = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.context["event"] = event
        serializer.is_valid(raise_exception=True)

        event.status = Event.Status.CANCELLED
        event.save(update_fields=["status"])

        # TODO: Send cancellation notifications to all registered attendees
        # from apps.notifications.tasks import send_event_cancellation_notification
        # send_event_cancellation_notification.delay(event.id, serializer.validated_data.get("cancellation_reason"))

        return Response(
            EventDetailSerializer(event, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="favorite")
    def favorite(self, request, slug=None):
        """Add event to user's favorites."""
        event = self.get_object()

        if event.favorites.filter(id=request.user.id).exists():
            return Response(
                {"detail": "Event is already in your favorites."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        event.favorites.add(request.user)

        return Response(
            {"detail": "Event added to favorites."}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["delete"], url_path="favorite")
    def unfavorite(self, request, slug=None):
        """Remove event from user's favorites."""
        event = self.get_object()

        if not event.favorites.filter(id=request.user.id).exists():
            return Response(
                {"detail": "Event is not in your favorites."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        event.favorites.remove(request.user)

        return Response(
            {"detail": "Event removed from favorites."}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["get"], url_path="roles")
    def list_roles(self, request, slug=None):
        """List all staff roles for this event."""
        event = self.get_object()
        roles = event.roles.select_related("user", "assigned_by").all()
        serializer = EventRoleSerializer(roles, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="roles")
    def assign_role(self, request, slug=None):
        """Assign a new role to a user for this event."""
        event = self.get_object()

        serializer = EventRoleCreateSerializer(
            data=request.data, context={"request": request, "event": event}
        )
        serializer.is_valid(raise_exception=True)
        role = serializer.save()

        return Response(
            EventRoleSerializer(role, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["patch"],
        url_path="roles/(?P<role_id>[0-9]+)",
    )
    def update_role(self, request, slug=None, role_id=None):
        """Update event role bio."""
        event = self.get_object()

        try:
            role = event.roles.get(id=role_id)
        except EventRole.DoesNotExist:
            return Response(
                {"detail": "Role not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = EventRoleUpdateSerializer(
            role, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            EventRoleSerializer(role, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path="roles/(?P<role_id>[0-9]+)",
    )
    def remove_role(self, request, slug=None, role_id=None):
        """Remove a role assignment."""
        event = self.get_object()

        try:
            role = event.roles.get(id=role_id)
        except EventRole.DoesNotExist:
            return Response(
                {"detail": "Role not found."}, status=status.HTTP_404_NOT_FOUND
            )

        role.delete()

        return Response(
            {"detail": "Role removed successfully."}, status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=["get"], url_path="occurrences")
    def occurrences(self, request, slug=None):
        """
        List all occurrences of a recurring event.

        For now, returns child events linked via parent_event.
        In the future, this could generate occurrences on-the-fly based on recurrence rules.
        """
        event = self.get_object()

        if not event.recurrence:
            return Response(
                {"detail": "This event is not recurring."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        occurrences = event.occurrences.filter(is_deleted=False).order_by("start_date")
        serializer = EventListSerializer(
            occurrences, many=True, context={"request": request}
        )

        return Response(serializer.data)
