"""Notification URLs."""

from django.urls import path
from apps.notifications import views

app_name = "notifications"

urlpatterns = [
    # List and detail
    path("", views.NotificationListView.as_view(), name="notification-list"),
    path(
        "<int:pk>/", views.NotificationDetailView.as_view(), name="notification-detail"
    ),
    # Actions
    path(
        "<int:notification_id>/read/",
        views.mark_notification_as_read,
        name="mark-as-read",
    ),
    path("mark-all-read/", views.mark_all_as_read, name="mark-all-read"),
    # Delete
    path(
        "<int:notification_id>/delete/",
        views.delete_notification,
        name="delete-notification",
    ),
    path("clear-read/", views.delete_all_read_notifications, name="clear-read"),
    # Stats
    path("stats/", views.notification_stats, name="notification-stats"),
]
