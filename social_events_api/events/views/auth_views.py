from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status

from rest_framework.decorators import action
from ..serializers import UserCreateSerializer, LoginSerializer
from ..service.user_service import UserService 
from ..service.auth_service import AuthService 
from ..utils.result import Result

User = get_user_model()

class AuthView(viewsets.ModelViewSet):  
    permission_classes = (AllowAny,)
    user_service = UserService()
    auth_service = AuthService()

    def get_serializer_class(self):
        if self.action == 'signup':
            return UserCreateSerializer
        return LoginSerializer
    
    @action(detail=False, methods=['post'], url_path='signup')  
    def signup(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validation = self.user_service.validate(serializer.validated_data)
        if not validation.success:
            return Response({'message': validation.error_message}, 
                            status=status.HTTP_400_BAD_REQUEST)
 
        user = User.objects.create_user(**serializer.validated_data)

        refresh = RefreshToken.for_user(user)
        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        return Response({'tokens': tokens}, status=status.HTTP_201_CREATED)


    @action(detail=False, methods=['post'], url_path='login')  
    def login(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validation = self.auth_service.validate_login(serializer.validated_data)
        if not validation.success:
            return Response({'message': validation.error_message}, 
                            status=status.HTTP_400_BAD_REQUEST)

        user = validation.data
        refresh = RefreshToken.for_user(user)

        tokens = {'refresh': str(refresh),
                  'access': str(refresh.access_token)}

        return Response({'tokens': tokens})


    @action(detail=False, methods=['post'], url_path='logout')  
    def logout(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()  
            return Response({"detail": "Successfully logged out."}, 
                            status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "Invalid token."}, 
                            status=status.HTTP_400_BAD_REQUEST)
