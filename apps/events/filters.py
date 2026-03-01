"""Filters for event queryset filtering."""

from django_filters import rest_framework as filters
from apps.events.models import Event


class EventFilter(filters.FilterSet):
    """
    Filter set for Event queryset.

    Supports filtering by:
    - category (slug)
    - tags (slug, can specify multiple)
    - event_type (in_person, online, hybrid)
    - city (partial match on location city)
    - start_after (events starting after this date)
    - start_before (events starting before this date)
    - organization (slug)
    - status (draft, published, cancelled, completed)
    - is_private (true/false)
    - search (searches in title and description)
    """

    category = filters.CharFilter(field_name="category__slug", lookup_expr="iexact")
    tags = filters.CharFilter(method="filter_tags")
    city = filters.CharFilter(field_name="location__city", lookup_expr="icontains")
    start_after = filters.DateTimeFilter(field_name="start_date", lookup_expr="gte")
    start_before = filters.DateTimeFilter(field_name="start_date", lookup_expr="lte")
    organization = filters.CharFilter(
        field_name="organization__slug", lookup_expr="iexact"
    )
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Event
        fields = [
            "category",
            "tags",
            "event_type",
            "city",
            "start_after",
            "start_before",
            "organization",
            "status",
            "is_private",
            "search",
        ]

    def filter_tags(self, queryset, name, value):
        """
        Filter events by tag slugs.
        Supports comma-separated values for multiple tags.
        """
        if not value:
            return queryset

        tag_slugs = [slug.strip() for slug in value.split(",")]
        return queryset.filter(tags__slug__in=tag_slugs).distinct()

    def filter_search(self, queryset, name, value):
        """
        Search events by title or description.
        Case-insensitive partial match.
        """
        if not value:
            return queryset

        from django.db.models import Q

        return queryset.filter(
            Q(title__icontains=value) | Q(description__icontains=value)
        ).distinct()
