import factory

from apps.comments.models import Comment
from apps.events.tests.factories import EventFactory
from apps.users.tests.factories import UserFactory


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    event = factory.SubFactory(EventFactory, status="published")
    author = factory.SubFactory(UserFactory, email_verified=True)
    content = "Nice event!"
