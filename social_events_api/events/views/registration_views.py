from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from ..models import Registration
from django.utils import timezone
from ..serializers import RegistrationSerializer, RegistrationCreateSerializer

class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = Registration.objects.all()

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
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        registration = get_object_or_404(Registration, pk=pk)

        if registration.attendee != request.user:
            return Response(
                {"detail": "Not allowed to make this action"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Undo Cancel
        if registration.status == 'cancelled':
            registration.status = 'pending'
            registration.cancelled_date = None
            registration.save()

            return Response(
                {"success": "Cancel succesfully undo"},
                status=status.HTTP_200_OK
            )
        # Normal Cancel
        else:   
            registration.status = 'cancelled'
            registration.cancelled_date = timezone.now()
            registration.save()

            return Response(
                {"success": "Inscripción succesfully cancel."},
                status=status.HTTP_200_OK
            )

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        registration = get_object_or_404(Registration, pk=pk)

        if registration.attendee != request.user:
            return Response(
                {"detail": "Not allowed to make this action"},
                status=status.HTTP_403_FORBIDDEN
            )

        if registration.status == 'confirmed' or registration.status == 'cancelled':
            return Response(
                {"detail": "Only pending registrations can be confirmed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        registration.status = 'confirmed'
        registration.save()

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
