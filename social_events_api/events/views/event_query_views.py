from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
from ..serializers import EventSerializer
from ..models import Event
from ..service.event_query_service import EventQueryService
from ..utils.filter import EventFilterBuilder

class EventQueryViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    event_service = EventQueryService()

    def get_object(self):
        identifier = self.kwargs.get('pk') 
        event = self.event_service.get_event_by_id_or_slug(identifier)
        return event

    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search events with various filters
        
        Query Parameters:
        - q: Search query for title, description, location, venue
        - category: Category ID
        - date_from: Start date (YYYY-MM-DD HH:MM:SS)
        - date_to: End date (YYYY-MM-DD HH:MM:SS)
        - price_min: Minimum price
        - price_max: Maximum price
        - status: Event status (draft/published/cancelled)
        - location: Location search
        - available_only: Show only available events (true/false)
        - favorites_only: Show only favorited events (true/false)
        - organizer: Organizer ID
        - order_by: Field to order by (e.g., start_date, -created_at)
        """
        filter_builder = EventFilterBuilder(request)
        events = self.event_service.search_events(
            search_query=request.query_params.get('q'),
            filters=filter_builder.get_filters(),
            user=request.user
        )

        page = self.paginate_queryset(events)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        events = self.get_serializer(events, many=True).data
        return Response(data=events, status=status.HTTP_200_OK)
