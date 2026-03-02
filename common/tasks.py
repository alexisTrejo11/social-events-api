"""Celery tasks for common operations and testing."""

from celery import shared_task
import time
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="common.test_task")
def test_task(self):
    """Test async task with progress tracking."""
    # Check if we're running in Celery context (async) or direct call (sync)
    task_id = self.request.id if hasattr(self.request, "id") else None
    is_async = task_id is not None

    logger.info(
        f"Starting test task... [Task ID: {task_id or 'SYNC'}] [Mode: {'ASYNC' if is_async else 'SYNC'}]"
    )

    # Simulate work with progress updates
    for i in range(1, 6):
        logger.info(f"Progress: {i}/5 (20% per step)")
        time.sleep(1)

        # Update task state only if running async
        if is_async:
            self.update_state(
                state="PROGRESS",
                meta={"current": i, "total": 5, "status": f"Step {i} of 5"},
            )

    logger.info(f"Test task completed! [Task ID: {task_id or 'SYNC'}]")
    return {
        "status": "success",
        "message": "Task completed successfully",
        "task_id": task_id,
        "steps_completed": 5,
        "mode": "async" if is_async else "sync",
    }


@shared_task(bind=True, name="common.long_running_task", max_retries=3)
def long_running_task(self, duration=10):
    """Simulate a long-running task with retry logic."""
    task_id = self.request.id if hasattr(self.request, "id") else None

    try:
        logger.info(f"Long task started: {duration}s [Task ID: {task_id or 'SYNC'}]")

        # Simulate work
        time.sleep(duration)

        logger.info(f" Long task finished [Task ID: {task_id or 'SYNC'}]")
        return {"status": "completed", "duration": duration, "task_id": task_id}

    except Exception as exc:
        logger.error(f"Task error: {exc}")
        # Retry only if running async (has valid task context)
        if task_id:
            raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))
        else:
            # In sync mode, just re-raise
            raise
