from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.db import transaction
from ..models import UserFollow, UserPreferences
from ..serializers import (
    UserSerializer, 
    UserPreferencesSerializer,
    UserCreateSerializer,
)
from ..utils.swagger_examples import _USER_EXAMPLE , USER_ERROR_EXAMPLES as _ERROR_EXAMPLES

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user accounts and social features
    
    Actions:
    - create: Register new user (Public)
    - retrieve: Get user details (Authenticated)
    - follow: Follow/unfollow user (Authenticated)
    - followers: List user followers (Public)
    - following: List followed users (Public)
    - me: Get/update current user profile (Authenticated)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        """Select serializer based on action"""
        return UserCreateSerializer if self.action == 'create' else UserSerializer

    def get_permissions(self):
        """Dynamically assign permissions based on action"""
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    @swagger_auto_schema(
        operation_summary="Create user",
        operation_description="Register a new user account",
        request_body=UserCreateSerializer,
        responses={
            201: openapi.Response(
                description="User created",
                schema=UserSerializer,
                examples={'application/json': _USER_EXAMPLE}
            ),
            400: openapi.Response(
                description="Validation error",
                examples={'application/json': _ERROR_EXAMPLES['VALIDATION_ERROR']}
            )
        },
        tags=['Users']
    )
    @transaction.atomic
    def create(self, request):
        """Handle user registration with preferences creation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        UserPreferences.objects.create(user=user)
        
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        operation_summary="Follow user",
        operation_description="Toggle follow status for a user",
        responses={
            200: openapi.Response(
                description="Unfollow successful",
                examples={'application/json': {'detail': 'Successfully unfollowed user'}}
            ),
            201: openapi.Response(
                description="Follow successful",
                examples={'application/json': {'detail': 'Successfully followed user'}}
            ),
            400: openapi.Response(
                description="Self-follow attempt",
                examples={'application/json': _ERROR_EXAMPLES['SELF_FOLLOW_ERROR']}
            ),
            404: openapi.Response(
                description="User not found",
                examples={'application/json': _ERROR_EXAMPLES['NOT_FOUND_ERROR']}
            )
        },
        tags=['Social']
    )
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """Handle follow/unfollow logic"""
        user_to_follow = self.get_object()
        
        if request.user == user_to_follow:
            return Response(
                _ERROR_EXAMPLES['SELF_FOLLOW_ERROR'],
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            follow, created = UserFollow.objects.get_or_create(
                follower=request.user,
                following=user_to_follow
            )

            if not created:
                follow.delete()
                return Response(
                    {'detail': 'Successfully unfollowed user'},
                    status=status.HTTP_200_OK
                )

        return Response(
            {'detail': 'Successfully followed user'},
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        operation_summary="List followers",
        operation_description="Get paginated list of user's followers",
        responses={
            200: openapi.Response(
                description="Followers list",
                schema=UserSerializer(many=True),
                examples={'application/json': [_USER_EXAMPLE]}
            )
        },
        tags=['Social']
    )
    @action(detail=True, methods=['get'])
    def followers(self, request, pk=None):
        """Retrieve paginated list of followers"""
        user = self.get_object()
        followers = user.followers.all()
        page = self.paginate_queryset(followers)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(followers, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="List following",
        operation_description="Get paginated list of users being followed",
        responses={
            200: openapi.Response(
                description="Following list",
                schema=UserSerializer(many=True),
                examples={'application/json': [_USER_EXAMPLE]}
            )
        },
        tags=['Social']
    )
    @action(detail=True, methods=['get'])
    def following(self, request, pk=None):
        """Retrieve paginated list of followed users"""
        user = self.get_object()
        following = user.following.all()
        page = self.paginate_queryset(following)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(following, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Current user profile",
        operation_description="Retrieve or update authenticated user's profile",
        methods=['get', 'patch'],
        responses={
            200: openapi.Response(
                description="User profile",
                schema=UserSerializer,
                examples={'application/json': _USER_EXAMPLE}
            ),
            400: openapi.Response(
                description="Validation error",
                examples={'application/json': _ERROR_EXAMPLES['VALIDATION_ERROR']}
            )
        },
        tags=['Users']
    )
    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """Handle current user profile operations"""
        if request.method == 'GET':
            return Response(
                self.get_serializer(request.user).data
            )

        serializer = self.get_serializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserPreferencesViewSet(mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            viewsets.GenericViewSet):
    """
    API endpoint for managing user preferences
    
    Actions:
    - retrieve: Get user preferences
    - update: Update user preferences (partial allowed)
    """
    serializer_class = UserPreferencesSerializer
    permission_classes = [IsAuthenticated]

    _PREFERENCES_EXAMPLE = {
        'theme': 'dark',
        'notifications_enabled': True,
        'language': 'en'
    }

    @swagger_auto_schema(
        operation_summary="Get preferences",
        operation_description="Retrieve current user's preferences",
        responses={
            200: openapi.Response(
                description="User preferences",
                schema=UserPreferencesSerializer,
                examples={'application/json': _PREFERENCES_EXAMPLE}
            )
        },
        tags=['Preferences']
    )
    @swagger_auto_schema(
        method='patch',
        operation_summary="Update preferences",
        operation_description="Update current user's preferences",
        request_body=UserPreferencesSerializer,
        responses={
            200: openapi.Response(
                description="Updated preferences",
                schema=UserPreferencesSerializer,
                examples={'application/json': _PREFERENCES_EXAMPLE}
            ),
            400: openapi.Response(
                description="Validation error",
                examples={'application/json': _ERROR_EXAMPLES['VALIDATION_ERROR']}
            )
        },
        tags=['Preferences']
    )
    @action(detail=False, methods=['patch'])
    def get_object(self):
        """Get or create preferences for current user"""
        preferences, _ = UserPreferences.objects.get_or_create(user=self.request.user)
        return preferences