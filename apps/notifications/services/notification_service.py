"""Centralized notification service for creating and managing notifications."""

from typing import Optional, List
from django.contrib.auth import get_user_model
from apps.notifications.models import Notification
from apps.events.models import Event
from apps.organizations.models import Organization

User = get_user_model()


class NotificationService:
    """
    Centralized service for creating in-app notifications.
    Handles all notification creation logic in one place.
    """

    @staticmethod
    def create_notification(
        recipient: User,
        notification_type: str,
        title: str,
        body: str = "",
        event: Optional[Event] = None,
        organization: Optional[Organization] = None,
        actor: Optional[User] = None,
    ) -> Notification:
        """
        Create a new notification.

        Args:
            recipient: User who will receive the notification
            notification_type: Type from Notification.NotificationType
            title: Notification title
            body: Notification body (optional)
            event: Related event (optional)
            organization: Related organization (optional)
            actor: User who triggered the notification (optional)

        Returns:
            Created Notification instance
        """
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            body=body,
            event=event,
            organization=organization,
            actor=actor,
        )
        return notification

    @staticmethod
    def create_bulk_notifications(
        recipients: List[User],
        notification_type: str,
        title: str,
        body: str = "",
        event: Optional[Event] = None,
        organization: Optional[Organization] = None,
        actor: Optional[User] = None,
    ) -> List[Notification]:
        """
        Create notifications for multiple recipients efficiently.

        Args:
            recipients: List of users who will receive the notification
            notification_type: Type from Notification.NotificationType
            title: Notification title
            body: Notification body (optional)
            event: Related event (optional)
            organization: Related organization (optional)
            actor: User who triggered the notification (optional)

        Returns:
            List of created Notification instances
        """
        notifications = [
            Notification(
                recipient=recipient,
                notification_type=notification_type,
                title=title,
                body=body,
                event=event,
                organization=organization,
                actor=actor,
            )
            for recipient in recipients
        ]
        return Notification.objects.bulk_create(notifications)

    # Event-related notifications

    @staticmethod
    def notify_event_invitation(
        recipient: User, event: Event, actor: User
    ) -> Notification:
        """Notify user of event invitation."""
        return NotificationService.create_notification(
            recipient=recipient,
            notification_type=Notification.NotificationType.EVENT_INVITE,
            title=f"You're invited to {event.title}",
            body=f"{actor.get_full_name()} invited you to attend {event.title}",
            event=event,
            actor=actor,
        )

    @staticmethod
    def notify_event_update(event: Event, actor: User) -> List[Notification]:
        """Notify all registered attendees of event update."""
        recipients = User.objects.filter(
            registrations__event=event,
            registrations__status="confirmed",
        ).distinct()

        return NotificationService.create_bulk_notifications(
            recipients=list(recipients),
            notification_type=Notification.NotificationType.EVENT_UPDATE,
            title=f"Event Update: {event.title}",
            body=f"{event.title} has been updated. Check the event page for details.",
            event=event,
            actor=actor,
        )

    @staticmethod
    def notify_event_cancelled(event: Event) -> List[Notification]:
        """Notify all registered attendees of event cancellation."""
        recipients = User.objects.filter(
            registrations__event=event,
            registrations__status="confirmed",
        ).distinct()

        return NotificationService.create_bulk_notifications(
            recipients=list(recipients),
            notification_type=Notification.NotificationType.EVENT_CANCELLED,
            title=f"Event Cancelled: {event.title}",
            body=f"Unfortunately, {event.title} has been cancelled.",
            event=event,
            actor=event.organizer,
        )

    @staticmethod
    def notify_event_reminder(recipient: User, event: Event) -> Notification:
        """Send event reminder to attendee."""
        return NotificationService.create_notification(
            recipient=recipient,
            notification_type=Notification.NotificationType.REMINDER,
            title=f"Reminder: {event.title}",
            body=f"{event.title} starts soon on {event.start_date.strftime('%B %d at %H:%M')}",
            event=event,
        )

    # Registration-related notifications

    @staticmethod
    def notify_registration_confirmed(recipient: User, event: Event) -> Notification:
        """Notify user their registration was confirmed."""
        return NotificationService.create_notification(
            recipient=recipient,
            notification_type=Notification.NotificationType.REGISTRATION_CONFIRMED,
            title=f"Registration Confirmed: {event.title}",
            body=f"Your registration for {event.title} has been confirmed!",
            event=event,
        )

    @staticmethod
    def notify_registration_pending(recipient: User, event: Event) -> Notification:
        """Notify user their registration is pending approval."""
        return NotificationService.create_notification(
            recipient=recipient,
            notification_type=Notification.NotificationType.REGISTRATION_PENDING,
            title=f"Registration Pending: {event.title}",
            body=f"Your registration for {event.title} is pending organizer approval.",
            event=event,
        )

    # Social notifications

    @staticmethod
    def notify_new_follower(recipient: User, follower: User) -> Notification:
        """Notify user they have a new follower."""
        return NotificationService.create_notification(
            recipient=recipient,
            notification_type=Notification.NotificationType.NEW_FOLLOWER,
            title="New Follower",
            body=f"{follower.get_full_name()} started following you",
            actor=follower,
        )

    @staticmethod
    def notify_comment_reply(
        recipient: User, event: Event, actor: User
    ) -> Notification:
        """Notify user someone replied to their comment."""
        return NotificationService.create_notification(
            recipient=recipient,
            notification_type=Notification.NotificationType.COMMENT_REPLY,
            title="New Reply",
            body=f"{actor.get_full_name()} replied to your comment on {event.title}",
            event=event,
            actor=actor,
        )

    # Organization-related notifications

    @staticmethod
    def notify_org_invitation(
        recipient: User, organization: Organization, actor: User
    ) -> Notification:
        """Notify user of organization invitation."""
        return NotificationService.create_notification(
            recipient=recipient,
            notification_type=Notification.NotificationType.ORG_INVITE,
            title=f"Invitation to join {organization.name}",
            body=f"{actor.get_full_name()} invited you to join {organization.name}",
            organization=organization,
            actor=actor,
        )

    # Utility methods

    @staticmethod
    def mark_all_as_read(user: User) -> int:
        """Mark all notifications as read for a user."""
        return Notification.objects.filter(recipient=user, is_read=False).update(
            is_read=True
        )

    @staticmethod
    def delete_old_notifications(days: int = 30) -> int:
        """Delete notifications older than specified days."""
        from django.utils import timezone
        from datetime import timedelta

        cutoff_date = timezone.now() - timedelta(days=days)
        count, _ = Notification.objects.filter(
            created_at__lt=cutoff_date, is_read=True
        ).delete()
        return count
