from django.utils import timezone
from ..models import Event
from typing import Any, Dict, Optional
from ..utils.result import Result
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q, QuerySet
from ..models import User
from rest_framework.exceptions import NotFound


class EventQueryService:
    def get_event_by_id_or_slug(self, identifier: str) -> Event:
        event = None
        if identifier.isdigit():
            event = Event.objects.filter(id=identifier).first()
        else:
            event = Event.objects.filter(slug=identifier).first()

        if not event:
            raise NotFound(detail="Event not found")
        
        return event
    
    # Not working
    def search_events(
        self,
        search_query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        user = None
    ) -> QuerySet:
            queryset = Event.objects.all()
            # Base filters for public events or private events if user is authenticated
            base_filters = Q(is_private=False)
            if user and user.is_authenticated:
                base_filters |= Q(organizer=user)
            
            queryset = queryset.filter(base_filters)

            # Apply search query if provided
            if search_query:
                search_filters = Q(title__icontains=search_query) | \
                               Q(description__icontains=search_query) | \
                               Q(location__icontains=search_query) | \
                               Q(venue__icontains=search_query)
                queryset = queryset.filter(search_filters)

            # Apply additional filters
            if filters:
                # Category filter
                if category_id := filters.get('category'):
                    queryset = queryset.filter(category_id=category_id)

                # Date range filter
                if date_from := filters.get('date_from'):
                    queryset = queryset.filter(start_date__gte=date_from)
                if date_to := filters.get('date_to'):
                    queryset = queryset.filter(end_date__lte=date_to)

                # Price range filter
                if price_min := filters.get('price_min'):
                    queryset = queryset.filter(price__gte=price_min)
                if price_max := filters.get('price_max'):
                    queryset = queryset.filter(price__lte=price_max)

                # Status filter
                if status := filters.get('status'):
                    queryset = queryset.filter(status=status)

                # Location filter
                if location := filters.get('location'):
                    queryset = queryset.filter(location__icontains=location)

                # Availability filter
                if filters.get('available_only'):
                    queryset = queryset.filter(
                        capacity__gt=0,
                        start_date__gt=timezone.now(),
                        status='published'
                    )

                # Favorites filter
                if filters.get('favorites_only') and user and user.is_authenticated:
                    queryset = queryset.filter(favorites=user)

                # Organizer filter
                if organizer_id := filters.get('organizer'):
                    queryset = queryset.filter(organizer_id=organizer_id)

            # Apply ordering
            order_by = filters.get('order_by', '-start_date') if filters else '-start_date'
            queryset = queryset.order_by(order_by)

            return queryset

            
       
   