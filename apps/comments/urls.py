"""Comments app URL configuration."""

from django.urls import path

from apps.comments.views import (
    EventCommentsListCreateView,
    update_comment,
    delete_comment,
    like_comment,
    unlike_comment,
    pin_comment,
    unpin_comment,
)

app_name = "comments"

urlpatterns = [
    # Event Comments
    path(
        "events/<slug:event_slug>/comments/",
        EventCommentsListCreateView.as_view(),
        name="event-comments-list-create",
    ),
    path(
        "events/<slug:event_slug>/comments/<int:comment_id>/",
        update_comment,
        name="update-comment",
    ),
    path(
        "events/<slug:event_slug>/comments/<int:comment_id>/",
        delete_comment,
        name="delete-comment",
    ),
    path(
        "events/<slug:event_slug>/comments/<int:comment_id>/like/",
        like_comment,
        name="like-comment",
    ),
    path(
        "events/<slug:event_slug>/comments/<int:comment_id>/like/",
        unlike_comment,
        name="unlike-comment",
    ),
    path(
        "events/<slug:event_slug>/comments/<int:comment_id>/pin/",
        pin_comment,
        name="pin-comment",
    ),
    path(
        "events/<slug:event_slug>/comments/<int:comment_id>/pin/",
        unpin_comment,
        name="unpin-comment",
    ),
]
