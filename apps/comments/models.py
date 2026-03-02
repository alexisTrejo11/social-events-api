from django.db import models
from django.conf import settings

from apps.events.models import Event


class Comment(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    content = models.TextField()
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="liked_comments", blank=True
    )
    is_pinned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(
        default=False
    )  # soft delete to preserve thread structure
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Comment by {self.author.get_full_name()} on {self.event.title}"
