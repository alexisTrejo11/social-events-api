from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from ..serializers import EventSerializer, EventCreateSerializer
from ..models import Event

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EventCreateSerializer
        return EventSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True) 
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if user is the organizer
        if instance.organizer != request.user:
            return Response(
                {"detail": "You do not have permission to edit this event."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if user is the organizer
        if instance.organizer != request.user:
            return Response(
                {"detail": "You do not have permission to delete this event."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        event = self.get_object()
        user = request.user
        
        if event.favorites.filter(id=user.id).exists():
            event.favorites.remove(user)
            return Response({'status': 'removed from favorites'})
        else:
            event.favorites.add(user)
            return Response({'status': 'added to favorites'})

    @action(detail=True, methods=['get'])
    def registrations(self, request, pk=None):
        """Get all registrations for an event"""
        event = self.get_object()
        registrations = event.registrations.all()
        from ..serializers import RegistrationSerializer  # Import here to avoid circular imports
        serializer = RegistrationSerializer(registrations, many=True)
        return Response(serializer.data)