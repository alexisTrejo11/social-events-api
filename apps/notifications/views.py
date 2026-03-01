"""Notification views."""

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from apps.notifications.models import Notification
from apps.notifications.serializers import (
    NotificationSerializer,
    NotificationListSerializer,
    NotificationMarkReadSerializer,
)
from common.serializers import (
    ErrorResponseSerializer,
    ValidationErrorSerializer,
)


@extend_schema(
    tags=["Notifications"],
    summary="List all notifications for the authenticated user",
    description="Returns a list of all notifications for the current user. "
    "Can filter by read status and notification type.",
    parameters=[
        OpenApiParameter(
            name="is_read",
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            description="Filter by read status (true/false)",
        ),
        OpenApiParameter(
            name="notification_type",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filter by notification type",
        ),
    ],
    responses={
        200: NotificationListSerializer(many=True),
        401: ErrorResponseSerializer,
    },
)
class NotificationListView(generics.ListAPIView):
    """
    List all notifications for the authenticated user.

    GET /notifications/ - List all notifications
    Query params:
    - is_read: Filter by read status (true/false)
    - notification_type: Filter by type
    """

    serializer_class = NotificationListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return notifications for the current user."""
        queryset = (
            Notification.objects.filter(recipient=self.request.user)
            .select_related("actor", "event", "organization")
            .order_by("-created_at")
        )

        # Filter by read status
        is_read = self.request.query_params.get("is_read")
        if is_read is not None:
            is_read_bool = is_read.lower() == "true"
            queryset = queryset.filter(is_read=is_read_bool)

        # Filter by notification type
        notification_type = self.request.query_params.get("notification_type")
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        return queryset


@extend_schema(
    tags=["Notifications"],
    summary="Get notification details",
    description="Returns detailed information for a specific notification.",
    responses={
        200: NotificationSerializer,
        401: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
class NotificationDetailView(generics.RetrieveAPIView):
    """
    Get notification details.

    GET /notifications/{id}/ - Get notification detail
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return notifications for the current user."""
        return Notification.objects.filter(recipient=self.request.user).select_related(
            "actor", "event", "organization"
        )


@extend_schema(
    tags=["Notifications"],
    summary="Mark a notification as read",
    description="Mark a specific notification as read.",
    responses={
        200: NotificationSerializer,
        401: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_as_read(request, notification_id):
    """
    Mark a specific notification as read.

    POST /notifications/{id}/read/
    """
    notification = get_object_or_404(
        Notification, id=notification_id, recipient=request.user
    )

    notification.mark_as_read()

    return Response(
        NotificationSerializer(notification, context={"request": request}).data,
        status=status.HTTP_200_OK,
    )


@extend_schema(
    tags=["Notifications"],
    summary="Mark all notifications as read",
    description="Mark all notifications or a specific set of notifications as read. "
    "If notification_ids is provided, only those notifications are marked as read.",
    request=NotificationMarkReadSerializer,
    responses={
        200: NotificationSerializer(many=True),
        400: ValidationErrorSerializer,
        401: ErrorResponseSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_all_as_read(request):
    """
    Mark all notifications or selected notifications as read.

    POST /notifications/mark-all-read/
    Body (optional):
    {
        "notification_ids": [1, 2, 3]  // If not provided, marks all as read
    }
    """
    serializer = NotificationMarkReadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    notification_ids = serializer.validated_data.get("notification_ids")

    if notification_ids:
        # Mark specific notifications as read
        count = Notification.objects.filter(
            recipient=request.user, id__in=notification_ids, is_read=False
        ).update(is_read=True)
    else:
        # Mark all as read
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True)

    return Response(
        {"detail": f"{count} notification(s) marked as read."},
        status=status.HTTP_200_OK,
    )


@extend_schema(
    tags=["Notifications"],
    summary="Delete a notification",
    description="Delete a specific notification by its ID.",
    responses={
        204: OpenApiTypes.NONE,
        401: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_notification(request, notification_id):
    """
    Delete a notification.

    DELETE /notifications/{id}/
    """
    notification = get_object_or_404(
        Notification, id=notification_id, recipient=request.user
    )

    notification.delete()

    return Response(
        {"detail": "Notification deleted successfully."},
        status=status.HTTP_204_NO_CONTENT,
    )


@extend_schema(
    tags=["Notifications"],
    summary="Delete all read notifications",
    description="Delete all notifications that have been marked as read for the authenticated user.",
    responses={
        200: OpenApiTypes.OBJECT,
        401: ErrorResponseSerializer,
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_all_read_notifications(request):
    """
    Delete all read notifications for the user.

    DELETE /notifications/clear-read/
    """
    count, _ = Notification.objects.filter(
        recipient=request.user, is_read=True
    ).delete()

    return Response(
        {"detail": f"{count} notification(s) deleted."},
        status=status.HTTP_200_OK,
    )


@extend_schema(
    tags=["Notifications"],
    summary="Get notification statistics",
    description="Get statistics about the user's notifications, including total count, unread count, read count, and counts by notification type.",
    responses={
        200: OpenApiTypes.OBJECT,
        401: ErrorResponseSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_stats(request):
    """
    Get notification statistics for the user.

    GET /notifications/stats/
    """
    user = request.user

    total = Notification.objects.filter(recipient=user).count()
    unread = Notification.objects.filter(recipient=user, is_read=False).count()
    read = total - unread

    # Count by type
    type_counts = {}
    for choice in Notification.NotificationType.choices:
        type_key = choice[0]
        count = Notification.objects.filter(
            recipient=user, notification_type=type_key
        ).count()
        if count > 0:
            type_counts[type_key] = count

    return Response(
        {
            "total": total,
            "unread": unread,
            "read": read,
            "by_type": type_counts,
        },
        status=status.HTTP_200_OK,
    )
