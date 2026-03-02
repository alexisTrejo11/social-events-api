"""Centralized notification service for creating and managing notifications."""

from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING
from django.contrib.auth import get_user_model
from apps.notifications.models import Notification
from apps.events.models import Event
from apps.organizations.models import Organization

if TYPE_CHECKING:
    User = get_user_model()
else:
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
