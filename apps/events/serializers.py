"""
Events serializers module.

This module imports and re-exports serializers from the serializers package.
This allows backward compatibility for imports like:
    from apps.events.serializers import EventListSerializer
"""

from apps.events.serializers.event_serializers import (
    EventListSerializer,
    EventDetailSerializer,
    EventCreateUpdateSerializer,
    EventPublishSerializer,
    EventCancelSerializer,
    RecurrenceRuleSerializer,
)
from apps.events.serializers.category_serializers import (
    CategorySerializer,
    TagSerializer,
)
from apps.events.serializers.role_serializers import (
    EventRoleSerializer,
    EventRoleCreateSerializer,
    EventRoleUpdateSerializer,
)

__all__ = [
    # Event serializers
    "EventListSerializer",
    "EventDetailSerializer",
    "EventCreateUpdateSerializer",
    "EventPublishSerializer",
    "EventCancelSerializer",
    "RecurrenceRuleSerializer",
    # Category serializers
    "CategorySerializer",
    "TagSerializer",
    # Role serializers
    "EventRoleSerializer",
    "EventRoleCreateSerializer",
    "EventRoleUpdateSerializer",
]
