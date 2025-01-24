from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from ..models import UserFollow, UserPreferences
from ..serializers import (
    UserSerializer, 
    UserPreferencesSerializer,
    UserCreateSerializer,
)

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """
    Viewset for viewing, creating, and managing user accounts.
    Allows users to view their profile, follow other users, and update their information.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    @swagger_auto_schema(
        operation_description="Create a new user account.",
        request_body=UserCreateSerializer,
        responses={201: UserSerializer, 400: 'Bad Request'}
    )
    def create(self, request):
        """
        Create a new user and associated user preferences.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            UserPreferences.objects.create(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Follow or unfollow a user.",
        responses={200: 'User unfollowed', 201: 'User followed', 400: 'Error'}
    )
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """
        Follow or unfollow a user.
        """
        user_to_follow = self.get_object()
        if request.user == user_to_follow:
            return Response(
                {'error': 'You cannot follow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        follow, created = UserFollow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )

        if not created:
            follow.delete()
            return Response(
                {'status': 'User unfollowed'},
                status=status.HTTP_200_OK
            )

        return Response(
            {'status': 'User followed'},
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        operation_description="List followers of a user.",
        responses={200: UserSerializer}
    )
    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        """
        Get a list of followers for a specific user.
        """
        user = self.get_object()
        followers = user.followers.all()
        serializer = UserSerializer(followers, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="List users the current user is following.",
        responses={200: UserSerializer}
    )
    @action(detail=True, methods=['get'])
    def following(self, request, pk=None):
        """
        Get a list of users that the current user is following.
        """
        user = self.get_object()
        following = user.following.all()
        serializer = UserSerializer(following, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get or update the current user's profile.",
        responses={200: UserSerializer, 400: 'Bad Request'},
        methods=['get'] 
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get or update the authenticated user's profile.
        """
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)

        serializer = self.get_serializer(
            request.user, 
            data=request.data, 
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserPreferencesView(generics.RetrieveUpdateAPIView):
    """
    View for retrieving or updating the current user's preferences.
    """
    serializer_class = UserPreferencesSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve or update user preferences.",
        responses={200: UserPreferencesSerializer, 400: 'Bad Request'}
    )
    def get_object(self):
        """
        Get or create preferences for the current user.
        """
        preferences, created = UserPreferences.objects.get_or_create(
            user=self.request.user
        )
        return preferences
