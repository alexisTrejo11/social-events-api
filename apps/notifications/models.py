from django.db import models
from django.conf import settings
from django.utils import timezone

from apps.events.models import Event
from apps.organizations.models import Organization


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        EVENT_INVITE = "event_invite", "Event Invitation"
        EVENT_UPDATE = "event_update", "Event Updated"
        EVENT_CANCELLED = "event_cancelled", "Event Cancelled"
        REGISTRATION_CONFIRMED = "reg_confirmed", "Registration Confirmed"
        REGISTRATION_PENDING = "reg_pending", "Registration Pending"
        NEW_FOLLOWER = "new_follower", "New Follower"
        ORG_INVITE = "org_invite", "Organization Invitation"
        COMMENT_REPLY = "comment_reply", "Reply to Comment"
        REMINDER = "reminder", "Event Reminder"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(
        max_length=20, choices=NotificationType.choices
    )
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Generic FK alternative: direct FK fields are simpler and more queryable
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_notifications",
        help_text="The user who triggered this notification.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
        ]

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    def __str__(self) -> str:
        return f"[{self.notification_type}] → {self.recipient.email}"
