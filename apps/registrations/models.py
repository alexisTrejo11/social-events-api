import uuid
from django.db import models
from django.conf import settings

from apps.events.models import Event


# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------


class TicketTier(models.Model):
    """
    Defines ticket types for an event (free, paid, VIP, employee-only, etc.).
    An event can have multiple tiers.
    """

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        INVITE_ONLY = "invite_only", "Invite Only"
        ORG_MEMBERS = "org_members", "Organization Members Only"

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="ticket_tiers"
    )
    name = models.CharField(max_length=100)  # e.g. "General Admission", "VIP"
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default="USD")
    capacity = models.PositiveIntegerField(
        null=True, blank=True, help_text="Null means shares the event's total capacity."
    )
    visibility = models.CharField(
        max_length=12, choices=Visibility.choices, default=Visibility.PUBLIC
    )
    sale_start = models.DateTimeField(null=True, blank=True)
    sale_end = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["price"]

    def __str__(self) -> str:
        return f"{self.name} — {self.event.title}"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class Registration(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending Approval"
        CONFIRMED = "confirmed", "Confirmed"
        WAITLISTED = "waitlisted", "Waitlisted"
        CANCELLED = "cancelled", "Cancelled"
        ATTENDED = "attended", "Attended"  # checked-in post-event

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="registrations"
    )
    attendee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="registrations"
    )
    ticket_tier = models.ForeignKey(
        TicketTier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registrations",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    notes = models.TextField(blank=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cancelled_registrations",
    )

    class Meta:
        unique_together = ["event", "attendee"]
        ordering = ["-registered_at"]

    def __str__(self) -> str:
        return f"{self.attendee.get_full_name()} → {self.event.title} [{self.status}]"
