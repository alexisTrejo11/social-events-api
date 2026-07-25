"""Comment views."""

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from apps.comments.models import Comment
from apps.comments.serializers import (
    CommentSerializer,
    CommentListSerializer,
    CommentCreateUpdateSerializer,
)
from apps.comments.permissions import (
    IsCommentAuthorOrReadOnly,
    CanModerateComment,
    CanCommentOnEvent,
)
from apps.events.models import Event
from common.serializers import (
    ErrorResponseSerializer,
    MessageResponseSerializer,
    ValidationErrorSerializer,
)
from common.throttling import ReadHeavyThrottle, WriteStandardThrottle


@extend_schema(
    tags=["Comments"],
    summary="List and create comments for an event",
    description="GET: List all top-level comments for an event (nested replies included in response). "
    "POST: Create a new top-level comment or reply to an existing comment.",
    responses={
        200: CommentListSerializer(many=True),
        201: CommentSerializer,
        400: ValidationErrorSerializer,
        401: ErrorResponseSerializer,
        403: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
class EventCommentsListCreateView(generics.ListCreateAPIView):
    """
    List and create comments for an event.

    GET /events/{slug}/comments/ - List all top-level comments (replies are nested)
    POST /events/{slug}/comments/ - Create a new comment or reply
    """

    serializer_class = CommentListSerializer
    throttle_classes = [ReadHeavyThrottle, WriteStandardThrottle]

    def get_event(self):
        """Get event from URL parameter and cache it."""
        if not hasattr(self, "_event"):
            event_slug = self.kwargs.get("event_slug")
            self._event = get_object_or_404(Event, slug=event_slug, is_deleted=False)
        return self._event

    def get_queryset(self):
        """Return top-level comments for the event (parent=None)."""
        event = self.get_event()
        # Only return top-level comments, replies are nested via serializer
        return (
            Comment.objects.filter(event=event, parent__isnull=True)
            .select_related("author")
            .prefetch_related("likes", "replies")
            .order_by("-is_pinned", "-created_at")
        )

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.request.method == "POST":
            return CommentCreateUpdateSerializer
        return CommentListSerializer

    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.request.method == "POST":
            return [IsAuthenticated(), CanCommentOnEvent()]
        return [IsAuthenticatedOrReadOnly()]

    def get_serializer_context(self):
        """Include the event so create/update serializers can attach it."""
        context = super().get_serializer_context()
        context["event"] = self.get_event()
        return context

    def perform_create(self, serializer):
        """Create comment with event and author (from serializer context)."""
        serializer.save()

        # TODO: Send notification to event organizer
        # from apps.comments.tasks import notify_new_comment
        # notify_new_comment.delay(comment.id)


@extend_schema(
    tags=["Comments"],
    summary="Update a comment",
    description="Update your own comment content. Only the comment author can perform this action.",
    request=CommentCreateUpdateSerializer,
    responses={
        200: CommentSerializer,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
        403: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsCommentAuthorOrReadOnly])
def update_comment(request, event_slug, comment_id):
    """
    Update own comment.

    PATCH /events/{slug}/comments/{id}/
    """
    event = get_object_or_404(Event, slug=event_slug, is_deleted=False)
    comment = get_object_or_404(Comment, id=comment_id, event=event)

    # Check permission
    permission = IsCommentAuthorOrReadOnly()
    if not permission.has_object_permission(request, None, comment):
        error_data = {"detail": "You can only edit your own comments."}
        return Response(
            ErrorResponseSerializer(error_data).data,
            status=status.HTTP_403_FORBIDDEN,
        )

    # Don't allow editing deleted comments
    if comment.is_deleted:
        error_data = {"detail": "Cannot edit a deleted comment."}
        return Response(
            ErrorResponseSerializer(error_data).data,
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = CommentCreateUpdateSerializer(
        comment,
        data=request.data,
        partial=True,
        context={"request": request, "event": event},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        CommentSerializer(comment, context={"request": request}).data,
        status=status.HTTP_200_OK,
    )


@extend_schema(
    tags=["Comments"],
    summary="Delete a comment",
    description="Soft delete your own comment. The comment is marked as deleted but not removed from the database.",
    responses={
        204: None,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
        403: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsCommentAuthorOrReadOnly])
def delete_comment(request, event_slug, comment_id):
    """
    Soft delete own comment.

    DELETE /events/{slug}/comments/{id}/
    """
    event = get_object_or_404(Event, slug=event_slug, is_deleted=False)
    comment = get_object_or_404(Comment, id=comment_id, event=event)

    # Check permission
    permission = IsCommentAuthorOrReadOnly()
    if not permission.has_object_permission(request, None, comment):
        error_data = {"detail": "You can only delete your own comments."}
        return Response(
            ErrorResponseSerializer(error_data).data,
            status=status.HTTP_403_FORBIDDEN,
        )

    # Don't allow deleting already deleted comments
    if comment.is_deleted:
        error_data = {"detail": "Comment is already deleted."}
        return Response(
            ErrorResponseSerializer(error_data).data,
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Soft delete
    comment.is_deleted = True
    comment.save(update_fields=["is_deleted"])

    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Comments"],
    summary="Like a comment",
    description="Add your like to a comment. Cannot like deleted comments or like the same comment twice.",
    responses={
        200: MessageResponseSerializer,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def like_comment(request, event_slug, comment_id):
    """
    Like a comment.

    POST /events/{slug}/comments/{id}/like/
    """
    event = get_object_or_404(Event, slug=event_slug, is_deleted=False)
    comment = get_object_or_404(Comment, id=comment_id, event=event)

    # Don't allow liking deleted comments
    if comment.is_deleted:
        error_data = {"detail": "Cannot like a deleted comment."}
        return Response(
            ErrorResponseSerializer(error_data).data,
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if already liked
    if comment.likes.filter(id=request.user.id).exists():
        error_data = {"detail": "You have already liked this comment."}
        return Response(
            ErrorResponseSerializer(error_data).data,
            status=status.HTTP_400_BAD_REQUEST,
        )

    comment.likes.add(request.user)

    return Response(
        MessageResponseSerializer({"message": "Comment liked successfully."}).data,
        status=status.HTTP_200_OK,
    )


@extend_schema(
    tags=["Comments"],
    summary="Unlike a comment",
    description="Remove your like from a comment.",
    responses={
        200: MessageResponseSerializer,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def unlike_comment(request, event_slug, comment_id):
    """
    Unlike a comment.

    DELETE /events/{slug}/comments/{id}/like/
    """
    event = get_object_or_404(Event, slug=event_slug, is_deleted=False)
    comment = get_object_or_404(Comment, id=comment_id, event=event)

    # Check if not liked
    if not comment.likes.filter(id=request.user.id).exists():
        error_data = {"detail": "You have not liked this comment."}
        return Response(
            ErrorResponseSerializer(error_data).data,
            status=status.HTTP_400_BAD_REQUEST,
        )

    comment.likes.remove(request.user)

    return Response(
        MessageResponseSerializer({"message": "Comment unliked successfully."}).data,
        status=status.HTTP_200_OK,
    )


@extend_schema(
    tags=["Comments"],
    summary="Pin a comment",
    description="Pin a top-level comment to the top of the comment list. Only event organizers and hosts can perform this action.",
    responses={
        200: CommentSerializer,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
        403: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, CanModerateComment])
def pin_comment(request, event_slug, comment_id):
    """
    Pin a comment (organizer/host only).

    POST /events/{slug}/comments/{id}/pin/
    """
    event = get_object_or_404(Event, slug=event_slug, is_deleted=False)
    comment = get_object_or_404(Comment, id=comment_id, event=event)

    # Check permission
    permission = CanModerateComment()
    if not permission.has_object_permission(request, None, comment):
        error_data = {
            "detail": "You do not have permission to moderate comments on this event."
        }
        return Response(
            ErrorResponseSerializer(error_data).data,
            status=status.HTTP_403_FORBIDDEN,
        )

    # Don't allow pinning deleted comments
    if comment.is_deleted:
        error_data = {"detail": "Cannot pin a deleted comment."}
        return Response(
            ErrorResponseSerializer(error_data).data,
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Don't allow pinning replies
    if comment.parent is not None:
        error_data = {
            "detail": "Cannot pin a reply. Only top-level comments can be pinned."
        }
        return Response(
            ErrorResponseSerializer(error_data).data,
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if already pinned
    if comment.is_pinned:
        error_data = {"detail": "Comment is already pinned."}
        return Response(
            ErrorResponseSerializer(error_data).data,
            status=status.HTTP_400_BAD_REQUEST,
        )

    comment.is_pinned = True
    comment.save(update_fields=["is_pinned"])

    return Response(
        CommentSerializer(comment, context={"request": request}).data,
        status=status.HTTP_200_OK,
    )


@extend_schema(
    tags=["Comments"],
    summary="Unpin a comment",
    description="Remove a pinned comment from the pinned position. Only event organizers and hosts can perform this action.",
    responses={
        200: MessageResponseSerializer,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
        403: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated, CanModerateComment])
def unpin_comment(request, event_slug, comment_id):
    """
    Unpin a comment (organizer/host only).

    DELETE /events/{slug}/comments/{id}/pin/
    """
    event = get_object_or_404(Event, slug=event_slug, is_deleted=False)
    comment = get_object_or_404(Comment, id=comment_id, event=event)

    # Check permission
    permission = CanModerateComment()
    if not permission.has_object_permission(request, None, comment):
        error_data = {
            "detail": "You do not have permission to moderate comments on this event."
        }
        return Response(
            ErrorResponseSerializer(error_data).data,
            status=status.HTTP_403_FORBIDDEN,
        )

    # Check if not pinned
    if not comment.is_pinned:
        error_data = {"detail": "Comment is not pinned."}
        return Response(
            ErrorResponseSerializer(error_data).data,
            status=status.HTTP_400_BAD_REQUEST,
        )

    comment.is_pinned = False
    comment.save(update_fields=["is_pinned"])

    return Response(
        MessageResponseSerializer({"message": "Comment unpinned successfully."}).data,
        status=status.HTTP_200_OK,
    )
