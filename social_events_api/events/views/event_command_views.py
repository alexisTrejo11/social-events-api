from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import Event
from ..serializers import EventSerializer, EventCreateSerializer, RegistrationSerializer
from ..service.event_command_service import EventCommandService  
from ..service.event_validation_service import EventValidationService  
from ..utils.swagger_examples import _SUCCESS_MESSAGE, _EVENT_EXAMPLE, EVENT_ERROR_EXAMPLES as _ERROR_EXAMPLES

class EventCommandViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing events and related operations
    
    Actions:
    - create: Create new event (Authenticated)
    - update: Update existing event (Authenticated)
    - destroy: Delete event (Authenticated)
    - favorite: Toggle favorite status (Authenticated)
    - registrations: Get event registrations (Public)
    """
    queryset = Event.objects.all()
    event_command_service = EventCommandService()
    event_validation_service = EventValidationService()


    def get_permissions(self):
        """Dynamically assign permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'favorite']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        """Select serializer based on action type"""
        if self.action in ['create', 'update', 'partial_update']:
            return EventCreateSerializer
        return EventSerializer

    @swagger_auto_schema(
        operation_summary="Create new event",
        operation_description="Create a new event (Authenticated users only)",
        request_body=EventCreateSerializer,
        responses={
            201: openapi.Response(
                description="Event created successfully",
                schema=EventSerializer,
                examples={'application/json': _EVENT_EXAMPLE}
            ),
            400: openapi.Response(
                description="Validation error",
                examples={'application/json': _ERROR_EXAMPLES['VALIDATION_ERROR']}
            ),
            403: openapi.Response(
                description="Permission denied",
                examples={'application/json': _ERROR_EXAMPLES['PERMISSION_ERROR']}
            )
        },
        tags=['Events']
    )
    def create(self, request, *args, **kwargs):
        """Handle event creation with validation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validation = self.event_validation_service.validate(
            data=serializer.validated_data,
            is_creation=True
        )
        if not validation.success:
            return Response(
                {'detail': validation.error_message}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        event = self.event_command_service.create_event(
            serializer.validated_data, 
            request.user
        )
        return Response(
            EventSerializer(event).data,
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        operation_summary="Update event",
        operation_description="Update existing event (Authenticated owners only)",
        request_body=EventCreateSerializer,
        responses={
            200: openapi.Response(
                description="Event updated successfully",
                schema=EventSerializer,
                examples={'application/json': _EVENT_EXAMPLE}
            ),
            400: openapi.Response(
                description="Validation error",
                examples={'application/json': _ERROR_EXAMPLES['VALIDATION_ERROR']}
            ),
            403: openapi.Response(
                description="Permission denied",
                examples={'application/json': _ERROR_EXAMPLES['PERMISSION_ERROR']}
            ),
            404: openapi.Response(
                description="Not found",
                examples={'application/json': _ERROR_EXAMPLES['NOT_FOUND_ERROR']}
            )
        },
        tags=['Events']
    )
    def update(self, request, *args, **kwargs):
        """Handle event updates with validation"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        validated_data['id'] = instance.id
        
        validation = self.event_validation_service.validate(
            data=validated_data, 
            is_creation=False
        )
        if not validation.success:
            return Response(
                {'detail': validation.error_message}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event = self.event_command_service.update_event(
            instance, 
            validated_data, 
            request.user
        )
        return Response(
            self.get_serializer(event).data,
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Delete event",
        operation_description="Permanently delete an event (Authenticated owners only)",
        responses={
            204: openapi.Response(description="Event deleted successfully"),
            403: openapi.Response(
                description="Permission denied",
                examples={'application/json': _ERROR_EXAMPLES['PERMISSION_ERROR']}
            ),
            404: openapi.Response(
                description="Not found",
                examples={'application/json': _ERROR_EXAMPLES['NOT_FOUND_ERROR']}
            )
        },
        tags=['Events']
    )
    def destroy(self, request, *args, **kwargs):
        """Handle event deletion"""
        instance = self.get_object()
        self.event_command_service.delete_event(instance, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_summary="Toggle favorite status",
        operation_description="Add/remove event from user favorites",
        manual_parameters=[
            openapi.Parameter(
                'id', openapi.IN_PATH,
                description="Event ID",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: openapi.Response(
                description="Favorite status updated",
                examples={'application/json': _SUCCESS_MESSAGE}
            ),
            400: openapi.Response(
                description="Processing error",
                examples={'application/json': _ERROR_EXAMPLES['FAVORITE_ERROR']}
            ),
            404: openapi.Response(
                description="Not found",
                examples={'application/json': _ERROR_EXAMPLES['NOT_FOUND_ERROR']}
            )
        },
        tags=['Events']
    )
    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        """Handle favorite toggle functionality"""
        event = self.get_object()
        message = self.event_command_service.toggle_favorite(event, request.user)
        return Response(
            {'detail': message},
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Get event registrations",
        operation_description="Retrieve all registrations for specified event",
        manual_parameters=[
            openapi.Parameter(
                'id', openapi.IN_PATH,
                description="Event ID",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: openapi.Response(
                description="Registrations retrieved",
                schema=RegistrationSerializer(many=True),
                examples={'application/json': [{
                    'id': 1,
                    'user': 'username',
                    'status': 'confirmed'
                }]}
            ),
            404: openapi.Response(
                description="Not found",
                examples={'application/json': _ERROR_EXAMPLES['NOT_FOUND_ERROR']}
            )
        },
        tags=['Events']
    )
    @action(detail=True, methods=['get'])
    def registrations(self, request, pk=None):
        """Retrieve event registrations"""
        event = self.get_object()
        registrations = self.event_command_service.get_event_registrations(event)
        return Response(
            RegistrationSerializer(registrations, many=True).data,
            status=status.HTTP_200_OK
        )