#!/bin/bash

# Stop all Celery processes
# Usage: ./stop_celery.sh

echo "🛑 Stopping Celery processes..."

# Kill worker
if [ -f "logs/celery_worker.pid" ]; then
    kill -TERM $(cat logs/celery_worker.pid) 2>/dev/null
    rm logs/celery_worker.pid
    echo "✅ Celery worker stopped"
else
    echo "ℹ️  No worker PID file found"
fi

# Kill beat
if [ -f "logs/celery_beat.pid" ]; then
    kill -TERM $(cat logs/celery_beat.pid) 2>/dev/null
    rm logs/celery_beat.pid
    echo "✅ Celery beat stopped"
else
    echo "ℹ️  No beat PID file found"
fi

# Cleanup
pkill -f 'celery worker' 2>/dev/null
pkill -f 'celery beat' 2>/dev/null

echo "✅ Done!"
