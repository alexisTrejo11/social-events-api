"""Factory for creating and sending notifications based on templates."""

from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING
from django.contrib.auth import get_user_model
from apps.notifications.models import Notification
from apps.events.models import Event
from apps.organizations.models import Organization
from apps.notifications.services.notification_service import NotificationService
from apps.notifications.services.email_sender import EmailSender

if TYPE_CHECKING:
    User = get_user_model()
else:
    User = get_user_model()


class NotificationFactory:
    """
    Factory for creating notifications with corresponding emails.
    Each method corresponds to a template and handles the complete flow:
    1. Create notification in database
    2. Send email to user
    """

    def __init__(self):
        self.notification_service = NotificationService()
        self.email_sender = EmailSender()

    # ==================== Authentication Notifications ====================

    def send_welcome_notification(
        self,
        user: User,
    ) -> tuple[Optional[Notification], bool]:
        """
        Send welcome notification to new user.

        Args:
            user: The new user

        Returns:
            tuple: (notification, email_sent)
        """
        # For welcome emails, we typically don't create an in-app notification
        # Just send the email
        email_sent = self.email_sender.send_email(
            to_email=user.email,
            subject="Welcome to Social Events!",
            template_name="welcome",
            context={
                "user_name": user.get_full_name() or user.username,
            },
        )
        return (None, email_sent)

    def send_email_verification(
        self,
        user: User,
        verification_url: str,
    ) -> tuple[Optional[Notification], bool]:
        """
        Send email verification notification.

        Args:
            user: User to verify
            verification_url: URL for verification

        Returns:
            tuple: (notification, email_sent)
        """
        email_sent = self.email_sender.send_email(
            to_email=user.email,
            subject="Verify Your Email Address",
            template_name="verify_email",
            context={
                "user_name": user.get_full_name() or user.username,
                "verification_url": verification_url,
            },
        )
        return (None, email_sent)

    def send_password_reset(
        self,
        user: User,
        reset_url: str,
    ) -> tuple[Optional[Notification], bool]:
        """
        Send password reset notification.

        Args:
            user: User requesting reset
            reset_url: URL for password reset

        Returns:
            tuple: (notification, email_sent)
        """
        email_sent = self.email_sender.send_email(
            to_email=user.email,
            subject="Reset Your Password",
            template_name="password_reset",
            context={
                "user_name": user.get_full_name() or user.username,
                "reset_url": reset_url,
            },
        )
        return (None, email_sent)

    def send_password_changed(
        self,
        user: User,
    ) -> tuple[Optional[Notification], bool]:
        """
        Send password changed confirmation.

        Args:
            user: User whose password was changed

        Returns:
            tuple: (notification, email_sent)
        """
        email_sent = self.email_sender.send_email(
            to_email=user.email,
            subject="Your Password Was Changed",
            template_name="password_changed",
            context={
                "user_name": user.get_full_name() or user.username,
            },
        )
        return (None, email_sent)

    # ==================== Event Notifications ====================

    def send_event_invitation(
        self,
        recipient: User,
        event: Event,
        inviter: User,
        event_url: str,
    ) -> tuple[Notification, bool]:
        """
        Send event invitation notification.

        Args:
            recipient: User being invited
            event: Event to invite to
            inviter: User sending the invitation
            event_url: URL to the event

        Returns:
            tuple: (notification, email_sent)
        """
        # Create in-app notification
        notification = self.notification_service.create_notification(
            recipient=recipient,
            notification_type=Notification.NotificationType.EVENT_INVITE,
            title=f"You're invited to {event.title}",
            body=f"{inviter.get_full_name()} invited you to attend {event.title}",
            event=event,
            actor=inviter,
        )

        # Send email
        email_sent = self.email_sender.send_email(
            to_email=recipient.email,
            subject=f"You're Invited: {event.title}",
            template_name="event_invitation",
            context={
                "user_name": recipient.get_full_name() or recipient.username,
                "event_title": event.title,
                "event_url": event_url,
                "inviter_name": inviter.get_full_name() or inviter.username,
            },
        )

        return (notification, email_sent)

    def send_event_reminder(
        self,
        recipient: User,
        event: Event,
        event_url: str,
    ) -> tuple[Notification, bool]:
        """
        Send event reminder notification.

        Args:
            recipient: User to remind
            event: Event to remind about
            event_url: URL to the event

        Returns:
            tuple: (notification, email_sent)
        """
        # Create in-app notification
        notification = self.notification_service.create_notification(
            recipient=recipient,
            notification_type=Notification.NotificationType.REMINDER,
            title=f"Reminder: {event.title}",
            body=f"{event.title} starts soon on {event.start_date.strftime('%B %d at %H:%M')}",
            event=event,
        )

        # Send email
        email_sent = self.email_sender.send_email(
            to_email=recipient.email,
            subject=f"Reminder: {event.title}",
            template_name="event_reminder",
            context={
                "user_name": recipient.get_full_name() or recipient.username,
                "event_title": event.title,
                "event_date": event.start_date.strftime("%B %d, %Y at %H:%M"),
                "event_url": event_url,
            },
        )

        return (notification, email_sent)

    def send_event_update(
        self,
        event: Event,
        actor: User,
        event_url: str,
    ) -> tuple[List[Notification], int]:
        """
        Send event update notification to all attendees.

        Args:
            event: Event that was updated
            actor: User who updated the event
            event_url: URL to the event

        Returns:
            tuple: (notification_list, emails_sent_count)
        """
        # Get all confirmed attendees
        recipients = User.objects.filter(
            registrations__event=event,
            registrations__status="confirmed",
        ).distinct()

        # Create in-app notifications
        notifications = self.notification_service.create_bulk_notifications(
            recipients=list(recipients),
            notification_type=Notification.NotificationType.EVENT_UPDATE,
            title=f"Event Update: {event.title}",
            body=f"{event.title} has been updated. Check the event page for details.",
            event=event,
            actor=actor,
        )

        # Send emails to all recipients
        emails_sent = 0
        for recipient in recipients:
            sent = self.email_sender.send_email(
                to_email=recipient.email,
                subject=f"Event Update: {event.title}",
                template_name="event_update",
                context={
                    "user_name": recipient.get_full_name() or recipient.username,
                    "event_title": event.title,
                    "event_url": event_url,
                },
            )
            if sent:
                emails_sent += 1

        return (notifications, emails_sent)

    def send_event_cancelled(
        self,
        event: Event,
        event_url: str,
    ) -> tuple[List[Notification], int]:
        """
        Send event cancellation notification to all attendees.

        Args:
            event: Event that was cancelled
            event_url: URL to the event

        Returns:
            tuple: (notification_list, emails_sent_count)
        """
        # Get all confirmed attendees
        recipients = User.objects.filter(
            registrations__event=event,
            registrations__status="confirmed",
        ).distinct()

        # Create in-app notifications
        notifications = self.notification_service.create_bulk_notifications(
            recipients=list(recipients),
            notification_type=Notification.NotificationType.EVENT_CANCELLED,
            title=f"Event Cancelled: {event.title}",
            body=f"Unfortunately, {event.title} has been cancelled.",
            event=event,
            actor=event.organizer,
        )

        # Send emails to all recipients
        emails_sent = 0
        for recipient in recipients:
            sent = self.email_sender.send_email(
                to_email=recipient.email,
                subject=f"Event Cancelled: {event.title}",
                template_name="event_cancelled",
                context={
                    "user_name": recipient.get_full_name() or recipient.username,
                    "event_title": event.title,
                    "event_url": event_url,
                },
            )
            if sent:
                emails_sent += 1

        return (notifications, emails_sent)

    # ==================== Registration Notifications ====================

    def send_registration_confirmed(
        self,
        recipient: User,
        event: Event,
        event_url: str,
    ) -> tuple[Notification, bool]:
        """
        Send registration confirmation notification.

        Args:
            recipient: User whose registration was confirmed
            event: Event registered for
            event_url: URL to the event

        Returns:
            tuple: (notification, email_sent)
        """
        # Create in-app notification
        notification = self.notification_service.create_notification(
            recipient=recipient,
            notification_type=Notification.NotificationType.REGISTRATION_CONFIRMED,
            title=f"Registration Confirmed: {event.title}",
            body=f"Your registration for {event.title} has been confirmed!",
            event=event,
        )

        # Send email
        email_sent = self.email_sender.send_email(
            to_email=recipient.email,
            subject=f"Registration Confirmed: {event.title}",
            template_name="registration_confirmed",
            context={
                "user_name": recipient.get_full_name() or recipient.username,
                "event_title": event.title,
                "event_date": event.start_date.strftime("%B %d, %Y at %H:%M"),
                "event_url": event_url,
            },
        )

        return (notification, email_sent)

    def send_registration_pending(
        self,
        recipient: User,
        event: Event,
        event_url: str,
    ) -> tuple[Notification, bool]:
        """
        Send registration pending notification.

        Args:
            recipient: User whose registration is pending
            event: Event registered for
            event_url: URL to the event

        Returns:
            tuple: (notification, email_sent)
        """
        # Create in-app notification
        notification = self.notification_service.create_notification(
            recipient=recipient,
            notification_type=Notification.NotificationType.REGISTRATION_PENDING,
            title=f"Registration Pending: {event.title}",
            body=f"Your registration for {event.title} is pending organizer approval.",
            event=event,
        )

        # Send email
        email_sent = self.email_sender.send_email(
            to_email=recipient.email,
            subject=f"Registration Pending: {event.title}",
            template_name="registration_pending",
            context={
                "user_name": recipient.get_full_name() or recipient.username,
                "event_title": event.title,
                "event_url": event_url,
            },
        )

        return (notification, email_sent)

    def send_registration_waitlisted(
        self,
        recipient: User,
        event: Event,
        event_url: str,
    ) -> tuple[Optional[Notification], bool]:
        """
        Send registration waitlisted notification.

        Args:
            recipient: User who was waitlisted
            event: Event registered for
            event_url: URL to the event

        Returns:
            tuple: (notification, email_sent)
        """
        # Note: No specific notification type for waitlisted, using pending
        # You may want to add REGISTRATION_WAITLISTED to NotificationType enum

        # Send email
        email_sent = self.email_sender.send_email(
            to_email=recipient.email,
            subject=f"Waitlisted: {event.title}",
            template_name="registration_waitlisted",
            context={
                "user_name": recipient.get_full_name() or recipient.username,
                "event_title": event.title,
                "event_url": event_url,
            },
        )

        return (None, email_sent)

    def send_registration_cancelled(
        self,
        recipient: User,
        event: Event,
        event_url: str,
    ) -> tuple[Optional[Notification], bool]:
        """
        Send registration cancellation notification.

        Args:
            recipient: User whose registration was cancelled
            event: Event that was cancelled from
            event_url: URL to the event

        Returns:
            tuple: (notification, email_sent)
        """
        # Send email
        email_sent = self.email_sender.send_email(
            to_email=recipient.email,
            subject=f"Registration Cancelled: {event.title}",
            template_name="registration_cancelled",
            context={
                "user_name": recipient.get_full_name() or recipient.username,
                "event_title": event.title,
                "event_url": event_url,
            },
        )

        return (None, email_sent)

    def send_check_in_confirmation(
        self,
        recipient: User,
        event: Event,
        event_url: str,
    ) -> tuple[Optional[Notification], bool]:
        """
        Send check-in confirmation notification.

        Args:
            recipient: User who checked in
            event: Event checked into
            event_url: URL to the event

        Returns:
            tuple: (notification, email_sent)
        """
        # Send email
        email_sent = self.email_sender.send_email(
            to_email=recipient.email,
            subject=f"Check-in Confirmed: {event.title}",
            template_name="check_in_confirmation",
            context={
                "user_name": recipient.get_full_name() or recipient.username,
                "event_title": event.title,
                "event_url": event_url,
            },
        )

        return (None, email_sent)

    # ==================== User Action Notifications ====================

    def send_new_follower_notification(
        self,
        recipient: User,
        follower: User,
    ) -> tuple[Notification, bool]:
        """
        Send new follower notification.

        Args:
            recipient: User who was followed
            follower: User who followed

        Returns:
            tuple: (notification, email_sent)
        """
        # Create in-app notification
        notification = self.notification_service.create_notification(
            recipient=recipient,
            notification_type=Notification.NotificationType.NEW_FOLLOWER,
            title="New Follower",
            body=f"{follower.get_full_name()} started following you",
            actor=follower,
        )

        # Send email
        email_sent = self.email_sender.send_email(
            to_email=recipient.email,
            subject="You Have a New Follower!",
            template_name="new_follower",
            context={
                "user_name": recipient.get_full_name() or recipient.username,
                "follower_name": follower.get_full_name() or follower.username,
            },
        )

        return (notification, email_sent)

    def send_comment_reply_notification(
        self,
        recipient: User,
        event: Event,
        replier: User,
        event_url: str,
    ) -> tuple[Notification, bool]:
        """
        Send comment reply notification.

        Args:
            recipient: User whose comment was replied to
            event: Event where comment was made
            replier: User who replied
            event_url: URL to the event

        Returns:
            tuple: (notification, email_sent)
        """
        # Create in-app notification
        notification = self.notification_service.create_notification(
            recipient=recipient,
            notification_type=Notification.NotificationType.COMMENT_REPLY,
            title="New Reply",
            body=f"{replier.get_full_name()} replied to your comment on {event.title}",
            event=event,
            actor=replier,
        )

        # Send email
        email_sent = self.email_sender.send_email(
            to_email=recipient.email,
            subject="Someone Replied to Your Comment",
            template_name="comment_reply",
            context={
                "user_name": recipient.get_full_name() or recipient.username,
                "replier_name": replier.get_full_name() or replier.username,
                "event_title": event.title,
                "event_url": event_url,
            },
        )

        return (notification, email_sent)

    def send_org_invitation(
        self,
        recipient: User,
        organization: Organization,
        inviter: User,
        org_url: str,
    ) -> tuple[Notification, bool]:
        """
        Send organization invitation notification.

        Args:
            recipient: User being invited
            organization: Organization to invite to
            inviter: User sending the invitation
            org_url: URL to the organization

        Returns:
            tuple: (notification, email_sent)
        """
        # Create in-app notification
        notification = self.notification_service.create_notification(
            recipient=recipient,
            notification_type=Notification.NotificationType.ORG_INVITE,
            title=f"Invitation to join {organization.name}",
            body=f"{inviter.get_full_name()} invited you to join {organization.name}",
            organization=organization,
            actor=inviter,
        )

        # Send email
        email_sent = self.email_sender.send_email(
            to_email=recipient.email,
            subject=f"Join {organization.name}",
            template_name="org_invitation",
            context={
                "user_name": recipient.get_full_name() or recipient.username,
                "organization_name": organization.name,
                "inviter_name": inviter.get_full_name() or inviter.username,
                "org_url": org_url,
            },
        )

        return (notification, email_sent)

    # ==================== Marketing/Informative Notifications ====================

    def send_newsletter(
        self,
        recipients: List[User],
        subject: str,
        content: dict,
    ) -> int:
        """
        Send newsletter to multiple users.

        Args:
            recipients: List of users to send to
            subject: Email subject
            content: Newsletter content dictionary

        Returns:
            int: Number of emails sent successfully
        """
        emails_sent = 0
        for recipient in recipients:
            sent = self.email_sender.send_email(
                to_email=recipient.email,
                subject=subject,
                template_name="newsletter",
                context={
                    "user_name": recipient.get_full_name() or recipient.username,
                    **content,
                },
            )
            if sent:
                emails_sent += 1

        return emails_sent

    def send_announcement(
        self,
        recipients: List[User],
        subject: str,
        announcement_title: str,
        announcement_body: str,
    ) -> int:
        """
        Send announcement to multiple users.

        Args:
            recipients: List of users to send to
            subject: Email subject
            announcement_title: Announcement title
            announcement_body: Announcement body

        Returns:
            int: Number of emails sent successfully
        """
        emails_sent = 0
        for recipient in recipients:
            sent = self.email_sender.send_email(
                to_email=recipient.email,
                subject=subject,
                template_name="announcement",
                context={
                    "user_name": recipient.get_full_name() or recipient.username,
                    "announcement_title": announcement_title,
                    "announcement_body": announcement_body,
                },
            )
            if sent:
                emails_sent += 1

        return emails_sent
