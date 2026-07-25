---
features:
  - id: "jwt-auth-oauth"
    title: "JWT authentication & social login"
    description: "Email/password registration and login with SimpleJWT access/refresh tokens, rotation, blacklist on logout, plus Google and GitHub OAuth via django-allauth and dj-rest-auth."
    icon: "shield-lock"
    category: "authentication"
    status: "stable"
    highlights:
      - "POST /api/v2/auth/login/ and /register/ with AuthActionsThrottle (10/min)"
      - "OAuth at /api/v2/auth/oauth/google/ and /github/"
      - "Token refresh at /api/v2/auth/token/refresh/"
    techStack:
      - "djangorestframework-simplejwt"
      - "django-allauth"
      - "dj-rest-auth"
      - "apps/users"
    metrics:
      - label: "Access token TTL"
        value: "60 min"
        trend: "stable"
        icon: "clock"
      - label: "Refresh token TTL"
        value: "7 days"
        trend: "stable"
        icon: "refresh"
    codeSnippet:
      language: "python"
      filename: "apps/users/views/auth_views.py"
      code: |
        class LoginView(generics.GenericAPIView):
            permission_classes = [AllowAny]
            throttle_classes = [AuthActionsThrottle]

            def post(self, request, *args, **kwargs):
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                return Response(
                    {"tokens": serializer.data["tokens"], "user": serializer.data["user"]},
                    status=status.HTTP_200_OK,
                )

  - id: "events-lifecycle"
    title: "Event lifecycle & discovery"
    description: "Full event CRUD with draft/publish/cancel, public vs private events, categories, tags, recurrence rules, staff roles, favorites, and filtered list for discovery."
    icon: "calendar-star"
    category: "api"
    status: "stable"
    highlights:
      - "EventViewSet with slug lookup and publish/cancel actions"
      - "Role matrix: host, co-host, speaker, volunteer, moderator"
      - "ReadHeavyThrottle on list; WriteSensitiveThrottle on mutations"
    techStack:
      - "apps/events"
      - "django-filter"
      - "drf-spectacular"
    metrics:
      - label: "Staff roles"
        value: "5"
        trend: "stable"
        icon: "users"

  - id: "organizations-multitenancy"
    title: "Organizations & memberships"
    description: "Multi-tenant organizations with owner/admin/manager/member roles, invites, join/leave, and listing events owned by the organization."
    icon: "building"
    category: "api"
    status: "beta"
    highlights:
      - "Slug-based organization URLs"
      - "Member invite and role update endpoints"
      - "Org managers can administer org-linked events via permissions"
    techStack:
      - "apps/organizations"
    metrics:
      - label: "Membership roles"
        value: "4"
        trend: "stable"
        icon: "badge"

  - id: "registrations-ticketing"
    title: "Ticket tiers & registrations"
    description: "Per-event ticket tiers (price, capacity, visibility) and user registrations with status workflow, waitlist, cancellation, and host check-in."
    icon: "ticket"
    category: "api"
    status: "stable"
    highlights:
      - "POST /api/v2/events/{slug}/register/ with RegistrationThrottle"
      - "Host-only registration list and status updates"
      - "Check-in endpoint for door staff"
    techStack:
      - "apps/registrations"
      - "apps/events"
    metrics:
      - label: "Registration states"
        value: "5+"
        trend: "stable"
        icon: "list"
    codeSnippet:
      language: "python"
      filename: "apps/registrations/views/registration_views.py"
      code: |
        class EventRegistrationsListView(generics.ListAPIView):
            permission_classes = [IsAuthenticated, IsEventHost]
            throttle_classes = [ReadHeavyThrottle]

  - id: "comments-engagement"
    title: "Comments, likes & moderation"
    description: "Threaded comments on events with author edit/delete, likes, and host/moderator pin/unpin for announcements."
    icon: "chat-dots"
    category: "messaging"
    status: "stable"
    highlights:
      - "Soft delete for comments"
      - "CanCommentOnEvent permission"
      - "Signals hook for future notification tasks"
    techStack:
      - "apps/comments"

  - id: "notifications-inapp"
    title: "In-app notifications"
    description: "User notification inbox with read/mark-all-read, stats, and delete; HTML email templates under apps/notifications/templates/."
    icon: "bell"
    category: "messaging"
    status: "stable"
    highlights:
      - "Prefix /api/v2/notifications/"
      - "mark-all-read and clear-read bulk actions"
      - "Notification services for domain events"
    techStack:
      - "apps/notifications"
      - "Celery (email tasks in users app)"

  - id: "redis-prefix-cache"
    title: "Redis cache & Celery with key prefix"
    description: "django-redis for cache and rate-limit counters; Celery broker and result backend on Redis with REDIS_KEY_PREFIX social-events-api: to avoid collisions on shared Upstash."
    icon: "database"
    category: "caching"
    status: "stable"
    highlights:
      - "KEY_PREFIX on django-redis"
      - "global_keyprefix on Celery broker and results"
      - "TLS rediss:// URL for Upstash in production .env"
    techStack:
      - "django-redis"
      - "redis 5.2"
      - "celery 5.4"
    metrics:
      - label: "Key prefix"
        value: "social-events-api:"
        trend: "stable"
        icon: "key"

  - id: "rate-limiting-layers"
    title: "Layered rate limiting"
    description: "Global RateLimitMiddleware (200/min anon IP, 1000/min auth user) plus DRF scoped throttles for auth, writes, registration, and check-in."
    icon: "speedometer"
    category: "performance"
    status: "stable"
    highlights:
      - "Fail-open if Redis unavailable (middleware)"
      - "X-RateLimit-* response headers"
      - "Exempt /api/schema/ and /api/docs/"
    techStack:
      - "common/throttling.py"
    codeSnippet:
      language: "python"
      filename: "common/throttling.py"
      code: |
        class RateLimitMiddleware:
            ANON_LIMIT = (200, 60)
            AUTH_LIMIT = (1000, 60)
            EXEMPT_PATHS = {"/health/", "/api/schema/", "/api/docs/"}

  - id: "audit-logging"
    title: "Request audit logging"
    description: "AuditLogMiddleware records method, path, user, duration, and sanitized JSON body (passwords/tokens redacted) to the audit logger."
    icon: "clipboard-list"
    category: "monitoring"
    status: "stable"
    highlights:
      - "SENSITIVE_FIELDS masking in common/audit_log.py"
      - "AuditLog model in common/models.py for domain audits"
    techStack:
      - "common/audit_log.py"

  - id: "openapi-docker-cloud"
    title: "OpenAPI docs & cloud deploy"
    description: "drf-spectacular schema and Swagger UI; Docker multi-stage image with Gunicorn; production compose runs web only against RDS and Upstash."
    icon: "cloud"
    category: "integration"
    status: "stable"
    highlights:
      - "GET /api/schema/ and /api/docs/"
      - "docker-compose.prod.yml — EC2 single container"
      - "USE_S3 for media when enabled in production"
    techStack:
      - "drf-spectacular"
      - "Docker"
      - "Gunicorn"
      - "AWS RDS"
      - "Upstash"
    metrics:
      - label: "Documented OpenAPI"
        value: "1.0.0"
        trend: "stable"
        icon: "tag"
---

# Project Features

> **Stable:** Events, registrations, comments, notifications, auth, Redis prefix, rate limits, OpenAPI.

> **Beta:** Organization endpoints need permission hardening; some Celery email hooks are TODO in signals.

> **Dangerous:** `/api/task-revoke/` and `/api/celery-health/` are AllowAny—restrict or protect behind admin network in production.

> **Before production:** Set `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, real `SECRET_KEY`, Upstash `rediss://` URLs, RDS `DATABASE_URL`, run Celery worker on EC2 (not only web container), enable `USE_S3` for durable media.
