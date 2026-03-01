import uuid
from django.db import models
from django.conf import settings

from apps.locations.models import Location
from common.utils import unique_slug


class Organization(models.Model):
    """
    Represents a company, community group, or any collective entity
    that can create and manage events.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="org_logos/%Y/%m/", blank=True, null=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organizations",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="OrganizationMembership",
        through_fields=("organization", "user"),
        related_name="organizations",
    )
    is_verified = models.BooleanField(default=False)  # verified business badge
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_organizations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["slug"])]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, Organization)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class OrganizationMembership(models.Model):
    """
    Granular roles within an organization.
    """

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MANAGER = "manager", "Event Manager"
        MEMBER = "member", "Member"
        GUEST = "guest", "Guest"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="org_memberships",
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    title = models.CharField(max_length=100, blank=True)  # e.g. "Lead Organizer"
    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_org_invites",
    )
    is_public = models.BooleanField(default=True)  # show on org's public member list

    class Meta:
        unique_together = ["organization", "user"]
        ordering = ["role", "joined_at"]

    def __str__(self) -> str:
        return f"{self.user.get_full_name()} — {self.role} @ {self.organization.name}"

    def get_admin_roles(self) -> list[Role]:
        return [self.Role.OWNER, self.Role.ADMIN]

    def get_manager_roles(self) -> list[Role]:
        return [self.Role.MANAGER, self.Role.OWNER, self.Role.ADMIN]

    def get_member_roles(self) -> list[Role]:
        return [self.Role.OWNER, self.Role.ADMIN, self.Role.MANAGER, self.Role.MEMBER]

    def get_all_roles(self) -> list[Role]:
        return [
            self.Role.OWNER,
            self.Role.ADMIN,
            self.Role.MANAGER,
            self.Role.MEMBER,
            self.Role.GUEST,
        ]
