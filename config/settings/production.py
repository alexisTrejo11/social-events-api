"""
Production settings - uses PostgreSQL, debug disabled, Docker environment.
This configuration is used when running with Docker Compose.
"""

from .base import *

# Production security settings
DEBUG = False

# Allowed hosts from environment
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost"])

# PostgreSQL Database for production
# Expects DATABASE_URL format: postgresql://user:password@host:port/dbname
# Or individual POSTGRES_* environment variables
if env("DATABASE_URL", default="").startswith("postgresql"):
    DATABASES = {"default": env.db("DATABASE_URL")}
else:
    # Build from individual environment variables (Docker Compose style)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB", default="social_events_db"),
            "USER": env("POSTGRES_USER", default="postgres"),
            "PASSWORD": env("POSTGRES_PASSWORD", default="postgres"),
            "HOST": env("POSTGRES_HOST", default="postgres"),
            "PORT": env("POSTGRES_PORT", default="5432"),
            "CONN_MAX_AGE": 600,
            "OPTIONS": {
                "connect_timeout": 10,
            },
        }
    }

# Redis cache configuration for production
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{env('REDIS_HOST', default='redis')}:{env('REDIS_PORT', default='6379')}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 50,
                "retry_on_timeout": True,
            },
        },
    }
}

# Celery broker for production
CELERY_BROKER_URL = f"redis://{env('REDIS_HOST', default='redis')}:{env('REDIS_PORT', default='6379')}/0"
CELERY_RESULT_BACKEND = f"redis://{env('REDIS_HOST', default='redis')}:{env('REDIS_PORT', default='6379')}/1"

# Email backend for production (use SMTP)
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)

# Security settings for production
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HSTS settings (enable after testing)
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# Static and media files (use WhiteNoise or S3 in production)
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"

# AWS S3 Configuration (optional, for media storage)
USE_S3 = env.bool("USE_S3", default=False)
if USE_S3:
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    AWS_DEFAULT_ACL = "public-read"

    # Media files (uploads)
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"

# Production logging (less verbose)
LOGGING["loggers"][""]["level"] = "INFO"
LOGGING["loggers"]["apps"]["level"] = "INFO"
LOGGING["loggers"]["common"]["level"] = "INFO"
LOGGING["loggers"]["django"]["level"] = "WARNING"

print("Running in PRODUCTION mode with PostgreSQL")
