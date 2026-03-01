from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.events.models import EventRole
from apps.events.permissions import has_event_role, is_event_org_manager

HOST = EventRole.Role.HOST
CO_HOST = EventRole.Role.CO_HOST
MODERATOR = EventRole.Role.MODERATOR


class IsCommentAuthorOrReadOnly(BasePermission):
    """
    Anyone can read comments on a published event.
    Only the author can edit or delete their own comment.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        # obj is a Comment instance
        return obj.author == request.user


class CanModerateComment(BasePermission):
    """
    Controls who can pin, hide, or soft-delete any comment on an event
    (not just their own).
    Granted to: event organizer, hosts, co-hosts, and moderators.
    """

    message = "You do not have permission to moderate comments on this event."

    def has_object_permission(self, request, view, obj):
        # obj is a Comment instance
        event = obj.event
        return (
            event.organizer == request.user
            or has_event_role(request.user, event, HOST, CO_HOST, MODERATOR)
            or is_event_org_manager(request.user, event)
        )


class CanCommentOnEvent(BasePermission):
    """
    Determines whether a user is allowed to post a new comment on an event.
    Rules:
    - Event must be published.
    - Private events: only confirmed registrants or org members can comment.
    - Public events: any authenticated user can comment.
    """

    message = "You must be registered for this event to leave a comment."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # The view must pass the event via the context or as a kwarg
        # Typically resolved from the URL: /events/{slug}/comments/
        event = view.get_event()  # TODO: implement get_event() in your view

        if event.status != "published":
            return False

        if not event.is_private:
            return True

        # Private event: must be a confirmed registrant or org member/host
        is_registered = event.registrations.filter(
            attendee=request.user, status="confirmed"
        ).exists()

        return (
            is_registered
            or event.organizer == request.user
            or has_event_role(request.user, event, HOST, CO_HOST, MODERATOR)
            or is_event_org_manager(request.user, event)
        )
