from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.organizations.models import OrganizationMembership


def get_membership(user, organization) -> OrganizationMembership | None:
    """Helper — returns the membership object or None."""
    try:
        return OrganizationMembership.objects.get(user=user, organization=organization)
    except OrganizationMembership.DoesNotExist:
        return None


def has_org_role(user, organization, *roles) -> bool:
    """Returns True if user has any of the given roles in the organization."""
    if not user or not user.is_authenticated:
        return False
    membership = get_membership(user, organization)
    return membership is not None and membership.role in roles


class IsOrgOwner(BasePermission):
    """
    Only the organization owner.
    Typically used for destructive actions like deleting the org
    or transferring ownership.
    """

    message = "Only the organization owner can perform this action."

    def has_object_permission(self, request, view, obj):
        return has_org_role(request.user, obj, OrganizationMembership.Role.OWNER)


class IsOrgAdmin(BasePermission):
    """
    Owner or Admin.
    Used for sensitive settings: editing org profile, managing members,
    changing roles.
    """

    message = "You must be an organization admin to perform this action."

    def has_object_permission(self, request, view, obj):
        return has_org_role(request.user, obj, OrganizationMembership.get_admin_roles())


class IsOrgManager(BasePermission):
    """
    Owner, Admin, or Manager.
    Used for event management within the org: creating, editing,
    cancelling events.
    """

    message = "You must be an organization manager or above to perform this action."

    def has_object_permission(self, request, view, obj):
        return has_org_role(
            request.user, obj, OrganizationMembership.get_manager_roles()
        )


class IsOrgMember(BasePermission):
    """
    Any active member of the organization (any role).
    Used for read access to private org content.
    """

    message = "You must be a member of this organization to view this content."

    def has_object_permission(self, request, view, obj):
        return has_org_role(request.user, obj, OrganizationMembership.get_all_roles())


class IsOrgMemberOrReadOnly(BasePermission):
    """
    Public read access.
    Write access restricted to org members.
    Useful for org-level comments or discussions in the future.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return has_org_role(
            request.user, obj, OrganizationMembership.get_member_roles()
        )
