import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.users.models import UserPreferences

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """
    Auto-create UserPreferences when a new user is created
    """
    if created:
        UserPreferences.objects.create(user=instance)
        logger.info(f"Created preferences for new user: {instance.email}")


@receiver(post_save, sender=User)
def save_user_preferences(sender, instance, **kwargs):
    """
    Ensure user preferences are saved when user is updated
    """
    if hasattr(instance, "preferences"):
        instance.preferences.save()
