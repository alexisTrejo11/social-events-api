"""
Celery tasks for user-related operations.
These are placeholders to be implemented with actual Celery configuration.
"""

import logging
from celery import shared_task
from apps.notifications.services.notification_factory import NotificationFactory

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="users.send_verification_email")
def send_verification_email(user):
    """
    Send email verification link to user.

    Args:
        user: User instance
    """
    logger.info(f"Sending verification email to user {user.id}")
    factory = NotificationFactory()
    # TODO: Implement dummy verification URL generation
    factory.send_email_verification(user=user, verification_url="dummy-url")
    pass


# TODO: Implement with Celery
@shared_task(bind=True, name="users.send_password_reset_email")
def send_password_reset_email(user):
    """
    Send password reset link to user.

    Args:
        user: User instance
    """
    logger.info(f"Sending password reset email to user {user.id}")

    factory = NotificationFactory()
    # TODO: Implement dummy verification URL generation
    factory.send_password_reset(user=user, reset_url="dummy-url")


@shared_task(bind=True, name="users.send_welcome_email")
def send_welcome_email(user):
    """
    Send welcome email to newly registered user.

    Args:
        user: User instance
    """
    logger.info(f"Sending welcome email to user {user.id}")
    factory = NotificationFactory()
    factory.send_welcome_notification(user=user, welcome_url="dummy-url")
    pass


def send_password_changed_notification(user):
    """
    Send notification that password was changed.

    Args:
        user: User instance
    """
    logger.info(f" Sending password changed notification to user {user.id}")
    factory = NotificationFactory()
    factory.send_password_changed(user=user)
