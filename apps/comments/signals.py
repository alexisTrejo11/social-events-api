"""Comment signals.

This module contains signal handlers for comment-related events.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from apps.comments.models import Comment


@receiver(post_save, sender=Comment)
def comment_created(sender, instance, created, **kwargs):
    """
    Handle actions after a comment is created.

    TODO: Implement the following:
    - Notify event organizer of new comment
    - Notify parent comment author if it's a reply
    - Update event statistics/cache
    """
    if created:
        # Placeholder for notification
        # from apps.comments.tasks import notify_new_comment
        # notify_new_comment.delay(instance.id)
        pass


@receiver(post_save, sender=Comment)
def comment_liked(sender, instance, **kwargs):
    """
    Handle actions when a comment receives a like.

    TODO: Implement the following:
    - Notify comment author when their comment is liked
    - Track engagement metrics
    """
    # This would typically be triggered by a m2m_changed signal on the likes field
    pass


@receiver(pre_delete, sender=Comment)
def comment_deleted(sender, instance, **kwargs):
    """
    Handle actions before a comment is hard deleted.

    Note: We use soft delete (is_deleted=True), so this should rarely fire.
    TODO: Log hard deletions for audit purposes
    """
    pass
