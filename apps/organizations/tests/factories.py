import factory

from apps.organizations.models import Organization, OrganizationMembership
from apps.users.tests.factories import UserFactory


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Org {n}")
    description = "A test organization"
    created_by = factory.SubFactory(UserFactory)


class OrganizationMembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganizationMembership

    organization = factory.SubFactory(OrganizationFactory)
    user = factory.SubFactory(UserFactory)
    role = OrganizationMembership.Role.OWNER
