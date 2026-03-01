"""
Events views module.

This module imports and re-exports views from the views package.
This allows backward compatibility for imports like:
    from apps.events.views import EventViewSet
"""

from apps.events.views.event_views import EventViewSet
from apps.events.views.category_views import CategoryViewSet, TagViewSet
from apps.events.views.user_event_views import UserFavoriteEventsView

__all__ = [
    "EventViewSet",
    "CategoryViewSet",
    "TagViewSet",
    "UserFavoriteEventsView",
]
