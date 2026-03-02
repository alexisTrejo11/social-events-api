from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """
    Full access to the owner of the object.
    Everyone else gets read-only access.

    Expects the object to have an `owner` or `user` attribute pointing to a User.
    Override `get_object_owner()` in the view if your field name differs.
    """

    def has_permission(self, request, view):
        # Allow unauthenticated users to read, but require auth to write
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        # Support both .user and .owner field naming conventions
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        return owner == request.user


class IsSelfOrReadOnly(BasePermission):
    """
    Used on User profile endpoints.
    A user can only modify their own profile.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user


class IsVerifiedUser(BasePermission):
    """
    Blocks any action (including reads) for users who have not
    verified their email address yet.
    """

    message = "You must verify your email address before performing this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.email_verified
        )
