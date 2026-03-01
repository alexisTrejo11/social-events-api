"""Registration views."""

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.registrations.models import Registration
from apps.registrations.serializers import (
    RegistrationSerializer,
    RegistrationCreateSerializer,
    RegistrationUpdateSerializer,
    RegistrationCheckInSerializer,
)
from apps.registrations.permissions import (
    IsRegistrationOwner,
    IsRegistrationOwnerOrEventHost,
    CanManageRegistrations,
    CanCheckIn,
)
from apps.events.models import Event
from apps.events.permissions import IsEventHost


class EventRegistrationsListView(generics.ListAPIView):
    """
    List all registrations for an event.
    Only accessible by event organizer/host.

    GET /events/{slug}/registrations/
    """

    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated, IsEventHost]

    def get_queryset(self):
        """Filter registrations by event slug."""
        event_slug = self.kwargs.get("event_slug")
        event = get_object_or_404(Event, slug=event_slug, is_deleted=False)

        # Check permission manually since we need the event object
        self.check_object_permissions(self.request, event)

        return (
            Registration.objects.filter(event=event)
            .select_related("attendee", "ticket_tier", "event")
            .order_by("-registered_at")
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_for_event(request, event_slug):
    """
    Register the authenticated user for an event.

    POST /events/{slug}/register/
    """
    event = get_object_or_404(Event, slug=event_slug, is_deleted=False)

    serializer = RegistrationCreateSerializer(
        data=request.data, context={"request": request, "event": event}
    )
    serializer.is_valid(raise_exception=True)
    registration = serializer.save()

    # TODO: Send confirmation email
    # from apps.registrations.tasks import send_registration_confirmation
    # send_registration_confirmation.delay(registration.id)

    return Response(
        RegistrationSerializer(registration, context={"request": request}).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def cancel_registration(request, event_slug):
    """
    Cancel the authenticated user's registration for an event.

    DELETE /events/{slug}/register/
    """
    event = get_object_or_404(Event, slug=event_slug, is_deleted=False)

    try:
        registration = Registration.objects.get(event=event, attendee=request.user)
    except Registration.DoesNotExist:
        return Response(
            {"detail": "You are not registered for this event."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Don't allow cancelling if event has already started
    if event.start_date < timezone.now():
        return Response(
            {"detail": "Cannot cancel registration after event has started."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Don't allow cancelling if already cancelled
    if registration.status == Registration.Status.CANCELLED:
        return Response(
            {"detail": "Registration is already cancelled."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Cancel the registration
    registration.status = Registration.Status.CANCELLED
    registration.cancelled_at = timezone.now()
    registration.cancelled_by = request.user
    registration.save(update_fields=["status", "cancelled_at", "cancelled_by"])

    # TODO: Send cancellation confirmation
    # from apps.registrations.tasks import send_cancellation_confirmation
    # send_cancellation_confirmation.delay(registration.id)

    return Response(
        {"detail": "Registration cancelled successfully."},
        status=status.HTTP_204_NO_CONTENT,
    )


class UserRegistrationsListView(generics.ListAPIView):
    """
    List all registrations for the authenticated user.

    GET /users/me/registrations/
    """

    serializer_class = RegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return registrations for the current user."""
        return (
            Registration.objects.filter(attendee=self.request.user)
            .select_related("attendee", "ticket_tier", "event")
            .order_by("-registered_at")
        )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, CanManageRegistrations])
def update_registration_status(request, event_slug, registration_id):
    """
    Update registration status (approve, reject, move to waitlist).
    Only accessible by event organizer/host.

    PATCH /events/{slug}/registrations/{id}/
    """
    event = get_object_or_404(Event, slug=event_slug, is_deleted=False)
    registration = get_object_or_404(Registration, id=registration_id, event=event)

    # Check permission
    permission = CanManageRegistrations()
    if not permission.has_object_permission(request, None, registration):
        return Response(
            {
                "detail": "You do not have permission to manage registrations for this event."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = RegistrationUpdateSerializer(
        registration, data=request.data, partial=True, context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    # TODO: Send status update notification
    # from apps.registrations.tasks import send_status_update_notification
    # send_status_update_notification.delay(registration.id)

    return Response(
        RegistrationSerializer(registration, context={"request": request}).data,
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated, CanCheckIn])
def check_in_attendee(request, event_slug, registration_id):
    """
    Mark an attendee as checked in (attended).
    Accessible by event organizer/host/volunteer.

    POST /events/{slug}/registrations/{id}/check-in/
    """
    event = get_object_or_404(Event, slug=event_slug, is_deleted=False)
    registration = get_object_or_404(Registration, id=registration_id, event=event)

    # Check permission
    permission = CanCheckIn()
    if not permission.has_object_permission(request, None, registration):
        return Response(
            {
                "detail": "You do not have permission to check in attendees for this event."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = RegistrationCheckInSerializer(
        data={}, context={"request": request, "registration": registration}
    )
    serializer.is_valid(raise_exception=True)

    # Mark as attended and record check-in time
    registration.status = Registration.Status.ATTENDED
    registration.checked_in_at = timezone.now()
    registration.save(update_fields=["status", "checked_in_at"])

    return Response(
        RegistrationSerializer(registration, context={"request": request}).data,
        status=status.HTTP_200_OK,
    )
