from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.response import Response

from ..serializers import UserCreateSerializer, LoginSerializer
from ..service.user_service import UserService
from ..service.auth_service import AuthService

User = get_user_model()

class AuthView(viewsets.ViewSet):
    permission_classes = (AllowAny,)
    user_service = UserService()
    auth_service = AuthService()

    @swagger_auto_schema(
        operation_description="User Registration Endpoint",
        request_body=UserCreateSerializer,
        responses={
            201: openapi.Response(
                description="User registered successfully",
                examples={
                    'application/json': {
                        'tokens': {
                            'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                            'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Validation failed",
                examples={
                    'application/json': {'message': 'Invalid registration data'}
                }
            )
        },
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='signup')
    def signup(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validation = self.user_service.validate(serializer.validated_data)
        if not validation.success:
            return Response(
                {'message': validation.error_message}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(**serializer.validated_data)

        refresh = RefreshToken.for_user(user)
        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        return Response({'tokens': tokens}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="User Login Endpoint",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="User logged in successfully",
                examples={
                    'application/json': {
                        'tokens': {
                            'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                            'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="Authentication failed",
                examples={
                    'application/json': {'message': 'Invalid credentials'}
                }
            )
        },
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validation = self.auth_service.validate_login(serializer.validated_data)
        if not validation.success:
            return Response(
                {'message': validation.error_message}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        user = validation.data
        refresh = RefreshToken.for_user(user)

        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }

        return Response({'tokens': tokens})

    @swagger_auto_schema(
        operation_description="User Logout Endpoint",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token to invalidate")
            }
        ),
        responses={
            200: openapi.Response(
                description="Successfully logged out",
                examples={
                    'application/json': {'detail': 'Successfully logged out.'}
                }
            ),
            400: openapi.Response(
                description="Invalid token",
                examples={
                    'application/json': {'detail': 'Invalid token.'}
                }
            )
        },
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()  
            return Response(
                {"detail": "Successfully logged out."}, 
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"detail": "Invalid token."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
