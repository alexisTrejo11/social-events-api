from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.response import Response

from ..serializers import UserCreateSerializer, LoginSerializer
from ..service.user_service import UserService
from ..service.auth_service import AuthService
from ..utils.swagger_examples import _TOKEN_EXAMPLE, _AUTH_ERROR_EXAMPLES as _ERROR_EXAMPLES

User = get_user_model()

class AuthView(viewsets.ViewSet):
    """
    ViewSet to manage authentication operations:
    - Register new users
    - Login
    - Logout
    """
    permission_classes = (AllowAny,)
    user_service = UserService()
    auth_service = AuthService()

    @swagger_auto_schema(
        operation_description="User registration",
        request_body=UserCreateSerializer,
        responses={
            201: openapi.Response(
                description="User successfully registered",
                examples={'application/json': _TOKEN_EXAMPLE}
            ),
            400: openapi.Response(
                description="Validation error",
                examples={'application/json': _ERROR_EXAMPLES['VALIDATION_ERROR']}
            ),
            403: openapi.Response(
                description="Data conflict",
                examples={'application/json': _ERROR_EXAMPLES['CONFLICT_ERROR']}
            )
        },
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='signup')
    def signup(self, request):
        """Endpoint for new user registration"""
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validation = self.user_service.validate(serializer.validated_data)
        if not validation.success:
            return Response(
                {'detail': validation.error_message},
                status=status.HTTP_403_FORBIDDEN
            )

        user = User.objects.create_user(**serializer.validated_data)
        return Response(
            {'tokens': self._get_tokens_for_user(user)},
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        operation_description="User login",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Successful login",
                examples={'application/json': _TOKEN_EXAMPLE}
            ),
            400: openapi.Response(
                description="Authentication error",
                examples={'application/json': _ERROR_EXAMPLES['AUTH_ERROR']}
            )
        },
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """Endpoint for user authentication"""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validation = self.auth_service.validate_login(serializer.validated_data)
        if not validation.success:
            return Response(
                {'detail': validation.error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
           
        tokens = self.auth_service.get_tokens_for_user(validation.data)
        return Response(
            {'tokens': tokens}
        )

    @swagger_auto_schema(
        operation_description="User logout",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description="Refresh token to invalidate"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Successful logout",
                examples={'application/json': {'detail': 'Successfully logged out.'}}
            ),
            400: openapi.Response(
                description="Invalid token",
                examples={'application/json': _ERROR_EXAMPLES['TOKEN_ERROR']}
            )
        },
        tags=['Authentication']
    )
    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        """Endpoint to invalidate refresh tokens"""
        try:
            refresh_token = request.data.get("refresh")
            self.auth_service.blacklist_token(refresh_token)
            return Response(
                {"detail": "Successfully logged out."},
                status=status.HTTP_200_OK
            )
        except (TokenError, AttributeError, KeyError):
            return Response(
                {"detail": "Invalid token."},
                status=status.HTTP_400_BAD_REQUEST
            )
