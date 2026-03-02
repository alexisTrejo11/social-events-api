"""Filters for location queryset filtering."""

from django_filters import rest_framework as filters
from apps.locations.models import Location


class LocationFilter(filters.FilterSet):
    """
    Filter set for Location queryset.

    Supports filtering by:
    - city (partial match)
    - country (partial match)
    - state_province (partial match)
    - postal_code (exact match)
    - is_virtual (true/false)
    - has_coordinates (true/false - filter by presence of lat/lng)
    - search (searches in name, city, country, and address)
    """

    city = filters.CharFilter(field_name="city", lookup_expr="icontains")
    country = filters.CharFilter(field_name="country", lookup_expr="icontains")
    state_province = filters.CharFilter(
        field_name="state_province", lookup_expr="icontains"
    )
    postal_code = filters.CharFilter(field_name="postal_code", lookup_expr="exact")
    has_coordinates = filters.BooleanFilter(method="filter_has_coordinates")
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Location
        fields = [
            "city",
            "country",
            "state_province",
            "postal_code",
            "is_virtual",
            "has_coordinates",
            "search",
        ]

    def filter_has_coordinates(self, queryset, name, value):
        """
        Filter locations by presence of coordinates.
        True: locations with both latitude and longitude
        False: locations without coordinates
        """
        if value is True:
            return queryset.filter(latitude__isnull=False, longitude__isnull=False)
        elif value is False:
            return queryset.filter(latitude__isnull=True) | queryset.filter(
                longitude__isnull=True
            )
        return queryset

    def filter_search(self, queryset, name, value):
        """
        Search locations by name, city, country, or address.
        Case-insensitive partial match.
        """
        if not value:
            return queryset

        from django.db.models import Q

        return queryset.filter(
            Q(name__icontains=value)
            | Q(city__icontains=value)
            | Q(country__icontains=value)
            | Q(address_line_1__icontains=value)
            | Q(address_line_2__icontains=value)
        ).distinct()
