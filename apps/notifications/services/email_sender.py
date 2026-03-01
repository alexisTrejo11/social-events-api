"""Email sender service with HTML template support."""

from typing import Optional, List, Dict, Any
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


class EmailSender:
    """
    Centralized email sending service with HTML template support.
    Provides elegant, pre-designed email templates for various purposes.
    """

    # Email template contexts
    TEMPLATE_BASE = "emails/base.html"

    # Template paths
    TEMPLATES = {
        # Authentication emails
        "welcome": "emails/auth/welcome.html",
        "verify_email": "emails/auth/verify_email.html",
        "password_reset": "emails/auth/password_reset.html",
        "password_changed": "emails/auth/password_changed.html",
        # Event emails
        "event_invitation": "emails/events/invitation.html",
        "event_reminder": "emails/events/reminder.html",
        "event_update": "emails/events/update.html",
        "event_cancelled": "emails/events/cancelled.html",
        # Registration emails
        "registration_confirmed": "emails/registrations/confirmed.html",
        "registration_pending": "emails/registrations/pending.html",
        "registration_waitlisted": "emails/registrations/waitlisted.html",
        "registration_cancelled": "emails/registrations/cancelled.html",
        "check_in_confirmation": "emails/registrations/check_in.html",
        # User action emails
        "new_follower": "emails/users/new_follower.html",
        "comment_reply": "emails/users/comment_reply.html",
        "org_invitation": "emails/users/org_invitation.html",
        # Marketing/Informative emails
        "newsletter": "emails/marketing/newsletter.html",
        "announcement": "emails/marketing/announcement.html",
    }

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """
        Send an HTML email using a template.

        Args:
            to_email: Recipient email address
            subject: Email subject
            template_name: Name of the template (key from TEMPLATES dict)
            context: Template context dictionary
            from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
            cc: List of CC recipients
            bcc: List of BCC recipients

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Get template path
            template_path = EmailSender.TEMPLATES.get(template_name)
            if not template_path:
                raise ValueError(f"Template '{template_name}' not found")

            # Add default context
            context = EmailSender._add_default_context(context)

            # Render HTML content
            html_content = render_to_string(template_path, context)

            # Create plain text version
            text_content = strip_tags(html_content)

            # Use default from_email if not provided
            if not from_email:
                from_email = getattr(
                    settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"
                )

            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[to_email],
                cc=cc or [],
                bcc=bcc or [],
            )

            # Attach HTML version
            email.attach_alternative(html_content, "text/html")

            # Send email
            email.send()
            return True

        except Exception as e:
            # Log error (in production, use proper logging)
            print(f"Error sending email to {to_email}: {str(e)}")
            return False

    @staticmethod
    def send_bulk_email(
        recipients: List[str],
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None,
    ) -> int:
        """
        Send the same email to multiple recipients.

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            template_name: Name of the template
            context: Template context dictionary
            from_email: Sender email

        Returns:
            int: Number of successfully sent emails
        """
        sent_count = 0
        for recipient in recipients:
            if EmailSender.send_email(
                recipient, subject, template_name, context, from_email
            ):
                sent_count += 1
        return sent_count

    @staticmethod
    def _add_default_context(context: Dict[str, Any]) -> Dict[str, Any]:
        """Add default context variables to all emails."""
        default_context = {
            "site_name": getattr(settings, "SITE_NAME", "Social Events"),
            "site_url": getattr(settings, "SITE_URL", "http://localhost:8000"),
            "support_email": getattr(settings, "SUPPORT_EMAIL", "support@example.com"),
            "current_year": "2026",
        }
        return {**default_context, **context}

    # Convenience methods for common emails

    @staticmethod
    def send_welcome_email(user_email: str, user_name: str) -> bool:
        """Send welcome email to new user."""
        return EmailSender.send_email(
            to_email=user_email,
            subject="Welcome to Social Events!",
            template_name="welcome",
            context={
                "user_name": user_name,
            },
        )

    @staticmethod
    def send_verification_email(
        user_email: str, user_name: str, verification_url: str
    ) -> bool:
        """Send email verification link."""
        return EmailSender.send_email(
            to_email=user_email,
            subject="Verify Your Email Address",
            template_name="verify_email",
            context={
                "user_name": user_name,
                "verification_url": verification_url,
            },
        )

    @staticmethod
    def send_password_reset_email(
        user_email: str, user_name: str, reset_url: str
    ) -> bool:
        """Send password reset link."""
        return EmailSender.send_email(
            to_email=user_email,
            subject="Reset Your Password",
            template_name="password_reset",
            context={
                "user_name": user_name,
                "reset_url": reset_url,
            },
        )

    @staticmethod
    def send_password_changed_email(user_email: str, user_name: str) -> bool:
        """Send password change confirmation."""
        return EmailSender.send_email(
            to_email=user_email,
            subject="Your Password Was Changed",
            template_name="password_changed",
            context={
                "user_name": user_name,
            },
        )

    @staticmethod
    def send_event_invitation(
        user_email: str,
        user_name: str,
        event_title: str,
        event_url: str,
        inviter_name: str,
    ) -> bool:
        """Send event invitation email."""
        return EmailSender.send_email(
            to_email=user_email,
            subject=f"You're Invited: {event_title}",
            template_name="event_invitation",
            context={
                "user_name": user_name,
                "event_title": event_title,
                "event_url": event_url,
                "inviter_name": inviter_name,
            },
        )

    @staticmethod
    def send_event_reminder(
        user_email: str,
        user_name: str,
        event_title: str,
        event_date: str,
        event_url: str,
    ) -> bool:
        """Send event reminder email."""
        return EmailSender.send_email(
            to_email=user_email,
            subject=f"Reminder: {event_title}",
            template_name="event_reminder",
            context={
                "user_name": user_name,
                "event_title": event_title,
                "event_date": event_date,
                "event_url": event_url,
            },
        )

    @staticmethod
    def send_registration_confirmed(
        user_email: str,
        user_name: str,
        event_title: str,
        event_date: str,
        event_url: str,
    ) -> bool:
        """Send registration confirmation email."""
        return EmailSender.send_email(
            to_email=user_email,
            subject=f"Registration Confirmed: {event_title}",
            template_name="registration_confirmed",
            context={
                "user_name": user_name,
                "event_title": event_title,
                "event_date": event_date,
                "event_url": event_url,
            },
        )
