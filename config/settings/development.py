"""
Development settings - uses SQLite, debug enabled, console email backend.
This is the default configuration when running locally with 'python manage.py runserver'.
"""

from .base import *

# Override DEBUG for development
DEBUG = True

# Development allowed hosts
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "0.0.0.0"])

# SQLite Database for development (override base DATABASE_URL)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Console email backend for development (emails print to console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Redis cache configuration for development (optional, can be disabled if not needed)
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{env('REDIS_HOST', default='localhost')}:{env('REDIS_PORT', default='6379')}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 50,
                "retry_on_timeout": True,
            },
        },
    }
}

# Celery broker for development
CELERY_BROKER_URL = f"redis://{env('REDIS_HOST', default='localhost')}:{env('REDIS_PORT', default='6379')}/0"
CELERY_RESULT_BACKEND = f"redis://{env('REDIS_HOST', default='localhost')}:{env('REDIS_PORT', default='6379')}/1"


# Development-specific logging (more verbose)
LOGGING["loggers"][""]["level"] = "DEBUG"
LOGGING["loggers"]["apps"]["level"] = "DEBUG"
LOGGING["loggers"]["common"]["level"] = "DEBUG"

# CORS for development (if using django-cors-headers)
CORS_ALLOW_ALL_ORIGINS = True

print("Running in DEVELOPMENT mode with SQLite")
