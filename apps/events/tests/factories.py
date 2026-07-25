from datetime import timedelta

import factory
from django.utils import timezone

from apps.events.models import Event
from apps.users.tests.factories import UserFactory


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    title = factory.Sequence(lambda n: f"Event {n}")
    description = "A test event"
    organizer = factory.SubFactory(UserFactory, email_verified=True)
    start_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    end_date = factory.LazyFunction(
        lambda: timezone.now() + timedelta(days=7, hours=2)
    )
    status = Event.Status.DRAFT
