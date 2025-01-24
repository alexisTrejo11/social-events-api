from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from ..models import Registration
from ..serializers import RegistrationSerializer, RegistrationCreateSerializer
from ..service.registration_service import RegistrationService

class RegistrationViewSet(viewsets.ModelViewSet):
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


    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        registration = get_object_or_404(Registration, pk=pk)
        self.registration_service.validate_authority(registration, request.user)
        
        self.registration_service.cancel(registration)

        return Response(
            {"success": "Inscripción succesfully cancel."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        registration = get_object_or_404(Registration, pk=pk)
        self.registration_service.validate_authority(registration, request.user)

        self.registration_service.confirm(registration)

        return Response(
            {"success": "Inscripción succesfully confirmed."},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='my-registrations')
    def list_user_registrations(self, request):
        user = request.user
        registrations = Registration.objects.filter(attendee=user)
        serializer = self.get_serializer(registrations, many=True)
        return Response(serializer.data)


    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
