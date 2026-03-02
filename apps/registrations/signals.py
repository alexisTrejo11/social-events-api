"""Registration signals.

This module contains signal handlers for registration-related events.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.registrations.models import Registration


@receiver(post_save, sender=Registration)
def registration_created(sender, instance, created, **kwargs):
    """
    Handle actions after a registration is created.

    TODO: Implement the following:
    - Send confirmation email to attendee
    - Notify event organizer of new registration
    - Update event statistics/cache
    """
    if created:
        # Placeholder for email notification
        # from apps.registrations.tasks import send_registration_confirmation
        # send_registration_confirmation.delay(instance.id)
        pass


@receiver(pre_save, sender=Registration)
def registration_status_changed(sender, instance, **kwargs):
    """
    Handle actions when registration status changes.

    TODO: Implement the following:
    - Send email when status changes to CONFIRMED
    - Send email when moved to WAITLISTED
    - Send notification when registration is cancelled
    """
    if instance.pk:
        try:
            old_instance = Registration.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Status has changed
                # Placeholder for status change notifications
                # from apps.registrations.tasks import send_status_update_notification
                # send_status_update_notification.delay(instance.id, old_instance.status, instance.status)
                pass
        except Registration.DoesNotExist:
            pass


@receiver(post_save, sender=Registration)
def handle_waitlist_promotion(sender, instance, **kwargs):
    """
    Auto-promote waitlisted registrations when a spot opens up.

    TODO: Implement the following:
    - When a registration is cancelled, check if there are waitlisted registrations
    - Promote the first waitlisted registration to CONFIRMED
    - Send notification to promoted attendee
    """
    if instance.status == Registration.Status.CANCELLED:
        # Placeholder for waitlist promotion logic
        # event = instance.event
        # waitlisted = event.registrations.filter(
        #     status=Registration.Status.WAITLISTED
        # ).order_by('registered_at').first()
        #
        # if waitlisted and event.capacity:
        #     confirmed_count = event.registrations.filter(status=Registration.Status.CONFIRMED).count()
        #     if confirmed_count < event.capacity:
        #         waitlisted.status = Registration.Status.CONFIRMED
        #         waitlisted.save()
        pass
