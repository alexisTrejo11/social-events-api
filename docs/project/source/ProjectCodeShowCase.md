---
codeExamples:
  - id: "redis-key-prefix"
    title: "Redis key prefix for shared Upstash"
    description: "Namespaces django-redis cache keys and Celery broker/result keys so multiple services can share one Upstash instance safely."
    category: "infrastructure"
    duration: "3 min read"
    views: 0
    tags:
      - "redis"
      - "upstash"
      - "celery"
    files:
      - name: "base.py"
        path: "config/settings/base.py"
        language: "python"
        highlighted: true
        explanation: "REDIS_KEY_PREFIX defaults to social-events-api: and applies to cache KEY_PREFIX and Celery global_keyprefix."
        content: |
          REDIS_KEY_PREFIX = env("REDIS_KEY_PREFIX")

          def redis_cache_options(**extra):
              return {
                  "CLIENT_CLASS": "django_redis.client.DefaultClient",
                  "KEY_PREFIX": REDIS_KEY_PREFIX,
                  **extra,
              }

          CELERY_BROKER_TRANSPORT_OPTIONS = {"global_keyprefix": REDIS_KEY_PREFIX}
          CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS = {"global_keyprefix": REDIS_KEY_PREFIX}

  - id: "event-permissions"
    title: "Event role & organization manager checks"
    description: "Permission helpers combine per-event roles (host, moderator) with organization membership for cross-event administration."
    category: "security"
    duration: "4 min read"
    views: 0
    tags:
      - "events"
      - "permissions"
      - "organizations"
    files:
      - name: "permissions.py"
        path: "apps/events/permissions.py"
        language: "python"
        highlighted: true
        explanation: "Org owners/admins/managers can manage events linked to their organization even if not the original organizer."
        content: |
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

  - id: "rate-limit-middleware"
    title: "Global rate limit middleware"
    description: "IP-based limits for anonymous clients and user-id limits for authenticated users, backed by Django cache (Redis in production)."
    category: "performance"
    duration: "3 min read"
    views: 0
    tags:
      - "throttling"
      - "redis"
    files:
      - name: "throttling.py"
        path: "common/throttling.py"
        language: "python"
        highlighted: true
        explanation: "Fails open on Redis errors so cache outages do not hard-down the API."
        content: |
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

  - id: "audit-sanitize"
    title: "Audit log with sensitive field redaction"
    description: "Middleware logs request metadata and JSON bodies with passwords and tokens masked."
    category: "security"
    duration: "2 min read"
    views: 0
    tags:
      - "audit"
      - "logging"
    files:
      - name: "audit_log.py"
        path: "common/audit_log.py"
        language: "python"
        highlighted: true
        explanation: "SENSITIVE_FIELDS set prevents credential leakage into log aggregators on EC2."
        content: |
          SENSITIVE_FIELDS = {"password", "token", "access", "refresh"}

          def sanitize_data(data):
              if not isinstance(data, dict):
                  return None
              return {
                  key: ("***" if key.lower() in SENSITIVE_FIELDS else value)
                  for key, value in data.items()
              }

  - id: "celery-signals"
    title: "Celery app with task lifecycle logging"
    description: "Celery autodiscovers tasks from apps and common; signal handlers log task start, success, failure, and retry."
    category: "messaging"
    duration: "3 min read"
    views: 0
    tags:
      - "celery"
      - "async"
    files:
      - name: "celery.py"
        path: "config/celery.py"
        language: "python"
        highlighted: true
        explanation: "Worker should run on EC2 alongside web container when email notifications must be reliable."
        content: |
          app = Celery("social_events_api")
          app.config_from_object("django.conf:settings", namespace="CELERY")
          app.autodiscover_tasks()
          app.autodiscover_tasks(["common"])
          app.autodiscover_tasks(["apps"])

          @task_prerun.connect
          def task_prerun_handler(sender=None, task_id=None, task=None, **extra):
              logger.info(f"Task Started: {task.name} [ID: {task_id}]")
---

# Code Showcase

> Snippets are taken from the repository; open full files for imports, error handling, and tests.

> **Recommended reading order:** Redis prefix → event permissions → rate limit middleware → audit sanitization → Celery setup.

> **Warning:** Register a `/health/` route if load balancers should use it—middleware exempts `/health/` but `config/urls.py` does not define it yet.
