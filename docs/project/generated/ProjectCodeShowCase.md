# Code Showcase

## Redis key prefix for shared Upstash

Namespaces django-redis cache keys and Celery broker/result keys so multiple services can share one Upstash instance safely.

**Category:** infrastructure | **Duration:** 3 min read | **Tags:** redis, upstash, celery

### base.py

**Path:** `config/settings/base.py`

REDIS_KEY_PREFIX defaults to social-events-api: and applies to cache KEY_PREFIX and Celery global_keyprefix.

```python
REDIS_KEY_PREFIX = env("REDIS_KEY_PREFIX")

def redis_cache_options(**extra):
    return {
        "CLIENT_CLASS": "django_redis.client.DefaultClient",
        "KEY_PREFIX": REDIS_KEY_PREFIX,
        **extra,
    }

CELERY_BROKER_TRANSPORT_OPTIONS = {"global_keyprefix": REDIS_KEY_PREFIX}
CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS = {"global_keyprefix": REDIS_KEY_PREFIX}
```

## Event role & organization manager checks

Permission helpers combine per-event roles (host, moderator) with organization membership for cross-event administration.

**Category:** security | **Duration:** 4 min read | **Tags:** events, permissions, organizations

### permissions.py

**Path:** `apps/events/permissions.py`

Org owners/admins/managers can manage events linked to their organization even if not the original organizer.

```python
def has_event_role(user, event, *roles) -> bool:
    if not user or not user.is_authenticated:
        return False
    event_role = get_event_role(user, event)
    return event_role is not None and event_role.role in roles

def is_event_org_manager(user, event) -> bool:
    if not event.organization:
        return False
    membership = OrganizationMembership.objects.get(
        user=user, organization=event.organization
    )
    return membership.role in (
        OrganizationMembership.Role.OWNER,
        OrganizationMembership.Role.ADMIN,
        OrganizationMembership.Role.MANAGER,
    )
```

## Global rate limit middleware

IP-based limits for anonymous clients and user-id limits for authenticated users, backed by Django cache (Redis in production).

**Category:** performance | **Duration:** 3 min read | **Tags:** throttling, redis

### throttling.py

**Path:** `common/throttling.py`

Fails open on Redis errors so cache outages do not hard-down the API.

```python
class RateLimitMiddleware:
    ANON_LIMIT = (200, 60)
    AUTH_LIMIT = (1000, 60)
    EXEMPT_PATHS = {"/health/", "/api/schema/", "/api/docs/"}

    def __call__(self, request):
        if request.path in self.EXEMPT_PATHS:
            return self.get_response(request)
        limit, window = self._get_limit(request)
        allowed, remaining, reset_at = self._check_limit(...)
        if not allowed:
            return JsonResponse({"error": {"code": "rate_limit_exceeded", ...}}, status=429)
```

## Audit log with sensitive field redaction

Middleware logs request metadata and JSON bodies with passwords and tokens masked.

**Category:** security | **Duration:** 2 min read | **Tags:** audit, logging

### audit_log.py

**Path:** `common/audit_log.py`

SENSITIVE_FIELDS set prevents credential leakage into log aggregators on EC2.

```python
SENSITIVE_FIELDS = {"password", "token", "access", "refresh"}

def sanitize_data(data):
    if not isinstance(data, dict):
        return None
    return {
        key: ("***" if key.lower() in SENSITIVE_FIELDS else value)
        for key, value in data.items()
    }
```

## Celery app with task lifecycle logging

Celery autodiscovers tasks from apps and common; signal handlers log task start, success, failure, and retry.

**Category:** messaging | **Duration:** 3 min read | **Tags:** celery, async

### celery.py

**Path:** `config/celery.py`

Worker should run on EC2 alongside web container when email notifications must be reliable.

```python
app = Celery("social_events_api")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.autodiscover_tasks(["common"])
app.autodiscover_tasks(["apps"])

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **extra):
    logger.info(f"Task Started: {task.name} [ID: {task_id}]")
```

## Additional notes

# Code Showcase

> Snippets are taken from the repository; open full files for imports, error handling, and tests.

> **Recommended reading order:** Redis prefix → event permissions → rate limit middleware → audit sanitization → Celery setup.

> **Warning:** Register a `/health/` route if load balancers should use it—middleware exempts `/health/` but `config/urls.py` does not define it yet.

