#!/bin/bash

# Celery Beat Startup Script (for periodic tasks)
# Usage: ./start_celery_beat.sh

echo "⏰ Starting Celery Beat Scheduler..."
echo "===================================="

# Activate virtual environment if exists
if [ -d "env" ]; then
    source env/bin/activate
fi

# Set Django settings module (use env var or default to development)
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings.development}

# Start Celery Beat
celery -A config beat \
    --loglevel=info \
    --logfile=logs/celery_beat.log \
    --pidfile=logs/celery_beat.pid

echo "❌ Celery beat stopped"
