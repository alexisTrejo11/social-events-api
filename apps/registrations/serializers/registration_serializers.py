"""Registration serializers."""

from rest_framework import serializers
from django.utils import timezone

from apps.registrations.models import Registration, TicketTier
from apps.users.serializers import PublicUserProfileSerializer
from .ticket_serializers import TicketTierSerializer


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for viewing registrations."""

    attendee = PublicUserProfileSerializer(read_only=True)
    ticket_tier = TicketTierSerializer(read_only=True)
    event_title = serializers.CharField(source="event.title", read_only=True)
    event_slug = serializers.CharField(source="event.slug", read_only=True)

    class Meta:
        model = Registration
        fields = [
            "id",
            "event_title",
            "event_slug",
            "attendee",
            "ticket_tier",
            "status",
            "notes",
            "checked_in_at",
            "registered_at",
            "cancelled_at",
        ]


class RegistrationCreateSerializer(serializers.Serializer):
    """Serializer for creating a registration."""

    ticket_tier_id = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_ticket_tier_id(self, value):
        """Validate that ticket tier exists and belongs to the event."""
        if value is None:
            return value

        event = self.context.get("event")
        try:
            tier = TicketTier.objects.get(id=value, event=event)
        except TicketTier.DoesNotExist:
            raise serializers.ValidationError(
                "Ticket tier not found or does not belong to this event."
            )

        # Check if tier is active
        if not tier.is_active:
            raise serializers.ValidationError("This ticket tier is not active.")

        # Check sale window
        now = timezone.now()
        if tier.sale_start and now < tier.sale_start:
            raise serializers.ValidationError("This ticket tier is not yet on sale.")
        if tier.sale_end and now > tier.sale_end:
            raise serializers.ValidationError("This ticket tier sale has ended.")

        # Check capacity
        if tier.capacity is not None:
            confirmed = tier.registrations.filter(status="confirmed").count()
            if confirmed >= tier.capacity:
                raise serializers.ValidationError("This ticket tier is sold out.")

        return value

    def validate(self, attrs):
        """Validate registration."""
        event = self.context.get("event")
        user = self.context.get("request").user

        # Check if user already registered
        if Registration.objects.filter(event=event, attendee=user).exists():
            raise serializers.ValidationError(
                "You are already registered for this event."
            )

        # Check event capacity
        if event.capacity is not None:
            confirmed = event.registrations.filter(status="confirmed").count()
            if confirmed >= event.capacity:
                raise serializers.ValidationError("This event is at full capacity.")

        # Check if event has started
        if event.start_date < timezone.now():
            raise serializers.ValidationError(
                "Cannot register for an event that has already started."
            )

        # Check if event is cancelled
        if event.status == "cancelled":
            raise serializers.ValidationError("Cannot register for a cancelled event.")

        return attrs

    def create(self, validated_data):
        """Create registration."""
        event = self.context.get("event")
        user = self.context.get("request").user
        ticket_tier_id = validated_data.get("ticket_tier_id")
        notes = validated_data.get("notes", "")

        # Get ticket tier if specified
        ticket_tier = None
        if ticket_tier_id:
            ticket_tier = TicketTier.objects.get(id=ticket_tier_id, event=event)

        # Determine initial status
        if event.requires_approval:
            status = Registration.Status.PENDING
        else:
            # Check if event is at capacity
            if event.capacity is not None:
                confirmed = event.registrations.filter(status="confirmed").count()
                if confirmed >= event.capacity:
                    status = Registration.Status.WAITLISTED
                else:
                    status = Registration.Status.CONFIRMED
            else:
                status = Registration.Status.CONFIRMED

        registration = Registration.objects.create(
            event=event,
            attendee=user,
            ticket_tier=ticket_tier,
            status=status,
            notes=notes,
        )

        return registration


class RegistrationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating registration status (organizer/host only)."""

    class Meta:
        model = Registration
        fields = ["status"]

    def validate_status(self, value):
        """Validate status transition."""
        instance = self.instance

        # Don't allow changing status of cancelled registrations
        if instance.status == Registration.Status.CANCELLED:
            raise serializers.ValidationError(
                "Cannot change status of a cancelled registration."
            )

        # Don't allow changing status to ATTENDED before event starts
        if value == Registration.Status.ATTENDED:
            event = instance.event
            if event.start_date > timezone.now():
                raise serializers.ValidationError(
                    "Cannot mark attendance before event starts."
                )

        # If changing to CONFIRMED, check capacity
        if value == Registration.Status.CONFIRMED:
            event = instance.event
            if event.capacity is not None:
                confirmed = event.registrations.filter(status="confirmed").count()
                # Don't count current registration if it's already confirmed
                if instance.status != Registration.Status.CONFIRMED:
                    if confirmed >= event.capacity:
                        raise serializers.ValidationError(
                            "Event is at full capacity. Cannot confirm more registrations."
                        )

        return value


class RegistrationCheckInSerializer(serializers.Serializer):
    """Serializer for checking in an attendee."""

    def validate(self, attrs):
        """Validate check-in."""
        registration = self.context.get("registration")

        # Check if already checked in
        if registration.checked_in_at is not None:
            raise serializers.ValidationError("Attendee is already checked in.")

        # Check if registration is confirmed
        if registration.status != Registration.Status.CONFIRMED:
            raise serializers.ValidationError(
                "Only confirmed registrations can be checked in."
            )

        # Check if event has started (allow check-in 1 hour before)
        event = registration.event
        one_hour_before = event.start_date - timezone.timedelta(hours=1)
        if timezone.now() < one_hour_before:
            raise serializers.ValidationError(
                "Check-in is not yet available. Event starts at "
                + event.start_date.strftime("%Y-%m-%d %H:%M %Z")
            )

        return attrs
