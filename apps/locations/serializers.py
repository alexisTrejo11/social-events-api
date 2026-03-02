from typing import LiteralString
import logging
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from apps.locations.models import Location

logger = logging.getLogger(__name__)


class LocationListSerializer(serializers.ModelSerializer):
    """Serializer for listing locations with computed full address."""

    full_address = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = [
            "id",
            "name",
            "city",
            "state_province",
            "country",
            "is_virtual",
            "virtual_url",
            "full_address",
        ]

    @extend_schema_field(serializers.CharField())
    def get_full_address(self, obj):
        """Get formatted full address. For virtual locations, returns 'Virtual — {URL}', otherwise comma-separated address parts."""
        if obj.is_virtual:
            return f"Virtual — {obj.virtual_url}"
        parts = [obj.name, obj.city, obj.state_province, obj.country]
        return ", ".join(filter[LiteralString](None, parts))


class LocationDetailSerializer(serializers.ModelSerializer):
    """Serializer for retrieving detailed location information including coordinates."""

    class Meta:
        model = Location
        fields = [
            "id",
            "name",
            "address_line_1",
            "address_line_2",
            "city",
            "state_province",
            "postal_code",
            "country",
            "latitude",
            "longitude",
            "is_virtual",
            "virtual_url",
        ]


class LocationCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating locations with validation for virtual vs physical locations."""

    class Meta:
        model = Location
        fields = [
            "name",
            "address_line_1",
            "address_line_2",
            "city",
            "state_province",
            "postal_code",
            "country",
            "latitude",
            "longitude",
            "is_virtual",
            "virtual_url",
        ]

    def validate(self, data):
        """Validate location data"""
        is_virtual = data.get("is_virtual", False)

        if is_virtual:
            # Virtual locations must have a URL
            if not data.get("virtual_url"):
                raise serializers.ValidationError(
                    {"virtual_url": "Virtual locations must have a virtual URL."}
                )
        else:
            # Physical locations must have address and city
            if not data.get("address_line_1"):
                raise serializers.ValidationError(
                    {"address_line_1": "Physical locations must have an address."}
                )
            if not data.get("city"):
                raise serializers.ValidationError(
                    {"city": "Physical locations must have a city."}
                )
            if not data.get("country"):
                raise serializers.ValidationError(
                    {"country": "Physical locations must have a country."}
                )

        # Validate coordinates if provided
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if latitude is not None:
            if not -90 <= float(latitude) <= 90:
                raise serializers.ValidationError(
                    {"latitude": "Latitude must be between -90 and 90."}
                )

        if longitude is not None:
            if not -180 <= float(longitude) <= 180:
                raise serializers.ValidationError(
                    {"longitude": "Longitude must be between -180 and 180."}
                )

        return data

    def create(self, validated_data):
        """Create location"""
        logger.info(f"Creating location: {validated_data.get('name', 'Unnamed')}")
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update location"""
        logger.info(f"Updating location: {instance.id}")
        return super().update(instance, validated_data)
