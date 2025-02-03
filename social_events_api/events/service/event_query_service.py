from django.utils import timezone
from ..models import Event
from typing import Any, Dict, Optional
from ..utils.result import Result
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q, QuerySet
from ..models import User
from rest_framework.exceptions import NotFound
from ..utils.filter import EventQueryBuilder


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
    

    def search_events(
        self,
        search_query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        user = None
    ) -> QuerySet:
        return (
            EventQueryBuilder(Event.objects.all())
            .apply_base_filters(user)
            .apply_search(search_query)
            .apply_filters(filters, user)
            .build()
        )