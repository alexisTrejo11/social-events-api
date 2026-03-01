import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field

from apps.organizations.models import Organization, OrganizationMembership
from apps.locations.models import Location

User = get_user_model()
logger = logging.getLogger(__name__)


class OrganizationMemberSerializer(serializers.ModelSerializer):
    """Serializer for organization member details with user information."""

    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()
    invited_by_email = serializers.EmailField(source="invited_by.email", read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = [
            "id",
            "user",
            "user_email",
            "user_name",
            "role",
            "title",
            "joined_at",
            "invited_by",
            "invited_by_email",
            "is_public",
        ]
        read_only_fields = [
            "id",
            "joined_at",
            "user_email",
            "user_name",
            "invited_by_email",
        ]

    @extend_schema_field(serializers.CharField())
    def get_user_name(self, obj):
        """Get the full name of the member."""
        return obj.user.get_full_name()


class OrganizationListSerializer(serializers.ModelSerializer):
    """Serializer for listing organizations with aggregate counts."""

    member_count = serializers.SerializerMethodField()
    event_count = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "logo",
            "is_verified",
            "is_active",
            "member_count",
            "event_count",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    @extend_schema_field(serializers.IntegerField())
    def get_member_count(self, obj):
        """Get total number of members in the organization."""
        return obj.memberships.count()

    @extend_schema_field(serializers.IntegerField())
    def get_event_count(self, obj):
        """Get total number of published events created by the organization."""
        return obj.events.filter(status="published").count()

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_created_by_name(self, obj):
        """Get the full name of the organization creator."""
        return obj.created_by.get_full_name() if obj.created_by else None


class OrganizationDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed organization information including location and stats."""

    location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), required=False, allow_null=True
    )
    location_details = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    event_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "logo",
            "website",
            "email",
            "phone_number",
            "location",
            "location_details",
            "is_verified",
            "is_active",
            "created_by",
            "created_by_name",
            "member_count",
            "event_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_by", "created_at", "updated_at"]

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_location_details(self, obj):
        """Get basic location information for the organization."""
        if obj.location:
            return {
                "id": obj.location.id,
                "name": obj.location.name,
                "city": obj.location.city,
                "country": obj.location.country,
            }
        return None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_created_by_name(self, obj):
        """Get the full name of the organization creator."""
        return obj.created_by.get_full_name() if obj.created_by else None

    @extend_schema_field(serializers.IntegerField())
    def get_member_count(self, obj):
        """Get total number of members in the organization."""
        return obj.memberships.count()

    @extend_schema_field(serializers.IntegerField())
    def get_event_count(self, obj):
        """Get total number of published events created by the organization."""
        return obj.events.filter(status="published").count()


class OrganizationCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating organizations with validation."""

    class Meta:
        model = Organization
        fields = [
            "name",
            "description",
            "logo",
            "website",
            "email",
            "phone_number",
            "location",
        ]

    def validate_email(self, value):
        """Validate organization email"""
        if value and not "@" in value:
            raise serializers.ValidationError("Enter a valid email address.")
        return value

    def validate_website(self, value):
        """Validate website URL"""
        if value and not value.startswith(("http://", "https://")):
            raise serializers.ValidationError(
                "Website must start with http:// or https://"
            )
        return value

    def create(self, validated_data):
        """Create organization and set creator"""
        request = self.context.get("request")
        validated_data["created_by"] = request.user
        logger.info(
            f"Creating organization '{validated_data['name']}' by user {request.user.email}"
        )
        return super().create(validated_data)


class MemberInviteSerializer(serializers.Serializer):
    """Serializer for inviting members to an organization by email."""

    email = serializers.EmailField(required=True)
    role = serializers.ChoiceField(
        choices=OrganizationMembership.Role.choices,
        default=OrganizationMembership.Role.MEMBER,
    )
    title = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_email(self, value):
        """Check if user exists"""
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        return value


class MemberUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating member role, title, and visibility."""

    class Meta:
        model = OrganizationMembership
        fields = ["role", "title", "is_public"]

    def validate_role(self, value):
        """Prevent downgrading the last owner"""
        instance = self.instance
        if instance and instance.role == OrganizationMembership.Role.OWNER:
            owner_count = instance.organization.memberships.filter(
                role=OrganizationMembership.Role.OWNER
            ).count()
            if owner_count <= 1 and value != OrganizationMembership.Role.OWNER:
                raise serializers.ValidationError(
                    "Cannot change role: organization must have at least one owner."
                )
        return value
