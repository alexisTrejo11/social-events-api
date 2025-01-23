from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
from ..serializers import EventSerializer
from ..models import Event
from ..service.event_query_service import EventQueryService

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

        filters = self.__fetch_filters(request)
       
        events = self.event_service.search_events(
            search_query=request.query_params.get('q'),
            filters=filters,
            user=request.user
        )

        page = self.paginate_queryset(events)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        events = self.get_serializer(events, many=True).data
        return Response(data=events, status=status.HTTP_200_OK)
    
    
    def __fetch_filters(self, request) -> dict:
        # Extract search parameters
        filters = {}
        
        # Parse date filters
        if date_from := request.query_params.get('date_from'):
            filters['date_from'] = parse_datetime(date_from)
        if date_to := request.query_params.get('date_to'):
            filters['date_to'] = parse_datetime(date_to)

        # Parse numeric filters
        if price_min := request.query_params.get('price_min'):
            filters['price_min'] = float(price_min)
        if price_max := request.query_params.get('price_max'):
            filters['price_max'] = float(price_max)

        # Parse boolean filters
        if available_only := request.query_params.get('available_only'):
            filters['available_only'] = available_only.lower() == 'true'
        if favorites_only := request.query_params.get('favorites_only'):
            filters['favorites_only'] = favorites_only.lower() == 'true'

        # Other filters
        for param in ['category', 'status', 'location', 'organizer', 'order_by']:
            if value := request.query_params.get(param):
                filters[param] = value

        return filters