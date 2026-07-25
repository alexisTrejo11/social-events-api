# Project Features

## JWT authentication & social login

Email/password registration and login with SimpleJWT access/refresh tokens, rotation, blacklist on logout, plus Google and GitHub OAuth via django-allauth and dj-rest-auth.

| Property | Value |
| --- | --- |
| ID | jwt-auth-oauth |
| Category | authentication |
| Status | stable |
| Icon | shield-lock |

### Highlights

- POST /api/v2/auth/login/ and /register/ with AuthActionsThrottle (10/min)
- OAuth at /api/v2/auth/oauth/google/ and /github/
- Token refresh at /api/v2/auth/token/refresh/

### Tech stack

- djangorestframework-simplejwt
- django-allauth
- dj-rest-auth
- apps/users

### Metrics

| Label | Value | Trend |
| --- | --- | --- |
| Access token TTL | 60 min | stable |
| Refresh token TTL | 7 days | stable |

### Code snippet

_apps/users/views/auth_views.py_

```python
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
```

## Event lifecycle & discovery

Full event CRUD with draft/publish/cancel, public vs private events, categories, tags, recurrence rules, staff roles, favorites, and filtered list for discovery.

| Property | Value |
| --- | --- |
| ID | events-lifecycle |
| Category | api |
| Status | stable |
| Icon | calendar-star |

### Highlights

- EventViewSet with slug lookup and publish/cancel actions
- Role matrix: host, co-host, speaker, volunteer, moderator
- ReadHeavyThrottle on list; WriteSensitiveThrottle on mutations

### Tech stack

- apps/events
- django-filter
- drf-spectacular

### Metrics

| Label | Value | Trend |
| --- | --- | --- |
| Staff roles | 5 | stable |

## Organizations & memberships

Multi-tenant organizations with owner/admin/manager/member roles, invites, join/leave, and listing events owned by the organization.

| Property | Value |
| --- | --- |
| ID | organizations-multitenancy |
| Category | api |
| Status | beta |
| Icon | building |

### Highlights

- Slug-based organization URLs
- Member invite and role update endpoints
- Org managers can administer org-linked events via permissions

### Tech stack

- apps/organizations

### Metrics

| Label | Value | Trend |
| --- | --- | --- |
| Membership roles | 4 | stable |

## Ticket tiers & registrations

Per-event ticket tiers (price, capacity, visibility) and user registrations with status workflow, waitlist, cancellation, and host check-in.

| Property | Value |
| --- | --- |
| ID | registrations-ticketing |
| Category | api |
| Status | stable |
| Icon | ticket |

### Highlights

- POST /api/v2/events/{slug}/register/ with RegistrationThrottle
- Host-only registration list and status updates
- Check-in endpoint for door staff

### Tech stack

- apps/registrations
- apps/events

### Metrics

| Label | Value | Trend |
| --- | --- | --- |
| Registration states | 5+ | stable |

### Code snippet

_apps/registrations/views/registration_views.py_

```python
class EventRegistrationsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsEventHost]
    throttle_classes = [ReadHeavyThrottle]
```

## Comments, likes & moderation

Threaded comments on events with author edit/delete, likes, and host/moderator pin/unpin for announcements.

| Property | Value |
| --- | --- |
| ID | comments-engagement |
| Category | messaging |
| Status | stable |
| Icon | chat-dots |

### Highlights

- Soft delete for comments
- CanCommentOnEvent permission
- Signals hook for future notification tasks

### Tech stack

- apps/comments

## In-app notifications

User notification inbox with read/mark-all-read, stats, and delete; HTML email templates under apps/notifications/templates/.

| Property | Value |
| --- | --- |
| ID | notifications-inapp |
| Category | messaging |
| Status | stable |
| Icon | bell |

### Highlights

- Prefix /api/v2/notifications/
- mark-all-read and clear-read bulk actions
- Notification services for domain events

### Tech stack

- apps/notifications
- Celery (email tasks in users app)

## Redis cache & Celery with key prefix

django-redis for cache and rate-limit counters; Celery broker and result backend on Redis with REDIS_KEY_PREFIX social-events-api: to avoid collisions on shared Upstash.

| Property | Value |
| --- | --- |
| ID | redis-prefix-cache |
| Category | caching |
| Status | stable |
| Icon | database |

### Highlights

- KEY_PREFIX on django-redis
- global_keyprefix on Celery broker and results
- TLS rediss:// URL for Upstash in production .env

### Tech stack

- django-redis
- redis 5.2
- celery 5.4

### Metrics

| Label | Value | Trend |
| --- | --- | --- |
| Key prefix | social-events-api: | stable |

## Layered rate limiting

Global RateLimitMiddleware (200/min anon IP, 1000/min auth user) plus DRF scoped throttles for auth, writes, registration, and check-in.

| Property | Value |
| --- | --- |
| ID | rate-limiting-layers |
| Category | performance |
| Status | stable |
| Icon | speedometer |

### Highlights

- Fail-open if Redis unavailable (middleware)
- X-RateLimit-* response headers
- Exempt /api/schema/ and /api/docs/

### Tech stack

- common/throttling.py

### Code snippet

_common/throttling.py_

```python
class RateLimitMiddleware:
    ANON_LIMIT = (200, 60)
    AUTH_LIMIT = (1000, 60)
    EXEMPT_PATHS = {"/health/", "/api/schema/", "/api/docs/"}
```

## Request audit logging

AuditLogMiddleware records method, path, user, duration, and sanitized JSON body (passwords/tokens redacted) to the audit logger.

| Property | Value |
| --- | --- |
| ID | audit-logging |
| Category | monitoring |
| Status | stable |
| Icon | clipboard-list |

### Highlights

- SENSITIVE_FIELDS masking in common/audit_log.py
- AuditLog model in common/models.py for domain audits

### Tech stack

- common/audit_log.py

## OpenAPI docs & cloud deploy

drf-spectacular schema and Swagger UI; Docker multi-stage image with Gunicorn; production compose runs web only against RDS and Upstash.

| Property | Value |
| --- | --- |
| ID | openapi-docker-cloud |
| Category | integration |
| Status | stable |
| Icon | cloud |

### Highlights

- GET /api/schema/ and /api/docs/
- docker-compose.prod.yml — EC2 single container
- USE_S3 for media when enabled in production

### Tech stack

- drf-spectacular
- Docker
- Gunicorn
- AWS RDS
- Upstash

### Metrics

| Label | Value | Trend |
| --- | --- | --- |
| Documented OpenAPI | 1.0.0 | stable |

## Additional notes

# Project Features

> **Stable:** Events, registrations, comments, notifications, auth, Redis prefix, rate limits, OpenAPI.

> **Beta:** Organization endpoints need permission hardening; some Celery email hooks are TODO in signals.

> **Dangerous:** `/api/task-revoke/` and `/api/celery-health/` are AllowAny—restrict or protect behind admin network in production.

> **Before production:** Set `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, real `SECRET_KEY`, Upstash `rediss://` URLs, RDS `DATABASE_URL`, run Celery worker on EC2 (not only web container), enable `USE_S3` for durable media.

