import logging
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from apps.organizations.models import Organization, OrganizationMembership
from apps.organizations.serializers import (
    OrganizationListSerializer,
    OrganizationDetailSerializer,
    OrganizationCreateUpdateSerializer,
    OrganizationMemberSerializer,
    MemberInviteSerializer,
    MemberUpdateSerializer,
)
from common.serializers import (
    ErrorResponseSerializer,
    MessageResponseSerializer,
    ValidationErrorSerializer,
    UserNotFoundErrorSerializer,
    OrganizationMemberErrorSerializer,
)
from common.throttling import (
    ReadHeavyThrottle,
    WriteSensitiveThrottle,
    WriteStandardThrottle,
)

User = get_user_model()
logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="List all active organizations",
        description="Returns a paginated list of active organizations with member and event counts. "
        "Supports filtering, search, and ordering.",
        tags=["Organizations"],
        responses={
            200: OrganizationListSerializer(many=True),
            401: ErrorResponseSerializer,
        },
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search term to filter organizations by name, description, or email",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Order results by field. Prefix with '-' for descending. "
                "Options: name, created_at, updated_at",
            ),
            OpenApiParameter(
                name="is_verified",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter by verification status",
            ),
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter by active status",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Get organization details",
        description="Returns detailed information for a specific organization identified by slug.",
        tags=["Organizations"],
        responses={
            200: OrganizationDetailSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    create=extend_schema(
        summary="Create a new organization",
        description="Create a new organization. The requesting user becomes the first owner.",
        tags=["Organizations"],
        request=OrganizationCreateUpdateSerializer,
        responses={
            201: OrganizationDetailSerializer,
            400: ValidationErrorSerializer,
            401: ErrorResponseSerializer,
        },
    ),
    update=extend_schema(
        summary="Update an organization",
        description="Fully update an organization. Only accessible to organization owners and admins.",
        tags=["Organizations"],
        request=OrganizationCreateUpdateSerializer,
        responses={
            200: OrganizationDetailSerializer,
            400: ValidationErrorSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    partial_update=extend_schema(
        summary="Partially update an organization",
        description="Partially update an organization with provided fields. Only accessible to organization owners and admins.",
        tags=["Organizations"],
        request=OrganizationCreateUpdateSerializer,
        responses={
            200: OrganizationDetailSerializer,
            400: ValidationErrorSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
    destroy=extend_schema(
        summary="Deactivate an organization",
        description="Soft delete an organization by marking it as inactive. Only accessible to organization owners.",
        tags=["Organizations"],
        responses={
            204: None,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    ),
)
class OrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing organizations and their memberships.

    Organizations are entities that can create events and have members with different roles.
    Supports CRUD operations on organizations and member management actions.

    Standard actions:
    - list: Get all active organizations with filtering and search
    - create: Create a new organization (user becomes owner)
    - retrieve: Get organization details by slug
    - update: Fully update an organization (owners/admins only)
    - partial_update: Partially update an organization (owners/admins only)
    - destroy: Soft delete/deactivate organization (owners only)

    Custom actions:
    - members: List organization members
    - invite_member: Invite a user to join by email
    - update_member: Update member role or title
    - remove_member: Remove a member from the organization
    - join: Join a public organization
    - leave: Leave the organization
    - events: List events created by the organization
    """

    queryset = Organization.objects.filter(is_active=True)
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["name", "description", "email"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["-created_at"]
    filterset_fields = ["is_verified", "is_active"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "list":
            return OrganizationListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return OrganizationCreateUpdateSerializer
        return OrganizationDetailSerializer

    def get_throttles(self):
        """Return appropriate throttles based on action."""
        if self.action == "list":
            return [ReadHeavyThrottle()]
        elif self.action == "create":
            return [WriteSensitiveThrottle()]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [WriteSensitiveThrottle()]
        elif self.action in ["members", "events"]:
            return [ReadHeavyThrottle()]
        elif self.action in ["invite_member", "update_member", "remove_member"]:
            return [WriteSensitiveThrottle()]
        elif self.action in ["join", "leave"]:
            return [WriteStandardThrottle()]
        return [ReadHeavyThrottle()]

    def perform_create(self, serializer):
        """Create organization and add creator as owner"""
        logger.info(f"User {self.request.user.email} creating organization")
        organization = serializer.save()

        # Add creator as owner
        OrganizationMembership.objects.create(
            organization=organization,
            user=self.request.user,
            role=OrganizationMembership.Role.OWNER,
            invited_by=None,
        )
        logger.info(f"Organization {organization.slug} created successfully")

    def perform_update(self, serializer):
        """Update organization"""
        logger.info(
            f"User {self.request.user.email} updating organization {serializer.instance.slug}"
        )
        serializer.save()

    def perform_destroy(self, instance):
        """Soft delete: deactivate organization instead of deleting"""
        logger.info(
            f"User {self.request.user.email} deactivating organization {instance.slug}"
        )
        instance.is_active = False
        instance.save()

    @extend_schema(
        summary="List organization members",
        description="Get a list of all members in the organization with their roles and details.",
        tags=["Organizations"],
        responses={
            200: OrganizationMemberSerializer(many=True),
            401: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    )
    @action(detail=True, methods=["get"])
    def members(self, request, slug=None):
        """
        GET /organizations/{slug}/members/
        List organization members
        """
        organization = self.get_object()
        logger.info(f"Fetching members for organization {organization.slug}")

        memberships = organization.memberships.select_related(
            "user", "invited_by"
        ).all()
        serializer = OrganizationMemberSerializer(memberships, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Invite a member to the organization",
        description="Invite a user to join the organization by email. The user must already be registered in the system.",
        tags=["Organizations"],
        request=MemberInviteSerializer,
        responses={
            201: OrganizationMemberSerializer,
            400: OrganizationMemberErrorSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: UserNotFoundErrorSerializer,
        },
    )
    @action(detail=True, methods=["post"], url_path="members/invite")
    def invite_member(self, request, slug=None):
        """
        POST /organizations/{slug}/members/invite/
        Invite a user to join the organization
        """
        organization = self.get_object()
        serializer = MemberInviteSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            role = serializer.validated_data.get(
                "role", OrganizationMembership.Role.MEMBER
            )
            title = serializer.validated_data.get("title", "")

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                logger.warning(
                    f"Attempt to invite non-existent user {email} to {organization.slug}"
                )
                error_data = {"error": "User not found"}
                return Response(
                    UserNotFoundErrorSerializer(error_data).data,
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Check if user is already a member
            if organization.memberships.filter(user=user).exists():
                logger.warning(f"User {email} already member of {organization.slug}")
                error_data = {"error": "User is already a member of this organization"}
                return Response(
                    OrganizationMemberErrorSerializer(error_data).data,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create membership
            membership = OrganizationMembership.objects.create(
                organization=organization,
                user=user,
                role=role,
                title=title,
                invited_by=request.user,
            )

            logger.info(
                f"User {email} invited to {organization.slug} by {request.user.email}"
            )
            return Response(
                OrganizationMemberSerializer(membership).data,
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Update organization member",
        description="Update a member's role or title in the organization. Only accessible to organization owners and admins.",
        tags=["Organizations"],
        request=MemberUpdateSerializer,
        responses={
            200: MemberUpdateSerializer,
            400: ValidationErrorSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: OrganizationMemberErrorSerializer,
        },
    )
    @action(detail=True, methods=["patch"], url_path="members/(?P<user_id>[^/.]+)")
    def update_member(self, request, slug=None, user_id=None):
        """
        PATCH /organizations/{slug}/members/{user_id}/
        Update member role or title
        """
        organization = self.get_object()

        try:
            membership = organization.memberships.get(user_id=user_id)
        except OrganizationMembership.DoesNotExist:
            logger.warning(
                f"Membership not found for user {user_id} in org {organization.slug}"
            )
            return Response(
                {"error": "Member not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = MemberUpdateSerializer(membership, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(
                f"Membership updated for user {user_id} in org {organization.slug}"
            )
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Remove organization member",
        description="Remove a member from the organization. Only accessible to organization owners and admins. Cannot remove the last owner.",
        tags=["Organizations"],
        responses={
            204: None,
            400: OrganizationMemberErrorSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: OrganizationMemberErrorSerializer,
        },
    )
    @action(detail=True, methods=["delete"], url_path="members/(?P<user_id>[^/.]+)")
    def remove_member(self, request, slug=None, user_id=None):
        """
        DELETE /organizations/{slug}/members/{user_id}/
        Remove a member from the organization
        """
        organization = self.get_object()

        try:
            membership = organization.memberships.get(user_id=user_id)
        except OrganizationMembership.DoesNotExist:
            logger.warning(
                f"Membership not found for user {user_id} in org {organization.slug}"
            )
            return Response(
                {"error": "Member not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Prevent removing last owner
        if membership.role == OrganizationMembership.Role.OWNER:
            owner_count = organization.memberships.filter(
                role=OrganizationMembership.Role.OWNER
            ).count()
            if owner_count <= 1:
                logger.warning(f"Attempt to remove last owner from {organization.slug}")
                return Response(
                    {"error": "Cannot remove the last owner of the organization"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        membership.delete()
        logger.info(f"User {user_id} removed from organization {organization.slug}")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Join an organization",
        description="Join a public organization as a member. The authenticated user will be added as a member.",
        tags=["Organizations"],
        request=None,
        responses={
            201: OrganizationMemberSerializer,
            400: OrganizationMemberErrorSerializer,
            401: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    )
    @action(detail=True, methods=["post"])
    def join(self, request, slug=None):
        """
        POST /organizations/{slug}/join/
        Request to join a public organization
        """
        organization = self.get_object()

        # Check if user is already a member
        if organization.memberships.filter(user=request.user).exists():
            logger.warning(
                f"User {request.user.email} already member of {organization.slug}"
            )
            return Response(
                {"error": "You are already a member of this organization"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create membership with guest/member role
        membership = OrganizationMembership.objects.create(
            organization=organization,
            user=request.user,
            role=OrganizationMembership.Role.MEMBER,
            invited_by=None,
        )

        logger.info(
            f"User {request.user.email} joined organization {organization.slug}"
        )
        return Response(
            OrganizationMemberSerializer(membership).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Leave an organization",
        description="Leave the organization. The authenticated user's membership will be removed. Cannot leave if you are the last owner.",
        tags=["Organizations"],
        responses={
            204: None,
            400: OrganizationMemberErrorSerializer,
            401: ErrorResponseSerializer,
            404: OrganizationMemberErrorSerializer,
        },
    )
    @action(detail=True, methods=["delete"])
    def leave(self, request, slug=None):
        """
        DELETE /organizations/{slug}/leave/
        Leave the organization
        """
        organization = self.get_object()

        try:
            membership = organization.memberships.get(user=request.user)
        except OrganizationMembership.DoesNotExist:
            logger.warning(
                f"User {request.user.email} not a member of {organization.slug}"
            )
            return Response(
                {"error": "You are not a member of this organization"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Prevent last owner from leaving
        if membership.role == OrganizationMembership.Role.OWNER:
            owner_count = organization.memberships.filter(
                role=OrganizationMembership.Role.OWNER
            ).count()
            if owner_count <= 1:
                logger.warning(
                    f"Last owner {request.user.email} attempting to leave {organization.slug}"
                )
                return Response(
                    {
                        "error": "Cannot leave: you are the last owner. Transfer ownership first."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        membership.delete()
        logger.info(f"User {request.user.email} left organization {organization.slug}")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="List organization events",
        description="Get a list of all events created by this organization. Returns basic event information including title, status, dates, and location.",
        tags=["Organizations"],
        responses={
            200: {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "title": {"type": "string"},
                        "slug": {"type": "string"},
                        "status": {"type": "string"},
                        "event_type": {"type": "string"},
                        "start_date": {"type": "string", "format": "date-time"},
                        "end_date": {"type": "string", "format": "date-time"},
                        "location": {"type": "string", "nullable": True},
                    },
                },
            },
            404: ErrorResponseSerializer,
        },
    )
    @action(detail=True, methods=["get"])
    def events(self, request, slug=None):
        """
        GET /organizations/{slug}/events/
        List events created by this organization
        """
        organization = self.get_object()
        logger.info(f"Fetching events for organization {organization.slug}")

        from apps.events.models import Event

        events = Event.objects.filter(
            organization=organization, is_deleted=False
        ).select_related("location", "category", "organizer")

        # Return simplified event data
        events_data = [
            {
                "id": str(event.id),
                "title": event.title,
                "slug": event.slug,
                "status": event.status,
                "event_type": event.event_type,
                "start_date": event.start_date,
                "end_date": event.end_date,
                "location": event.location.name if event.location else None,
            }
            for event in events
        ]

        return Response(events_data)
