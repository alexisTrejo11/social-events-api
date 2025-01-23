# views.py
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from ..models import Event
from ..serializers import EventSerializer, EventCreateSerializer
from ..service.event_command_service import EventCommandService  
from ..service.event_validation_service import EventValidationService  

class EventCommandViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    event_command_service = EventCommandService()
    event_validation_service = EventValidationService()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]


    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return EventCreateSerializer
        return EventSerializer


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validation = self.event_validation_service.validate(data=serializer.validated_data,
                                                            is_creation=True)
        if not validation.success:
            return Response({'message': validation.error_message}, 
                            status=status.HTTP_400_BAD_REQUEST)
 
        event = self.event_command_service.create_event(serializer.validated_data, request.user)

        event = EventSerializer(event).data
        return Response(event, status=status.HTTP_201_CREATED)


    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # ID is required to validate any slug changes
        data = serializer.validated_data
        data['id'] =  instance.id
        
        validation = self.event_validation_service.validate(data=serializer.validated_data, 
                                                            is_creation=False)
        if not validation.success:
                return Response({'message': validation.error_message}, 
                                status=status.HTTP_400_BAD_REQUEST)
        
        event = self.event_command_service.update_event(instance, data, request.user)
         
        event = self.get_serializer(event).data
        return Response(event, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        self.event_command_service.delete_event(instance, request.user)
        
        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        event = self.get_object()
        messge = self.event_command_service.toggle_favorite(event, request.user)
        return Response(messge, status.HTTP_200_OK)


    @action(detail=True, methods=['get'])
    def registrations(self, request, pk=None):
        event = self.get_object()

        self.event_command_service.get_event_registrations(event)

        registrations = RegistrationSerializer(result.data, many=True).data
        return Response(registrations, status.HTTP_200_OK)