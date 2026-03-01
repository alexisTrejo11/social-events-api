import logging
from django.contrib.auth import get_user_model
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    """
    POST /auth/register/
    Register a new user account
    """

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

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


class LoginView(generics.GenericAPIView):
    """
    POST /auth/login/
    Login and receive JWT tokens
    """

    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

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
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            logger.info(f"User logged out: {request.user.email}")

            return Response(
                {"message": "Logged out successfully"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )


class VerifyEmailView(generics.GenericAPIView):
    """
    POST /auth/verify-email/
    Verify email with token
    """

    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]

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


class ResendVerificationView(generics.GenericAPIView):
    """
    POST /auth/resend-verification/
    Resend verification email
    """

    permission_classes = [IsAuthenticated]

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

        return Response(
            {"message": "Verification email sent"}, status=status.HTTP_200_OK
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

        return Response(
            {"message": "Password changed successfully"}, status=status.HTTP_200_OK
        )


class PasswordResetRequestView(generics.GenericAPIView):
    """
    POST /auth/password/reset/
    Request password reset email
    """

    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

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


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    POST /auth/password/reset/confirm/
    Confirm password reset with token
    """

    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Reset password"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: Reset password
        # user = User.objects.get(id=serializer.validated_data['user_id'])
        # user.set_password(serializer.validated_data['new_password'])
        # user.save()

        logger.info("Password reset placeholder")

        return Response(
            {"message": "Password reset successfully"}, status=status.HTTP_200_OK
        )
