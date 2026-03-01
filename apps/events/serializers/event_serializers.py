"""Event serializers for CRUD, publish, cancel, and favorite operations."""

from rest_framework import serializers
from django.utils import timezone

from apps.events.models import Event, RecurrenceRule, Category, Tag
from apps.locations.models import Location
from apps.organizations.models import Organization
from apps.users.serializers import PublicUserProfileSerializer
from apps.locations.serializers import LocationListSerializer
from .category_serializers import CategorySerializer, TagSerializer


class RecurrenceRuleSerializer(serializers.ModelSerializer):
    """Serializer for event recurrence rules."""

    class Meta:
        model = RecurrenceRule
        fields = [
            "frequency",
            "interval",
            "by_weekday",
            "by_month_day",
            "end_date",
            "max_occurrences",
        ]


class EventListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for event lists."""

    organizer = PublicUserProfileSerializer(read_only=True)
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    category_name = serializers.CharField(source="category.name", read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    is_favorited = serializers.SerializerMethodField()
    attendees_count = serializers.SerializerMethodField()
    available_spots = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "slug",
            "title",
            "description",
            "cover_image",
            "organizer",
            "organization_name",
            "category_name",
            "tags",
            "event_type",
            "start_date",
            "end_date",
            "timezone",
            "location_name",
            "capacity",
            "is_private",
            "status",
            "is_favorited",
            "attendees_count",
            "available_spots",
            "created_at",
        ]

    def get_is_favorited(self, obj):
        """Check if current user has favorited this event."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.favorites.filter(id=request.user.id).exists()
        return False

    def get_attendees_count(self, obj):
        """Count confirmed registrations."""
        return obj.registrations.filter(status="confirmed").count()

    def get_available_spots(self, obj):
        """Calculate remaining capacity."""
        if obj.capacity is None:
            return None
        attendees = obj.registrations.filter(status="confirmed").count()
        return max(0, obj.capacity - attendees)


class EventDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for event detail view."""

    organizer = PublicUserProfileSerializer(read_only=True)
    organization = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    location = LocationListSerializer(read_only=True)
    recurrence = RecurrenceRuleSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    attendees_count = serializers.SerializerMethodField()
    available_spots = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    user_registration = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "slug",
            "title",
            "description",
            "cover_image",
            "organizer",
            "organization",
            "category",
            "tags",
            "event_type",
            "start_date",
            "end_date",
            "timezone",
            "recurrence",
            "location",
            "capacity",
            "is_private",
            "requires_approval",
            "status",
            "is_favorited",
            "attendees_count",
            "available_spots",
            "user_role",
            "user_registration",
            "created_at",
            "updated_at",
        ]

    def get_organization(self, obj):
        """Return organization summary if event belongs to one."""
        if not obj.organization:
            return None
        return {
            "id": obj.organization.id,
            "name": obj.organization.name,
            "slug": obj.organization.slug,
            "logo": obj.organization.logo.url if obj.organization.logo else None,
        }

    def get_is_favorited(self, obj):
        """Check if current user has favorited this event."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.favorites.filter(id=request.user.id).exists()
        return False

    def get_attendees_count(self, obj):
        """Count confirmed registrations."""
        return obj.registrations.filter(status="confirmed").count()

    def get_available_spots(self, obj):
        """Calculate remaining capacity."""
        if obj.capacity is None:
            return None
        attendees = obj.registrations.filter(status="confirmed").count()
        return max(0, obj.capacity - attendees)

    def get_user_role(self, obj):
        """Get current user's role in this event (if any)."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            role = obj.roles.filter(user=request.user).first()
            if role:
                return role.role
        return None

    def get_user_registration(self, obj):
        """Get current user's registration status (if any)."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            registration = obj.registrations.filter(attendee=request.user).first()
            if registration:
                return {
                    "id": registration.id,
                    "status": registration.status,
                    "ticket_tier": (
                        registration.ticket_tier.name
                        if registration.ticket_tier
                        else None
                    ),
                }
        return None


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating events."""

    category_slug = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Category.objects.all(),
        source="category",
        required=False,
        allow_null=True,
    )
    tag_slugs = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Tag.objects.all(),
        source="tags",
        many=True,
        required=False,
    )
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source="location",
        required=False,
        allow_null=True,
    )
    organization_id = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        source="organization",
        required=False,
        allow_null=True,
    )
    recurrence = RecurrenceRuleSerializer(required=False, allow_null=True)

    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "cover_image",
            "organization_id",
            "category_slug",
            "tag_slugs",
            "event_type",
            "start_date",
            "end_date",
            "timezone",
            "recurrence",
            "location_id",
            "capacity",
            "is_private",
            "requires_approval",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Limit organizations to those the user is a manager of
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            from apps.organizations.models import OrganizationMembership

            self.fields["organization_id"].queryset = Organization.objects.filter(
                memberships__user=request.user,
                memberships__role__in=OrganizationMembership.get_manager_roles(),
            )

    def validate(self, attrs):
        """Validate event dates and capacity."""
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        # Validate dates
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError(
                {"end_date": "End date must be after start date."}
            )

        # Validate start date is in the future for new events
        if not self.instance and start_date and start_date < timezone.now():
            raise serializers.ValidationError(
                {"start_date": "Event start date must be in the future."}
            )

        # Validate capacity
        capacity = attrs.get("capacity")
        if capacity is not None and capacity < 1:
            raise serializers.ValidationError(
                {"capacity": "Capacity must be at least 1."}
            )

        # If updating, check that reducing capacity doesn't drop below confirmed attendees
        if self.instance and capacity is not None:
            confirmed_count = self.instance.registrations.filter(
                status="confirmed"
            ).count()
            if capacity < confirmed_count:
                raise serializers.ValidationError(
                    {
                        "capacity": f"Cannot reduce capacity below {confirmed_count} confirmed attendees."
                    }
                )

        return attrs

    def create(self, validated_data):
        """Create event with recurrence rule if provided."""
        recurrence_data = validated_data.pop("recurrence", None)
        tags = validated_data.pop("tags", [])

        # Set organizer from request user
        validated_data["organizer"] = self.context["request"].user

        # Create event
        event = Event.objects.create(**validated_data)

        # Add tags
        if tags:
            event.tags.set(tags)

        # Create recurrence rule if provided
        if recurrence_data:
            recurrence = RecurrenceRule.objects.create(**recurrence_data)
            event.recurrence = recurrence
            event.save()

        return event

    def update(self, instance, validated_data):
        """Update event and handle recurrence rule."""
        recurrence_data = validated_data.pop("recurrence", None)
        tags = validated_data.pop("tags", None)

        # Update event fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update tags if provided
        if tags is not None:
            instance.tags.set(tags)

        # Handle recurrence update
        if recurrence_data is not None:
            if instance.recurrence:
                # Update existing recurrence
                for attr, value in recurrence_data.items():
                    setattr(instance.recurrence, attr, value)
                instance.recurrence.save()
            else:
                # Create new recurrence
                recurrence = RecurrenceRule.objects.create(**recurrence_data)
                instance.recurrence = recurrence
                instance.save()

        return instance


class EventPublishSerializer(serializers.Serializer):
    """Serializer for publishing an event."""

    def validate(self, attrs):
        """Validate that event can be published."""
        event = self.context.get("event")

        if event.status == Event.Status.PUBLISHED:
            raise serializers.ValidationError("Event is already published.")

        if event.status == Event.Status.CANCELLED:
            raise serializers.ValidationError("Cannot publish a cancelled event.")

        # Validate required fields are present
        if not event.title or not event.description:
            raise serializers.ValidationError(
                "Event must have a title and description to be published."
            )

        if not event.start_date or not event.end_date:
            raise serializers.ValidationError(
                "Event must have start and end dates to be published."
            )

        return attrs


class EventCancelSerializer(serializers.Serializer):
    """Serializer for cancelling an event."""

    cancellation_reason = serializers.CharField(
        required=False, allow_blank=True, max_length=500
    )

    def validate(self, attrs):
        """Validate that event can be cancelled."""
        event = self.context.get("event")

        if event.status == Event.Status.CANCELLED:
            raise serializers.ValidationError("Event is already cancelled.")

        if event.status == Event.Status.COMPLETED:
            raise serializers.ValidationError("Cannot cancel a completed event.")

        return attrs
