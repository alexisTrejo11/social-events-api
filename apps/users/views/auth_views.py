import logging
from django.contrib.auth import get_user_model
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from apps.users.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer,
)
from common.serializers import (
    ErrorResponseSerializer,
    MessageResponseSerializer,
    ValidationErrorSerializer,
)
from common.throttling import AuthActionsThrottle

User = get_user_model()
logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Authentication"],
    summary="Register a new user account",
    description="Create a new user account with email verification. "
    "Password must meet strength requirements (8+ chars, uppercase, lowercase, digit, special char).",
    request=UserRegistrationSerializer,
    responses={
        201: UserRegistrationSerializer,
        400: ValidationErrorSerializer,
    },
)
class RegisterView(generics.CreateAPIView):
    """
    POST /auth/register/
    Register a new user account
    """

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AuthActionsThrottle]

    def create(self, request, *args, **kwargs):
        """Create user and return user data"""
        logger.info(f"Registration attempt for email: {request.data.get('email')}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "message": "User registered successfully. Please check your email to verify your account.",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Authentication"],
    summary="Login and receive JWT tokens",
    description="Authenticate with email and password to receive JWT access and refresh tokens.",
    request=UserLoginSerializer,
    responses={
        200: UserLoginSerializer,
        400: ValidationErrorSerializer,
        401: ErrorResponseSerializer,
    },
)
class LoginView(generics.GenericAPIView):
    """
    POST /auth/login/
    Login and receive JWT tokens
    """

    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AuthActionsThrottle]
    throttle_classes = [AuthActionsThrottle]

    def post(self, request, *args, **kwargs):
        """Authenticate and return tokens"""
        logger.info(f"Login attempt for email: {request.data.get('email')}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        logger.info(f"User logged in: {serializer.validated_data['user'].email}")

        return Response(
            {"tokens": serializer.data["tokens"], "user": serializer.data["user"]},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Authentication"],
    summary="Logout and blacklist refresh token",
    description="Invalidate the refresh token to log the user out.",
    responses={
        200: MessageResponseSerializer,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
    },
)
class LogoutView(generics.GenericAPIView):
    """
    POST /auth/logout/
    Logout and blacklist refresh token
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Blacklist refresh token"""
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                error_data = {"error": "Refresh token is required"}
                return Response(
                    ErrorResponseSerializer(error_data).data,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            logger.info(f"User logged out: {request.user.email}")

            return Response(
                MessageResponseSerializer({"message": "Logged out successfully"}).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            error_data = {"error": "Invalid token"}
            return Response(
                ErrorResponseSerializer(error_data).data,
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(
    tags=["Authentication"],
    summary="Verify email with token",
    description="Verify a user's email address using a token sent to their email.",
    request=EmailVerificationSerializer,
    responses={
        200: MessageResponseSerializer,
        400: ValidationErrorSerializer,
        401: ErrorResponseSerializer,
    },
)
class VerifyEmailView(generics.GenericAPIView):
    """
    POST /auth/verify-email/
    Verify email with token
    """

    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AuthActionsThrottle]

    def post(self, request, *args, **kwargs):
        """Verify email"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: Decode token and verify user
        # user_id = decoded_token['user_id']
        # user = User.objects.get(id=user_id)
        # user.email_verified = True
        # user.save()

        logger.info("Email verification placeholder")

        return Response(
            {"message": "Email verified successfully"}, status=status.HTTP_200_OK
        )


@extend_schema(
    tags=["Authentication"],
    summary="Resend email verification",
    description="Resend the email verification link to the user's email address.",
    responses={
        204: None,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
    },
)
class ResendVerificationView(generics.GenericAPIView):
    """
    POST /auth/resend-verification/
    Resend verification email
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [AuthActionsThrottle]

    def post(self, request, *args, **kwargs):
        """Resend verification email"""
        user = request.user

        if user.email_verified:
            return Response(
                {"message": "Email is already verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"Resending verification email to: {user.email}")

        # TODO: Send verification email
        # from apps.users.tasks import send_verification_email
        # send_verification_email.delay(user.id)

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Authentication"],
    summary="Change password",
    description="Change the password for the authenticated user. Requires current password and new password.",
    request=PasswordChangeSerializer,
    responses={
        204: None,
        400: ValidationErrorSerializer,
        401: ErrorResponseSerializer,
    },
)
class PasswordChangeView(generics.GenericAPIView):
    """
    POST /auth/password/change/
    Change password for authenticated user
    """

    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Change password"""
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Authentication"],
    summary="Request password reset",
    description="Request a password reset email to be sent to the user's email address.",
    request=PasswordResetRequestSerializer,
    responses={
        200: MessageResponseSerializer,
        400: ValidationErrorSerializer,
        401: ErrorResponseSerializer,
    },
)
class PasswordResetRequestView(generics.GenericAPIView):
    """
    POST /auth/password/reset/
    Request password reset email
    """

    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AuthActionsThrottle]

    def post(self, request, *args, **kwargs):
        """Send password reset email"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "If an account exists with this email, a password reset link has been sent."
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Authentication"],
    summary="Confirm password reset",
    description="Confirm the password reset using the token sent to the user's email.",
    request=PasswordResetConfirmSerializer,
    responses={
        200: None,
        400: ValidationErrorSerializer,
        401: ErrorResponseSerializer,
    },
)
class PasswordResetConfirmView(generics.GenericAPIView):
    """
    POST /auth/password/reset/confirm/
    Confirm password reset with token
    """

    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AuthActionsThrottle]

    def post(self, request, *args, **kwargs):
        """Reset password"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: Reset password
        # user = User.objects.get(id=serializer.validated_data['user_id'])
        # user.set_password(serializer.validated_data['new_password'])
        # user.save()

        logger.info("Password reset placeholder")

        return Response(status=status.HTTP_204_NO_CONTENT)
