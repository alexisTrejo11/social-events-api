from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from ..models import Registration
from ..serializers import RegistrationSerializer, RegistrationCreateSerializer
from ..service.registration_service import RegistrationService


class RegistrationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing event registrations, including creation, retrieval, 
    cancellation, and confirmation of registrations, as well as listing user-specific registrations.
    """
    queryset = Registration.objects.all()
    registration_service = RegistrationService()

    def get_serializer_class(self):
        if self.action == 'create':
            return RegistrationCreateSerializer
        return RegistrationSerializer

    def get_permissions(self):
        if self.action in ['create', 'cancel', 'list_user_registrations']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @swagger_auto_schema(
        operation_summary="Create a new registration",
        operation_description=(
            "Create a new registration for an event. "
            "The authenticated user is automatically set as the attendee."
        ),
        request_body=RegistrationCreateSerializer,
        responses={
            201: RegistrationSerializer,
            400: "Bad Request: Validation failed."
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['attendee'] = request.user
        
        validation = self.registration_service.validate_creation(serializer.validated_data)
        if not validation.success:
            return Response(data=validation.error_message, 
                            status=status.HTTP_400_BAD_REQUEST)

        registration = self.registration_service.create(serializer.validated_data)
        
        registration = RegistrationSerializer(registration).data
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        method="post",
        operation_summary="Cancel a registration",
        operation_description=(
            "Cancel a specific registration by its ID. "
            "Only the attendee or an authorized user can cancel the registration."
        ),
        responses={
            200: openapi.Response("Registration successfully cancelled."),
            404: "Not Found: Registration not found.",
            403: "Forbidden: User does not have permission to cancel this registration."
        }
    )
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        registration = get_object_or_404(Registration, pk=pk)
        self.registration_service.validate_authority(registration, request.user)
        
        self.registration_service.cancel(registration)

        return Response(
            {"success": "Registration successfully cancelled."},
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        method="post",
        operation_summary="Confirm a registration",
        operation_description=(
            "Confirm a specific registration by its ID. "
            "Only an authorized user can confirm the registration."
        ),
        responses={
            200: openapi.Response("Registration successfully confirmed."),
            404: "Not Found: Registration not found.",
            403: "Forbidden: User does not have permission to confirm this registration."
        }
    )
    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        registration = get_object_or_404(Registration, pk=pk)
        self.registration_service.validate_authority(registration, request.user)

        self.registration_service.confirm(registration)

        return Response(
            {"success": "Registration successfully confirmed."},
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        method="get",
        operation_summary="List user registrations",
        operation_description=(
            "Retrieve all registrations associated with the currently authenticated user."
        ),
        responses={
            200: RegistrationSerializer(many=True),
        }
    )
    @action(detail=False, methods=['get'], url_path='my-registrations')
    def list_user_registrations(self, request):
        user = request.user
        registrations = Registration.objects.filter(attendee=user)
        serializer = self.get_serializer(registrations, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Retrieve a registration",
        operation_description="Retrieve details of a specific registration by its ID.",
        responses={
            200: RegistrationSerializer,
            404: "Not Found: Registration not found."
        }
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
