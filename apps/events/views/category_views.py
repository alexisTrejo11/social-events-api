"""Category and Tag views."""

from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from drf_spectacular.utils import extend_schema_view, extend_schema

from apps.events.models import Category, Tag
from apps.events.serializers import CategorySerializer, TagSerializer
from common.serializers import ErrorResponseSerializer
from common.throttling import SearchThrottle


@extend_schema_view(
    list=extend_schema(
        tags=["Events"],
        summary="List all event categories",
        description="Get a list of all available event categories. Categories are managed by administrators.",
        responses={
            200: CategorySerializer(many=True),
        },
    ),
    retrieve=extend_schema(
        tags=["Events"],
        summary="Get category details",
        description="Retrieve detailed information for a specific event category by slug.",
        responses={
            200: CategorySerializer,
            404: ErrorResponseSerializer,
        },
    ),
)
class CategoryViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    ViewSet for event categories (read-only for regular users).

    List: GET /categories/ - List all categories
    Retrieve: GET /categories/{slug}/ - Get category details

    Note: Categories are managed via Django admin by staff.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    permission_classes = [IsAuthenticatedOrReadOnly]
    throttle_classes = [SearchThrottle]


@extend_schema_view(
    list=extend_schema(
        tags=["Events"],
        summary="List all event tags",
        description="Get a list of all available event tags. Tags are created automatically when events are created or managed via admin.",
        responses={
            200: TagSerializer(many=True),
        },
    ),
    retrieve=extend_schema(
        tags=["Events"],
        summary="Get tag details",
        description="Retrieve detailed information for a specific event tag by slug.",
        responses={
            200: TagSerializer,
            404: ErrorResponseSerializer,
        },
    ),
)
class TagViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    ViewSet for event tags (read-only).

    List: GET /tags/ - List all tags
    Retrieve: GET /tags/{slug}/ - Get tag details

    Note: Tags are typically created automatically when events are created.
    They can also be managed via Django admin.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = "slug"
    permission_classes = [IsAuthenticatedOrReadOnly]
    throttle_classes = [SearchThrottle]
