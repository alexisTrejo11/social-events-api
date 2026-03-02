import logging
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.users.models import UserFollow
from apps.users.serializers import (
    UserFollowSerializer,
    UserFollowerSerializer,
)
from common.serializers import (
    ErrorResponseSerializer,
    MessageResponseSerializer,
)
from common.throttling import ReadHeavyThrottle, WriteStandardThrottle

User = get_user_model()
logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Users"],
    summary="List user's followers",
    description="Get a list of all users following the specified user.",
    responses={
        200: UserFollowerSerializer(many=True),
        404: ErrorResponseSerializer,
    },
)
class UserFollowersView(generics.ListAPIView):
    """
    GET /users/{username}/followers/
    Get list of user's followers
    """

    serializer_class = UserFollowerSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ReadHeavyThrottle]

    def get_queryset(self):
        """Get followers for the specified user"""
        username = self.kwargs.get("username")
        user = get_object_or_404(User, username=username, is_active=True)
        logger.info(f"Fetching followers for: {username}")
        return UserFollow.objects.filter(following=user).select_related("follower")


@extend_schema(
    tags=["Users"],
    summary="List users being followed",
    description="Get a list of all users that the specified user is following.",
    responses={
        200: UserFollowSerializer(many=True),
        404: ErrorResponseSerializer,
    },
)
class UserFollowingView(generics.ListAPIView):
    """
    GET /users/{username}/following/
    Get list of users that this user follows
    """

    serializer_class = UserFollowSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ReadHeavyThrottle]

    def get_queryset(self):
        """Get following for the specified user"""
        username = self.kwargs.get("username")
        user = get_object_or_404(User, username=username, is_active=True)
        logger.info(f"Fetching following for: {username}")
        return UserFollow.objects.filter(follower=user).select_related("following")


@extend_schema(
    tags=["Users"],
    summary="Follow a user",
    description="Follow another user. Cannot follow yourself or follow the same user twice.",
    responses={
        200: MessageResponseSerializer,
        201: MessageResponseSerializer,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
class FollowUserView(generics.GenericAPIView):
    """
    POST /users/{username}/follow/
    Follow a user
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [WriteStandardThrottle]

    def post(self, request, username=None):
        """Follow user"""
        user_to_follow = get_object_or_404(User, username=username, is_active=True)

        if user_to_follow == request.user:
            error_data = {"error": "You cannot follow yourself"}
            return Response(
                ErrorResponseSerializer(error_data).data,
                status=status.HTTP_400_BAD_REQUEST,
            )

        follow, created = UserFollow.objects.get_or_create(
            follower=request.user, following=user_to_follow
        )

        if created:
            logger.info(
                f"{request.user.email} started following {user_to_follow.username}"
            )

            # TODO: Send notification to followed user
            # from apps.notifications.tasks import create_notification
            # create_notification.delay(
            #     user_id=user_to_follow.id,
            #     notification_type='new_follower',
            #     actor_id=request.user.id
            # )

            return Response(
                MessageResponseSerializer(
                    {"message": f"You are now following {user_to_follow.username}"}
                ).data,
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                MessageResponseSerializer(
                    {"message": f"You are already following {user_to_follow.username}"}
                ).data,
                status=status.HTTP_200_OK,
            )


@extend_schema(
    tags=["Users"],
    summary="Unfollow a user",
    description="Stop following a user. Returns an error if not currently following the user.",
    responses={
        200: MessageResponseSerializer,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
class UnfollowUserView(generics.GenericAPIView):
    """
    DELETE /users/{username}/follow/
    Unfollow a user
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [WriteStandardThrottle]

    def delete(self, request, username=None):
        """Unfollow user"""
        user_to_unfollow = get_object_or_404(User, username=username, is_active=True)

        try:
            follow = UserFollow.objects.get(
                follower=request.user, following=user_to_unfollow
            )
            follow.delete()

            logger.info(f"{request.user.email} unfollowed {user_to_unfollow.username}")

            return Response(
                MessageResponseSerializer(
                    {"message": f"You have unfollowed {user_to_unfollow.username}"}
                ).data,
                status=status.HTTP_200_OK,
            )
        except UserFollow.DoesNotExist:
            error_data = {"error": f"You are not following {user_to_unfollow.username}"}
            return Response(
                ErrorResponseSerializer(error_data).data,
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema(
    tags=["Users"],
    summary="Get personalized event feed",
    description="Get a personalized feed of events from followed users and organizations the user belongs to. Limited to 50 most recent events.",
    responses={
        200: None,  # Custom response structure
        401: ErrorResponseSerializer,
    },
)
class UserFeedView(generics.GenericAPIView):
    """
    GET /users/me/feed/
    Get events from followed users and organizations
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [ReadHeavyThrottle]

    def get(self, request):
        """Get personalized feed"""
        user = request.user

        # Get users that current user follows
        following_users = user.following.values_list("id", flat=True)

        # Get organizations that current user follows
        # (members of organizations they belong to)
        user_orgs = user.organizations.values_list("id", flat=True)

        logger.info(f"Fetching feed for user: {user.email}")

        # Get events from followed users and organizations
        from apps.events.models import Event

        feed_events = (
            Event.objects.filter(
                Q(organizer_id__in=following_users) | Q(organization_id__in=user_orgs),
                status="published",
                is_deleted=False,
            )
            .select_related("organizer", "organization", "location", "category")
            .order_by("-created_at")[:50]
        )

        # Return simplified event data
        events_data = [
            {
                "id": str(event.id),
                "title": event.title,
                "slug": event.slug,
                "description": (
                    event.description[:200] + "..."
                    if len(event.description) > 200
                    else event.description
                ),
                "event_type": event.event_type,
                "start_date": event.start_date,
                "end_date": event.end_date,
                "organizer": event.organizer.get_full_name(),
                "organization": event.organization.name if event.organization else None,
                "location": event.location.name if event.location else None,
                "category": event.category.name if event.category else None,
            }
            for event in feed_events
        ]

        return Response(
            {"count": len(events_data), "events": events_data},
            status=status.HTTP_200_OK,
        )
