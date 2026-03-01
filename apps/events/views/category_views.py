"""Category and Tag views."""

from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser

from apps.events.models import Category, Tag
from apps.events.serializers import CategorySerializer, TagSerializer


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
