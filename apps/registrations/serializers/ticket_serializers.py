"""Ticket tier serializers."""

from rest_framework import serializers
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field

from apps.registrations.models import TicketTier


class TicketTierSerializer(serializers.ModelSerializer):
    """Serializer for viewing ticket tiers."""

    available_capacity = serializers.SerializerMethodField()
    registrations_count = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = TicketTier
        fields = [
            "id",
            "name",
            "description",
            "price",
            "currency",
            "capacity",
            "visibility",
            "sale_start",
            "sale_end",
            "is_active",
            "available_capacity",
            "registrations_count",
            "is_available",
        ]

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_registrations_count(self, obj):
        """Count confirmed registrations for this tier."""
        return obj.registrations.filter(status="confirmed").count()

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_available_capacity(self, obj):
        """Calculate remaining capacity for this tier."""
        if obj.capacity is None:
            return None
        confirmed = obj.registrations.filter(status="confirmed").count()
        return max(0, obj.capacity - confirmed)

    @extend_schema_field(serializers.BooleanField())
    def get_is_available(self, obj):
        """Check if tier is currently available for purchase."""
        if not obj.is_active:
            return False

        now = timezone.now()

        # Check sale window
        if obj.sale_start and now < obj.sale_start:
            return False
        if obj.sale_end and now > obj.sale_end:
            return False

        # Check capacity
        if obj.capacity is not None:
            confirmed = obj.registrations.filter(status="confirmed").count()
            if confirmed >= obj.capacity:
                return False

        return True


class TicketTierCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating ticket tiers."""

    class Meta:
        model = TicketTier
        fields = [
            "name",
            "description",
            "price",
            "currency",
            "capacity",
            "visibility",
            "sale_start",
            "sale_end",
            "is_active",
        ]
        extra_kwargs = {
            "name": {
                "help_text": "Name of the ticket tier (e.g., 'General Admission', 'VIP')"
            },
            "description": {"help_text": "Description of what's included in this tier"},
            "price": {"help_text": "Price of the ticket in the specified currency"},
            "currency": {"help_text": "Currency code (e.g., USD, EUR, GBP)"},
            "capacity": {
                "help_text": "Maximum number of tickets available in this tier (null for unlimited)"
            },
            "visibility": {
                "help_text": "Visibility of this ticket tier (public, private, or hidden)"
            },
            "sale_start": {
                "help_text": "Date and time when ticket sales start (null for immediate)"
            },
            "sale_end": {
                "help_text": "Date and time when ticket sales end (null for until event starts)"
            },
            "is_active": {
                "help_text": "Whether this ticket tier is currently active and available for purchase"
            },
        }

    def validate(self, attrs):
        """Validate ticket tier data."""
        sale_start = attrs.get("sale_start")
        sale_end = attrs.get("sale_end")

        # Validate sale window
        if sale_start and sale_end and sale_end <= sale_start:
            raise serializers.ValidationError(
                {"sale_end": "Sale end must be after sale start."}
            )

        # Validate capacity
        capacity = attrs.get("capacity")
        if capacity is not None and capacity < 1:
            raise serializers.ValidationError(
                {"capacity": "Capacity must be at least 1."}
            )

        # If updating, check that reducing capacity doesn't drop below confirmed registrations
        if self.instance and capacity is not None:
            confirmed_count = self.instance.registrations.filter(
                status="confirmed"
            ).count()
            if capacity < confirmed_count:
                raise serializers.ValidationError(
                    {
                        "capacity": f"Cannot reduce capacity below {confirmed_count} confirmed registrations."
                    }
                )

        return attrs
