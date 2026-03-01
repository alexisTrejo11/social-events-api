from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.events.models import EventRole
from apps.organizations.models import OrganizationMembership


def get_event_role(user, event) -> EventRole | None:
    """Returns the EventRole object for a user on a specific event, or None."""
    try:
        return EventRole.objects.get(user=user, event=event)
    except EventRole.DoesNotExist:
        return None


def has_event_role(user, event, *roles) -> bool:
    """Returns True if the user holds any of the given roles on the event."""
    if not user or not user.is_authenticated:
        return False
    event_role = get_event_role(user, event)
    return event_role is not None and event_role.role in roles


def is_event_org_manager(user, event) -> bool:
    """
    Returns True if the event belongs to an organization and the user
    is at least a Manager in that organization.
    This allows org managers to administer events they didn't personally create.
    """
    if not event.organization:
        return False
    try:
        membership = OrganizationMembership.objects.get(
            user=user, organization=event.organization
        )
        return membership.role in (
            OrganizationMembership.Role.OWNER,
            OrganizationMembership.Role.ADMIN,
            OrganizationMembership.Role.MANAGER,
        )
    except OrganizationMembership.DoesNotExist:
        return False


# Role constants
HOST = EventRole.Role.HOST
CO_HOST = EventRole.Role.CO_HOST
SPEAKER = EventRole.Role.SPEAKER
VOLUNTEER = EventRole.Role.VOLUNTEER
MODERATOR = EventRole.Role.MODERATOR


class IsEventOrganizer(BasePermission):
    """
    The user who created the event (Event.organizer).
    Full control: edit, delete, publish, cancel.
    Also grants access to org managers if the event belongs to an org.
    """

    message = "Only the event organizer can perform this action."

    def has_object_permission(self, request, view, obj):
        # obj is an Event instance
        return obj.organizer == request.user or is_event_org_manager(request.user, obj)


class IsEventHost(BasePermission):
    """
    The organizer OR anyone with a Host / Co-host role.
    Used for actions like approving registrations, check-ins,
    pinning comments, managing the event on the day.
    """

    message = "You must be a host or co-host of this event."

    def has_object_permission(self, request, view, obj):
        return (
            obj.organizer == request.user
            or has_event_role(request.user, obj, HOST, CO_HOST)
            or is_event_org_manager(request.user, obj)
        )


class CanManageEventStaff(BasePermission):
    """
    Only the organizer or org manager can assign/remove event roles
    (hosts, speakers, volunteers, moderators).
    """

    message = "Only the event organizer or org manager can manage event staff."

    def has_object_permission(self, request, view, obj):
        # obj is an Event instance
        return obj.organizer == request.user or is_event_org_manager(request.user, obj)


class IsPublishedAndPublicOrHost(BasePermission):
    """
    Read access rules for event detail:
    - Published + public  → anyone
    - Published + private → org members or registered attendees
    - Draft / cancelled   → only the organizer / host
    """

    message = "You do not have permission to view this event."

    def has_object_permission(self, request, view, obj):
        # Organizer and hosts always have access
        if (
            obj.organizer == request.user
            or has_event_role(request.user, obj, HOST, CO_HOST)
            or is_event_org_manager(request.user, obj)
        ):
            return True

        # Non-published events are invisible to the public
        if obj.status != "published":
            return False

        # Public published events: open to all
        if not obj.is_private:
            return True

        # Private published events: only org members or registered attendees
        if obj.organization and is_event_org_manager(request.user, obj):
            return True

        # Check if the user is a confirmed registrant
        return obj.registrations.filter(
            attendee=request.user, status="confirmed"
        ).exists()
