#!/bin/bash

# Celery Worker Startup Script
# Usage: ./start_celery.sh

echo "🚀 Starting Celery Worker..."
echo "================================"

# Activate virtual environment if exists
if [ -d "env" ]; then
    source env/bin/activate
fi

# Set Django settings module (use env var or default to development)
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings.development}

# Start Celery worker with logging
celery -A config worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=1000 \
    --logfile=logs/celery_worker.log \
    --pidfile=logs/celery_worker.pid

echo "❌ Celery worker stopped"
