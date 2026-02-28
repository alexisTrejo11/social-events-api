import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.text import slugify

from apps.locations.models import Location
from apps.organizations.models import Organization
from common.utils import unique_slug


# ---------------------------------------------------------------------------
# Category & Tag
# ---------------------------------------------------------------------------


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # e.g. CSS icon class or emoji
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_categories",
    )

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    """
    Flexible free-form tags for discovery and filtering.
    Separate from Category (structured) to allow user-generated folksonomy.
    """

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Recurrence
# ---------------------------------------------------------------------------


class RecurrenceRule(models.Model):
    """
    Stores recurrence configuration for repeating events.
    Inspired by iCalendar RRULE, kept as structured fields
    instead of raw RRULE strings for easier querying.
    """

    class Frequency(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        BIWEEKLY = "biweekly", "Bi-weekly"
        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"

    frequency = models.CharField(max_length=10, choices=Frequency.choices)
    interval = models.PositiveSmallIntegerField(
        default=1, help_text="Repeat every N frequency units (e.g. every 2 weeks)."
    )
    # Days of week as comma-separated values: "MO,WE,FR"
    by_weekday = models.CharField(max_length=20, blank=True)
    by_month_day = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Day of month (1–31) for monthly recurrence."
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Recurrence ends on this date. Null means indefinite.",
    )
    max_occurrences = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Stop after N occurrences. Takes precedence over end_date.",
    )

    def __str__(self) -> str:
        return f"{self.frequency} (every {self.interval})"


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    class EventType(models.TextChoices):
        IN_PERSON = "in_person", "In Person"
        ONLINE = "online", "Online"
        HYBRID = "hybrid", "Hybrid"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    cover_image = models.ImageField(
        upload_to="event_covers/%Y/%m/", blank=True, null=True
    )

    # Ownership — event belongs to a user OR an organization, not both
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_events",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        help_text="Set if this event is hosted on behalf of an organization.",
    )

    # Classification
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="events"
    )
    tags = models.ManyToManyField(Tag, related_name="events", blank=True)
    event_type = models.CharField(
        max_length=10, choices=EventType.choices, default=EventType.IN_PERSON
    )

    # Schedule
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    timezone = models.CharField(max_length=50, default="UTC")

    # Recurrence
    recurrence = models.OneToOneField(
        RecurrenceRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event",
    )
    # For recurrence: link child occurrences back to their parent template
    parent_event = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="occurrences",
    )

    # Location
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    # Capacity & visibility
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        null=True,
        blank=True,
        help_text="Null means unlimited capacity.",
    )
    is_private = models.BooleanField(default=False)
    requires_approval = models.BooleanField(
        default=False,
        help_text="If True, registrations start as pending until manually approved.",
    )

    # Status
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )

    # Engagement
    favorites = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="favorite_events", blank=True
    )

    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["start_date", "status"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["organization", "status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title, Event)
        super().save(*args, **kwargs)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def __str__(self) -> str:
        return self.title


class EventRole(models.Model):
    """
    Granular per-event roles. Separate from Registration
    to distinguish attendees from staff/volunteers/hosts.
    """

    class Role(models.TextChoices):
        HOST = "host", "Host"
        CO_HOST = "co_host", "Co-host"
        SPEAKER = "speaker", "Speaker"
        VOLUNTEER = "volunteer", "Volunteer"
        MODERATOR = "moderator", "Moderator"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="roles")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="event_roles"
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    bio_override = models.TextField(
        blank=True,
        help_text="Event-specific bio shown on the event page (e.g. speaker intro).",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assigned_event_roles",
    )

    class Meta:
        unique_together = ["event", "user", "role"]

    def __str__(self) -> str:
        return f"{self.user.get_full_name()} — {self.role} @ {self.event.title}"
