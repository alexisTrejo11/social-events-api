import factory

from apps.locations.models import Location


class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Location

    name = factory.Sequence(lambda n: f"Venue {n}")
    address_line_1 = "123 Main St"
    city = "San Francisco"
    country = "US"
