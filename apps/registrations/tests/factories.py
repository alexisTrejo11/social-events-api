import factory

from apps.events.tests.factories import EventFactory
from apps.registrations.models import Registration
from apps.users.tests.factories import UserFactory


class RegistrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Registration

    event = factory.SubFactory(EventFactory, status="published")
    attendee = factory.SubFactory(UserFactory, email_verified=True)
    status = Registration.Status.CONFIRMED
