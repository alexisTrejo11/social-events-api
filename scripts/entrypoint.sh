#!/bin/bash

set -e

# TODO: Fix ENV does not load from .env file issue
# Wait until PostgreSQL is ready
echo "Waiting for PostgreSQL to be ready..."
while ! nc -z ${POSTGRES_HOST:-db} ${POSTGRES_PORT:-5432}; do
  echo "Waiting for PostgreSQL at ${POSTGRES_HOST:-db}:${POSTGRES_PORT:-5432}..."
  sleep 1
done
echo "PostgreSQL is ready!"

# Wait until Redis is ready
echo "Waiting for Redis to be ready..."
if  [ -n "${REDIS_HOST}" ] && [ -n "${REDIS_PORT}" ]; then
  while ! nc -z ${REDIS_HOST} ${REDIS_PORT}; do
    echo "Waiting for Redis at ${REDIS_HOST}:${REDIS_PORT}..."
    sleep 1
  done
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear
echo "Static files collected."

# Apply Django migrations
echo "Applying Django migrations..."
python manage.py migrate --noinput
echo "Migrations applied."

# Create superuser if specified
if [ "$CREATE_SUPERUSER" = "true" ]; then
   echo "Creating superuser..."
   python manage.py shell -c "
from apps.users.models import User
if not User.objects.filter(username='${DJANGO_SUPERUSER_USERNAME:-admin}').exists():
   User.objects.create_superuser(
       username='${DJANGO_SUPERUSER_USERNAME:-admin}',
       email='${DJANGO_SUPERUSER_EMAIL:-admin@example.com}',
       password='${DJANGO_SUPERUSER_PASSWORD:-admin123}'
   )
   print('Superuser created!')
else:
   print('Superuser already exists')
" 2>/dev/null || echo "Note: Superuser creation skipped or failed"
fi

#  Start Celery worker and beat in background if Redis is configured
if [ -n "${REDIS_HOST}" ] && [ -n "${REDIS_PORT}" ]; then
  echo "Starting Celery worker and beat..."
  celery -A config worker --loglevel=info --logfile=logs/celery_worker.log --detach
  celery -A config beat --loglevel=info --logfile=logs/celery_beat.log --detach
  echo "Celery started in background"
fi

echo "Starting the application..."
exec python manage.py runserver 0.0.0.0:${PORT:-8000} --settings=config.settings.production
