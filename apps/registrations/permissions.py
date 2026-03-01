from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.events.models import EventRole
from apps.events.permissions import has_event_role, is_event_org_manager

HOST = EventRole.Role.HOST
CO_HOST = EventRole.Role.CO_HOST
VOLUNTEER = EventRole.Role.VOLUNTEER


class IsRegistrationOwner(BasePermission):
    """
    The attendee who made the registration.
    Can view their own registration and cancel it.
    """

    message = "You can only manage your own registration."

    def has_object_permission(self, request, view, obj):
        # obj is a Registration instance
        return obj.attendee == request.user


class IsRegistrationOwnerOrEventHost(BasePermission):
    """
    The attendee can view their own registration.
    The event host/organizer can view and modify any registration.
    Used on the registration detail endpoint.
    """

    def has_object_permission(self, request, view, obj):
        # obj is a Registration instance
        if obj.attendee == request.user:
            return True

        event = obj.event
        return (
            event.organizer == request.user
            or has_event_role(request.user, event, HOST, CO_HOST)
            or is_event_org_manager(request.user, event)
        )


class CanManageRegistrations(BasePermission):
    """
    Controls who can approve, reject, move to waitlist, or cancel
    other people's registrations.
    Only the organizer, hosts, and org managers qualify.
    """

    message = "You do not have permission to manage registrations for this event."

    def has_object_permission(self, request, view, obj):
        # obj is a Registration instance
        if request.method in SAFE_METHODS:
            # Read access: the attendee or any host-level role
            if obj.attendee == request.user:
                return True

        event = obj.event
        return (
            event.organizer == request.user
            or has_event_role(request.user, event, HOST, CO_HOST)
            or is_event_org_manager(request.user, event)
        )


class CanCheckIn(BasePermission):
    """
    Controls who can mark a registration as ATTENDED (check-in).
    Extends CanManageRegistrations to also allow volunteers,
    since they're typically the ones scanning tickets at the door.
    """

    message = "You do not have permission to check in attendees for this event."

    def has_object_permission(self, request, view, obj):
        # obj is a Registration instance
        event = obj.event
        return (
            event.organizer == request.user
            or has_event_role(request.user, event, HOST, CO_HOST, VOLUNTEER)
            or is_event_org_manager(request.user, event)
        )


class CanManageTicketTiers(BasePermission):
    """
    Only the event organizer or an org manager can create, edit,
    or deactivate ticket tiers.
    """

    message = "Only the event organizer can manage ticket tiers."

    def has_object_permission(self, request, view, obj):
        # obj is a TicketTier instance — navigate to its event
        event = obj.event
        return event.organizer == request.user or is_event_org_manager(
            request.user, event
        )
