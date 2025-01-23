from django.utils import timezone
from ..models import Event
from typing import Any, Dict, Optional
from ..utils.result import Result
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q, QuerySet
from ..models import User

class EventCommandService:
    def create_event(self, validated_data, user):
        validated_data['organizer'] = user
        return Event.objects.create(**validated_data)

    def check_user_permission(self, event, user):
        if event.organizer != user:
            raise DjangoValidationError("You do not have permission to edit or delete this event.")

    def update_event(self, event: Event, data: Dict[str, Any], user: User) -> Result[Event]:
        self.check_user_permission(event, user)
             
        for key, value in data.items():
            setattr(event, key, value)
        event.save()

        return event
    
    def delete_event(self, event: Event, user: User) -> Result:
            self.check_user_permission(event, user)
            
            event.delete()

    def toggle_favorite(self, event: Event, user: User) -> Result:
        if event.favorites.filter(id=user.id).exists():
            event.favorites.remove(user)
            return "Event removed from favorites"
        else:
            event.favorites.add(user)
            return "Event added to favorites"


    def get_event_registrations(self, event: Event) -> Result:
            return event.registrations.all()
            