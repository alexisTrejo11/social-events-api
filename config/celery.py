"""Celery configuration for async task processing."""

import os
import logging
from celery import Celery
from celery.signals import (
    task_prerun,
    task_postrun,
    task_failure,
    task_success,
    task_retry,
)

logger = logging.getLogger(__name__)

# Set default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Create Celery app
app = Celery("social_events_api")

# Load config from Django settings with CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Also discover tasks from common module (not in INSTALLED_APPS)
app.autodiscover_tasks(["common"])
app.autodiscover_tasks(["apps"])

# Additional Celery configuration
app.conf.update(
    task_track_started=True,  # Track when tasks start
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # Soft limit before hard kill
    worker_prefetch_multiplier=1,  # One task at a time
    worker_max_tasks_per_child=1000,  # Restart worker after N tasks
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,  # Reject task if worker dies
)


# =============================================================================
# CELERY SIGNALS FOR LOGGING & MONITORING
# =============================================================================


@task_prerun.connect
def task_prerun_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, **extra
):
    """Log when a task starts."""
    logger.info(
        f"📋 Task Started: {task.name} [ID: {task_id}] | Args: {args} | Kwargs: {kwargs}"
    )


@task_postrun.connect
def task_postrun_handler(
    sender=None, task_id=None, task=None, retval=None, state=None, **extra
):
    """Log when a task finishes."""
    logger.info(
        f"✅ Task Finished: {task.name} [ID: {task_id}] | State: {state} | Result: {retval}"
    )


@task_success.connect
def task_success_handler(sender=None, result=None, **extra):
    """Log successful task completion."""
    logger.info(f"🎉 Task Success: {sender.name} | Result: {result}")


@task_failure.connect
def task_failure_handler(
    sender=None, task_id=None, exception=None, traceback=None, **extra
):
    """Log task failures."""
    logger.error(
        f"❌ Task Failed: {sender.name} [ID: {task_id}] | Exception: {exception}",
        exc_info=True,
        extra={"traceback": traceback},
    )


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, **extra):
    """Log task retries."""
    logger.warning(f"🔄 Task Retry: {sender.name} [ID: {task_id}] | Reason: {reason}")


@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery configuration."""
    logger.info(f"Debug task executed: Request: {self.request!r}")
    return {"status": "success", "message": "Celery is working!"}
