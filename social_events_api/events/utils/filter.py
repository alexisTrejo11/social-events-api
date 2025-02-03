from typing import Dict, Any
from django.utils.dateparse import parse_datetime
from django.db.models import Q, QuerySet
from django.utils import timezone

class EventFilterBuilder:
    def __init__(self, request=None):
        self.filters = {}
        if request:
            self.build_from_request(request)

    def build_from_request(self, request) -> None:
        """Construye los filtros a partir de los parámetros de la request"""
        self._parse_date_filters(request)
        self._parse_numeric_filters(request)
        self._parse_boolean_filters(request)
        self._parse_basic_filters(request)
        
    def _parse_date_filters(self, request) -> None:
        if date_from := request.query_params.get('date_from'):
            self.filters['date_from'] = parse_datetime(date_from)
        if date_to := request.query_params.get('date_to'):
            self.filters['date_to'] = parse_datetime(date_to)

    def _parse_numeric_filters(self, request) -> None:
        if price_min := request.query_params.get('price_min'):
            self.filters['price_min'] = float(price_min)
        if price_max := request.query_params.get('price_max'):
            self.filters['price_max'] = float(price_max)

    def _parse_boolean_filters(self, request) -> None:
        if available_only := request.query_params.get('available_only'):
            self.filters['available_only'] = available_only.lower() == 'true'
        if favorites_only := request.query_params.get('favorites_only'):
            self.filters['favorites_only'] = favorites_only.lower() == 'true'

    def _parse_basic_filters(self, request) -> None:
        for param in ['category', 'status', 'location', 'organizer', 'order_by']:
            if value := request.query_params.get(param):
                self.filters[param] = value

    def get_filters(self) -> Dict[str, Any]:
        return self.filters


class EventQueryBuilder:
    def __init__(self, queryset: QuerySet):
        self.queryset = queryset

    def apply_base_filters(self, user=None) -> 'EventQueryBuilder':
        base_filters = Q(is_private=False)
        if user and user.is_authenticated:
            base_filters |= Q(organizer=user)
        self.queryset = self.queryset.filter(base_filters)
        return self

    def apply_search(self, search_query: str) -> 'EventQueryBuilder':
        if search_query:
            search_filters = Q(title__icontains=search_query) | \
                           Q(description__icontains=search_query) | \
                           Q(location__icontains=search_query) | \
                           Q(venue__icontains=search_query)
            self.queryset = self.queryset.filter(search_filters)
        return self

    def apply_filters(self, filters: Dict[str, Any], user=None) -> 'EventQueryBuilder':
        if not filters:
            return self

        self._apply_basic_filters(filters)
        self._apply_availability_filter(filters)
        self._apply_favorites_filter(filters, user)
        self._apply_ordering(filters)
        return self

    def _apply_basic_filters(self, filters: Dict[str, Any]) -> None:
        filter_mappings = {
            'category': 'category_id',
            'date_from': 'start_date__gte',
            'date_to': 'end_date__lte',
            'price_min': 'price__gte',
            'price_max': 'price__lte',
            'status': 'status',
            'location': 'location__icontains',
            'organizer': 'organizer_id'
        }

        for filter_key, query_key in filter_mappings.items():
            if value := filters.get(filter_key):
                self.queryset = self.queryset.filter(**{query_key: value})

    def _apply_availability_filter(self, filters: Dict[str, Any]) -> None:
        if filters.get('available_only'):
            self.queryset = self.queryset.filter(
                capacity__gt=0,
                start_date__gt=timezone.now(),
                status='published'
            )

    def _apply_favorites_filter(self, filters: Dict[str, Any], user) -> None:
        if filters.get('favorites_only') and user and user.is_authenticated:
            self.queryset = self.queryset.filter(favorites=user)

    def _apply_ordering(self, filters: Dict[str, Any]) -> None:
        order_by = filters.get('order_by', '-start_date')
        self.queryset = self.queryset.order_by(order_by)

    def build(self) -> QuerySet:
        return self.queryset