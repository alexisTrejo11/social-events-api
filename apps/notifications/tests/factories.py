import factory

from apps.notifications.models import Notification
from apps.users.tests.factories import UserFactory


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    recipient = factory.SubFactory(UserFactory, email_verified=True)
    notification_type = Notification.NotificationType.REMINDER
    title = "Test notification"
    body = "Something happened"
    is_read = False
