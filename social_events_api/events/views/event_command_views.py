from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import Event
from ..serializers import EventSerializer, EventCreateSerializer, RegistrationSerializer
from ..service.event_command_service import EventCommandService  
from ..service.event_validation_service import EventValidationService  

class EventCommandViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing events, including create, update, delete, and additional actions.
    """
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

    @swagger_auto_schema(
        operation_summary="Create a new event",
        operation_description="Creates a new event with the given data.",
        request_body=EventCreateSerializer,
        responses={
            201: openapi.Response("Event created successfully.", EventSerializer),
            400: "Validation error or bad request."
        }
    )
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

    @swagger_auto_schema(
        operation_summary="Update an existing event",
        operation_description="Updates an event partially or completely based on the provided data.",
        request_body=EventCreateSerializer,
        responses={
            200: openapi.Response("Event updated successfully.", EventSerializer),
            400: "Validation error or bad request.",
            404: "Event not found."
        }
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        data['id'] = instance.id
        
        validation = self.event_validation_service.validate(data=serializer.validated_data, 
                                                            is_creation=False)
        if not validation.success:
            return Response({'message': validation.error_message}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        event = self.event_command_service.update_event(instance, data, request.user)
        event = self.get_serializer(event).data
        return Response(event, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Delete an event",
        operation_description="Deletes an event permanently.",
        responses={
            204: "Event deleted successfully.",
            404: "Event not found."
        }
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.event_command_service.delete_event(instance, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_summary="Toggle favorite status for an event",
        operation_description="Marks an event as favorite or removes it from favorites for the current user.",
        responses={
            200: "Favorite status toggled successfully.",
            404: "Event not found.",
            401: "Unauthorized."
        }
    )
    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        event = self.get_object()
        message = self.event_command_service.toggle_favorite(event, request.user)
        return Response(message, status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Get registrations for an event",
        operation_description="Retrieves the list of registrations associated with the event.",
        responses={
            200: openapi.Response("Registrations retrieved successfully.", RegistrationSerializer(many=True)),
            404: "Event not found.",
        }
    )
    @action(detail=True, methods=['get'])
    def registrations(self, request, pk=None):
        event = self.get_object()
        result = self.event_command_service.get_event_registrations(event)
        registrations = RegistrationSerializer(result.data, many=True).data
        return Response(registrations, status.HTTP_200_OK)
