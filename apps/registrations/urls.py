"""Registrations app URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.registrations.views import (
    TicketTierViewSet,
    EventRegistrationsListView,
    register_for_event,
    cancel_registration,
    UserRegistrationsListView,
    update_registration_status,
    check_in_attendee,
)

app_name = "registrations"

# Router for ticket tiers (nested under events)
ticket_tier_router = DefaultRouter()
ticket_tier_router.register(
    r"ticket-tiers",
    TicketTierViewSet,
    basename="ticket-tier",
)

urlpatterns = [
    # Ticket Tiers (nested under events)
    path(
        "events/<slug:event_slug>/",
        include(ticket_tier_router.urls),
    ),
    # Event Registrations
    path(
        "events/<slug:event_slug>/registrations/",
        EventRegistrationsListView.as_view(),
        name="event-registrations",
    ),
    path(
        "events/<slug:event_slug>/register/",
        register_for_event,
        name="register-for-event",
    ),
    path(
        "events/<slug:event_slug>/register/",
        cancel_registration,
        name="cancel-registration",
    ),
    path(
        "events/<slug:event_slug>/registrations/<uuid:registration_id>/",
        update_registration_status,
        name="update-registration-status",
    ),
    path(
        "events/<slug:event_slug>/registrations/<uuid:registration_id>/check-in/",
        check_in_attendee,
        name="check-in-attendee",
    ),
    # User Registrations
    path(
        "users/me/registrations/",
        UserRegistrationsListView.as_view(),
        name="user-registrations",
    ),
]
