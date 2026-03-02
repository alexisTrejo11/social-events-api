from rest_framework.decorators import api_view
from rest_framework.response import Response
from common.tasks import test_task, long_running_task
import logging


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from celery.result import AsyncResult
from config.celery import app as celery_app


logger = logging.getLogger(__name__)


@api_view(["GET"])
def test(request, format=None):
    """Test endpoint with async task execution."""
    logger.info("Test API endpoint hit!")
    logger.debug(f"Request from: {request.META.get('REMOTE_ADDR')}")

    # Get execution mode from query params
    mode = request.GET.get("mode", "sync")  # sync or async

    if mode == "async":
        # Execute asynchronously with Celery
        task = test_task.delay()
        logger.info(f"📤 Task enqueued: {task.id}")

        return Response(
            {
                "message": "Task enqueued successfully!",
                "task_id": task.id,
                "status_url": f"/api/task-status/{task.id}/",
                "mode": "async",
                "note": "Check logs to see task execution",
            }
        )
    else:
        # Execute synchronously (for testing without Celery worker)
        logger.info("Running in synchronous mode")
        result = test_task()
        logger.info(f"Response sent: {result}")

        return Response(
            {
                "message": "API is working!",
                "task_result": result,
                "mode": "sync",
                "note": "Task executed synchronously (no Celery worker needed)",
            }
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def task_status(request, task_id):
    """
    Check the status of a Celery task.

    GET /api/task-status/{task_id}/

    Returns:
        - PENDING: Task is waiting to be executed
        - STARTED: Task has been started
        - PROGRESS: Task is in progress (custom state)
        - SUCCESS: Task completed successfully
        - FAILURE: Task failed
        - RETRY: Task is being retried
    """
    logger.info(f"🔍 Checking status for task: {task_id}")

    task = AsyncResult(task_id, app=celery_app)

    response_data = {
        "task_id": task_id,
        "status": task.state,
        "ready": task.ready(),
    }

    if task.state == "PENDING":
        response_data.update(
            {
                "message": "Task is waiting to be executed",
                "current": 0,
                "total": 1,
            }
        )
    elif task.state == "PROGRESS":
        response_data.update(
            {
                "message": "Task is in progress",
                "current": task.info.get("current", 0),
                "total": task.info.get("total", 1),
                "progress_status": task.info.get("status", ""),
            }
        )
    elif task.state == "SUCCESS":
        response_data.update(
            {
                "message": "Task completed successfully",
                "result": task.result,
            }
        )
    elif task.state == "FAILURE":
        response_data.update(
            {
                "message": "Task failed",
                "error": str(task.info),
            }
        )
    elif task.state == "RETRY":
        response_data.update(
            {
                "message": "Task is being retried",
                "retry_count": task.info.get("retries", 0),
            }
        )
    else:
        response_data.update(
            {
                "message": f"Task state: {task.state}",
            }
        )

    logger.debug(f"📊 Task {task_id} - Status: {task.state}")

    return Response(response_data)


@api_view(["POST"])
@permission_classes([AllowAny])
def revoke_task(request, task_id):
    """
    Revoke/cancel a running task.

    POST /api/task-revoke/{task_id}/
    """
    logger.warning(f"⚠️  Revoking task: {task_id}")

    task = AsyncResult(task_id, app=celery_app)

    # Revoke the task (terminate=True will kill the worker process)
    terminate = request.data.get("terminate", False)
    task.revoke(terminate=terminate)

    return Response(
        {
            "message": f"Task {task_id} has been revoked",
            "task_id": task_id,
            "terminated": terminate,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def celery_health(request):
    """
    Check if Celery workers are running and healthy.

    GET /api/celery-health/
    """
    logger.info("Checking Celery health...")

    # Inspect active workers
    inspect = celery_app.control.inspect()

    # Get stats
    stats = inspect.stats()
    active_tasks = inspect.active()
    registered_tasks = inspect.registered()

    if stats is None:
        # No workers are running
        return Response(
            {
                "status": "error",
                "message": "No Celery workers are running",
                "workers": [],
                "recommendation": "Start a worker with: celery -A config worker -l info",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    worker_info = []
    for worker_name, worker_stats in stats.items():
        worker_info.append(
            {
                "name": worker_name,
                "status": "active",
                "pool": worker_stats.get("pool", {}).get("implementation", "N/A"),
                "max_concurrency": worker_stats.get("pool", {}).get(
                    "max-concurrency", 0
                ),
            }
        )

    return Response(
        {
            "status": "healthy",
            "message": f"{len(worker_info)} worker(s) running",
            "workers": worker_info,
            "active_tasks": (
                len(active_tasks.get(list(active_tasks.keys())[0], []))
                if active_tasks
                else 0
            ),
            "registered_tasks_count": (
                len(registered_tasks.get(list(registered_tasks.keys())[0], []))
                if registered_tasks
                else 0
            ),
        }
    )
