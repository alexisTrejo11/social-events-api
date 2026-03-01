"""Events app URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.events.views import (
    EventViewSet,
    CategoryViewSet,
    TagViewSet,
    UserFavoriteEventsView,
)

app_name = "events"

# Router for viewsets
router = DefaultRouter()
router.register(r"events", EventViewSet, basename="event")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"tags", TagViewSet, basename="tag")

urlpatterns = [
    # Router URLs
    path("", include(router.urls)),
    # User-specific event endpoints
    path(
        "users/me/favorite-events/",
        UserFavoriteEventsView.as_view(),
        name="user-favorite-events",
    ),
]
