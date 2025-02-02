from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from ..models import Registration
from ..serializers import RegistrationSerializer, RegistrationCreateSerializer
from ..service.registration_service import RegistrationService
from ..utils.swagger_examples import _REGISTRATION_EXAMPLE, REGISTRATION_ERROR_EXAMPLES as _ERROR_EXAMPLES


class RegistrationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing event registrations
    
    Actions:
    - create: Register for an event (Authenticated)
    - cancel: Cancel registration (Authenticated)
    - confirm: Confirm registration (Authenticated)
    - list_user_registrations: Get user's registrations (Authenticated)
    - retrieve: Get registration details (Public)
    """
    queryset = Registration.objects.all()
    registration_service = RegistrationService()

    def get_serializer_class(self):
        """Select serializer based on action type"""
        if self.action == 'create':
            return RegistrationCreateSerializer
        return RegistrationSerializer

    def get_permissions(self):
        """Dynamically assign permissions based on action"""
        if self.action in ['create', 'cancel', 'confirm', 'list_user_registrations']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @swagger_auto_schema(
        operation_summary="Create registration",
        operation_description="Register for an event (Authenticated users only)",
        request_body=RegistrationCreateSerializer,
        responses={
            201: openapi.Response(
                description="Registration created",
                schema=RegistrationSerializer,
                examples={'application/json': _REGISTRATION_EXAMPLE}
            ),
            400: openapi.Response(
                description="Validation error",
                examples={'application/json': _ERROR_EXAMPLES['VALIDATION_ERROR']}
            ),
            403: openapi.Response(
                description="Permission error",
                examples={'application/json': _ERROR_EXAMPLES['PERMISSION_ERROR']}
            ),
            409: openapi.Response(
                description="Conflict error",
                examples={'application/json': _ERROR_EXAMPLES['CONFLICT_ERROR']}
            )
        },
        tags=['Registrations']
    )
    def create(self, request, *args, **kwargs):
        """Handle registration creation with validation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['attendee'] = request.user
        
        validation = self.registration_service.validate_creation(serializer.validated_data)
        if not validation.success:
            return Response(
                {'detail': validation.error_message}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        registration = self.registration_service.create(serializer.validated_data)
        return Response(
            RegistrationSerializer(registration).data,
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        method="post",
        operation_summary="Cancel registration",
        operation_description="Cancel existing registration (Authenticated user only)",
        responses={
            200: openapi.Response(
                description="Registration cancelled",
                examples={'application/json': {'detail': 'Registration cancelled successfully'}}
            ),
            403: openapi.Response(
                description="Permission error",
                examples={'application/json': _ERROR_EXAMPLES['PERMISSION_ERROR']}
            ),
            404: openapi.Response(
                description="Not found",
                examples={'application/json': _ERROR_EXAMPLES['NOT_FOUND_ERROR']}
            )
        },
        tags=['Registrations']
    )
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """Handle registration cancellation"""
        registration = self.get_object()
        self.registration_service.validate_authority(registration, request.user)
        self.registration_service.cancel(registration)
        return Response(
            {"detail": "Registration cancelled successfully"},
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        method="post",
        operation_summary="Confirm registration",
        operation_description="Confirm a pending registration (Authorized users only)",
        responses={
            200: openapi.Response(
                description="Registration confirmed",
                examples={'application/json': {'detail': 'Registration confirmed successfully'}}
            ),
            403: openapi.Response(
                description="Permission error",
                examples={'application/json': _ERROR_EXAMPLES['PERMISSION_ERROR']}
            ),
            404: openapi.Response(
                description="Not found",
                examples={'application/json': _ERROR_EXAMPLES['NOT_FOUND_ERROR']}
            )
        },
        tags=['Registrations']
    )
    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        """Handle registration confirmation"""
        registration = self.get_object()
        self.registration_service.validate_authority(registration, request.user)
        self.registration_service.confirm(registration)
        return Response(
            {"detail": "Registration confirmed successfully"},
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        method="get",
        operation_summary="List user registrations",
        operation_description="Get all registrations for current user",
        responses={
            200: openapi.Response(
                description="User registrations",
                schema=RegistrationSerializer(many=True),
                examples={'application/json': [_REGISTRATION_EXAMPLE]}
            )
        },
        tags=['Registrations']
    )
    @action(detail=False, methods=['get'], url_path='my-registrations')
    def list_user_registrations(self, request):
        """Retrieve current user's registrations"""
        registrations = self.registration_service.get_user_registrations(request.user)
        return Response(
            RegistrationSerializer(registrations, many=True).data,
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_summary="Get registration details",
        operation_description="Retrieve detailed information about a specific registration",
        responses={
            200: openapi.Response(
                description="Registration details",
                schema=RegistrationSerializer,
                examples={'application/json': _REGISTRATION_EXAMPLE}
            ),
            404: openapi.Response(
                description="Not found",
                examples={'application/json': _ERROR_EXAMPLES['NOT_FOUND_ERROR']}
            )
        },
        tags=['Registrations']
    )
    def retrieve(self, request, *args, **kwargs):
        """Get registration details"""
        instance = self.get_object()
        return Response(
            RegistrationSerializer(instance).data,
            status=status.HTTP_200_OK
        )