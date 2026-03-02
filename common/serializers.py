"""Common serializers for API documentation and error responses."""

from rest_framework import serializers


class ErrorDetailSerializer(serializers.Serializer):
    """Standard error detail response."""

    error = serializers.CharField(help_text="Error message describing what went wrong")


class ErrorResponseSerializer(serializers.Serializer):
    """Standard error response with detail field."""

    detail = serializers.CharField(help_text="Error message describing what went wrong")


class ValidationErrorSerializer(serializers.Serializer):
    """Validation error response with field-specific errors."""

    field_name = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of error messages for the field",
    )


class MessageResponseSerializer(serializers.Serializer):
    """Generic success message response."""

    message = serializers.CharField(help_text="Success message")


class LocationDeletionErrorSerializer(serializers.Serializer):
    """Error response when attempting to delete a location in use."""

    error = serializers.CharField(help_text="Error message")
    organizations_count = serializers.IntegerField(
        help_text="Number of organizations using this location"
    )
    events_count = serializers.IntegerField(
        help_text="Number of events using this location"
    )


class TokenErrorSerializer(serializers.Serializer):
    """Error response for invalid or missing tokens."""

    error = serializers.CharField(help_text="Token error message")


class PermissionDeniedSerializer(serializers.Serializer):
    """Error response for permission denied."""

    detail = serializers.CharField(help_text="Permission error message")


class NotFoundSerializer(serializers.Serializer):
    """Error response for resource not found."""

    detail = serializers.CharField(help_text="Not found error message")


class ConflictErrorSerializer(serializers.Serializer):
    """Error response for conflict (e.g., already registered)."""

    error = serializers.CharField(help_text="Conflict error message")


class CountResponseSerializer(serializers.Serializer):
    """Response containing a count of items."""

    count = serializers.IntegerField(help_text="Number of items")


class UserNotFoundErrorSerializer(serializers.Serializer):
    """Error response when a user is not found."""

    error = serializers.CharField(help_text="User not found message")


class OrganizationMemberErrorSerializer(serializers.Serializer):
    """Error response for organizationmember-related errors."""

    error = serializers.CharField(help_text="Member-related error message")
