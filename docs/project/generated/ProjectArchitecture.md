# Architecture

## Presentation (clients)

Web and mobile clients for attendees, organizers, and organization admins.

### Components

- Event discovery UI (placeholder)
- Organizer dashboard (placeholder)
- Registration & ticket flow

### Responsibilities

- Store JWT access token securely
- Call REST JSON under /api/v2/

### Technologies

- HTTPS
- Bearer JWT
- OpenAPI-generated clients (optional)

## API gateway & edge

TLS termination and reverse proxy to Gunicorn on AWS EC2.

### Components

- Nginx (local Docker / EC2)
- AWS ALB (recommended placeholder)
- CORS via django-cors-headers

### Responsibilities

- SSL termination and static file serving
- Proxy to Gunicorn :8000

### Technologies

- Nginx
- Let's Encrypt / ACM

## Application layer

Django 5 + DRF monolith with domain apps and shared common package.

### Components

- config.urls — routing
- apps/users — auth & profiles
- apps/organizations — tenants
- apps/events — events & roles
- apps/locations — venues
- apps/registrations — tickets & check-in
- apps/comments — engagement
- apps/notifications — inbox & email
- common — throttling, audit, pagination

### Responsibilities

- Permission classes per resource
- DRF serializers and filters
- Signals for side effects

### Technologies

- Django REST Framework
- SimpleJWT
- drf-spectacular
- Gunicorn WSGI

## Data & cache

RDS PostgreSQL for transactional data; Upstash Redis for cache, rate limits, and Celery.

### Components

- Amazon RDS PostgreSQL 15
- Upstash Redis — cache (REDIS_URL DB 1)
- Upstash Redis — Celery broker (DB 0)

### Responsibilities

- ACID persistence for events and registrations
- Prefixed keys (social-events-api:)

### Technologies

- psycopg2-binary
- django-redis

## Async & integrations

Background email tasks and OAuth providers.

### Components

- Celery workers on EC2
- Google / GitHub OAuth
- SMTP or Amazon SES
- Amazon S3 (optional media)

### Responsibilities

- Async verification and welcome emails
- Store uploaded media when USE_S3=true

### Technologies

- Celery 5.4
- boto3 / django-storages

## Design patterns

| Pattern | Category | Description |
| --- | --- | --- |
| 🧩 App per bounded context | Structural | Each domain (events, registrations, comments) is a Django app with models, serializers, views, and optional signals. |
| 🏗️ Service layer (selective) | Structural | Notification and email logic lives in apps/notifications/services/; views stay thin with permission checks. |
| 🔐 Custom permissions | Security | Object-level permissions (IsEventHost, CanManageRegistrations) compose with organization membership. |
| 🎀 Middleware cross-cutting | Behavioral | RateLimitMiddleware and AuditLogMiddleware wrap all requests before DRF. |
| 👁️ Observer — signals | Behavioral | users, registrations, and comments apps register signals for future notification hooks. |
| 🗑️ Soft delete base model | Data | common.models.BaseModel provides timestamps and soft-delete fields shared by domain models. |

## Scalability strategies

- **Stateless API containers** — Run multiple Gunicorn workers per EC2 instance; add EC2 instances behind ALB as traffic grows.
- **Amazon RDS** — Managed PostgreSQL with backups; scale instance class or add read replica for reporting (placeholder).
- **Upstash Redis** — Offload rate-limit counters and cache; prefix keys when sharing instance across projects.
- **Celery workers** — Decouple email and long tasks from HTTP threads; scale workers independently on EC2.
- **S3 for media** — Avoid filling EC2 disk—serve uploads from S3 when USE_S3 is enabled.

## Security strategies

- **JWT + per-view permissions** — Default authentication is JWT; each viewset declares IsAuthenticated, IsEventHost, or AllowAny explicitly.
- **Production TLS & HSTS** — SECURE_SSL_REDIRECT, secure cookies, HSTS, and SECURE_PROXY_SSL_HEADER in production.py.
- **Audit logging** — AuditLogMiddleware with sanitized bodies; sensitive fields redacted.
- **Layered throttling** — Global middleware plus DRF AuthActionsThrottle, RegistrationThrottle, CheckInThrottle.
- **OAuth via allauth** — Social tokens handled by django-allauth; API returns JWT via custom oauth views.

## Cache strategies

| Name | TTL | Coverage | Description |
| --- | --- | --- | --- |
| Django default cache | Default backend timeout (300s typical) | Rate limit windows, optional view cache | django-redis with KEY_PREFIX social-events-api: on Upstash (rediss://) |
| Celery broker & results | N/A (queue semantics) | Async tasks and task results | Redis DB 0 broker, DB 1 result backend; same global_keyprefix |
| Fail-open rate limits | 60s windows | All non-exempt HTTP paths | Middleware allows traffic if Redis is down—documented tradeoff |

## Architecture highlights

### 📖 OpenAPI-first

drf-spectacular documents ViewSets at /api/schema/ and /api/docs/.

### 🔗 Slug-based URLs

Events and organizations use slugs for readable public URLs.

### 📊 Celery observability

GET /api/celery-health/ and task status endpoints for ops.

### 🐳 Docker profiles

Local full stack vs production web-only compose files.

## Architecture diagram

### Legend

| Type | Label |
| --- | --- |
| client | Client |
| gateway | Gateway |
| service | API service |
| database | Database |
| queue | Queue / cache |
| monitoring | External |

### Nodes

| ID | Label | Type | Status |
| --- | --- | --- | --- |
| clients | Web / mobile clients | client | healthy |
| nginx | Nginx / ALB (TLS) | gateway | healthy |
| api | Social Events API (EC2 Docker) | service | healthy |
| rds | AWS RDS PostgreSQL | database | healthy |
| upstash | Upstash Redis | queue | healthy |
| celery | Celery worker (EC2) | service | healthy |
| s3 | AWS S3 (optional) | database | healthy |
| smtp | SMTP / SES | monitoring | healthy |
| oauth | Google / GitHub | monitoring | healthy |

### Connections

| From | To | Label | Protocol |
| --- | --- | --- | --- |
| clients | nginx | HTTPS | TLS 1.2+ |
| nginx | api | Proxy | HTTP |
| api | rds | SQL | PostgreSQL |
| api | upstash | Cache / broker | rediss |
| api | celery | Enqueue | Redis |
| celery | upstash | Broker | Redis |
| celery | smtp | Email | SMTP |
| api | s3 | Media | HTTPS |
| clients | oauth | OAuth | HTTPS |
| oauth | api | Token exchange | REST |

### Mermaid overview

```mermaid
flowchart LR
    clients([Web / mobile clients])
    nginx{Nginx / ALB (TLS)}
    api[Social Events API (EC2 Docker)]
    rds[(AWS RDS PostgreSQL)]
    upstash[/Upstash Redis/]
    celery[Celery worker (EC2)]
    s3[(AWS S3 (optional))]
    smtp>SMTP / SES]
    oauth>Google / GitHub]
    clients -->|HTTPS| nginx
    nginx -->|Proxy| api
    api -->|SQL| rds
    api -->|Cache / broker| upstash
    api -->|Enqueue| celery
    celery -->|Broker| upstash
    celery -->|Email| smtp
    api -->|Media| s3
    clients -->|OAuth| oauth
    oauth -->|Token exchange| api
```

## Data flow

### Request flow

1. **Client request** — Client sends HTTPS request with Bearer JWT for protected routes (events, registrations, profile).
2. **Middleware** — RateLimitMiddleware and AuditLogMiddleware run; DRF authenticates JWT and applies throttles.
3. **View & permissions** — ViewSet or APIView checks IsEventHost, CanManageRegistrations, etc., then validates serializer.
4. **Persistence** — ORM reads/writes RDS; cache keys updated in Upstash with social-events-api: prefix.
5. **JSON response** — DRF Response returns serializer data or standard error shape to client.

### Event flow

1. **Domain action** — User registers, books event, or comments—signal or view may trigger async work.
2. **Celery enqueue** — Task published to Redis broker DB 0 with prefixed keys.
3. **Worker execution** — Celery worker on EC2 runs users.send_verification_email or common.test_task.
4. **Delivery** — SMTP sends HTML email from apps/notifications/templates/; in-app Notification row created when wired.

## Technical decisions

### Django monolith on EC2

**Problem:** Need rapid feature delivery for event MVP without Kubernetes complexity.

**Solution:** Single repo, Docker image, Gunicorn on EC2; domain split into Django apps.

**Outcome:** Simple deploy path documented in docker/README.md; scale EC2/RDS vertically first.

#### Alternatives considered

- Microservices per bounded context
- Serverless API Gateway + Lambda

### Amazon RDS PostgreSQL

**Problem:** Relational model for organizations, events, registrations, and foreign keys.

**Solution:** RDS in production; SQLite only in config.settings.development for local runserver.

**Outcome:** CONN_MAX_AGE 600 reduces connection overhead from Docker web container.

#### Alternatives considered

- Self-managed Postgres on EC2
- PlanetScale / serverless SQL

### Upstash Redis with key prefix

**Problem:** One Redis account shared across multiple portfolio projects on Upstash.

**Solution:** REDIS_KEY_PREFIX and Celery global_keyprefix social-events-api:.

**Outcome:** No key collisions; rediss:// for TLS to Upstash endpoint.

#### Alternatives considered

- Dedicated Redis per environment
- Separate Upstash database per project

### SimpleJWT + allauth

**Problem:** SPA needs stateless auth; users want Google/GitHub sign-in.

**Solution:** JWT for API; allauth stores social accounts; custom views return tokens.

**Outcome:** Consistent Bearer flow; blacklist on logout when token_blacklist enabled.

#### Alternatives considered

- Session-only auth
- Auth0 / Cognito

### drf-spectacular for API contract

**Problem:** Frontend and portfolio need discoverable endpoint documentation.

**Solution:** Schema at /api/schema/, Swagger UI at /api/docs/.

**Outcome:** Schema stays in sync with ViewSet decorators.

#### Alternatives considered

- Manual OpenAPI YAML
- GraphQL

## Additional notes

# Architecture

> **Cloud target:** EC2 runs Docker `web`; **RDS** holds data; **Upstash** handles cache and Celery; **S3** optional for uploads. Treat as deployed architecture for portfolio—even if EC2 provisioning is still in progress, `.env` is already shaped for this layout.

> **Highlight:** Request path is Nginx → Gunicorn → DRF → RDS/Upstash; async path is API → Celery → Upstash broker → SMTP.

> **Warning:** Without a Celery worker process on EC2, eventFlow steps 2–4 only run for synchronous code paths.

> **Dangerous:** Organization endpoints need auth before exposing production RDS to the internet.

> **Debt:** Add `/health/` route for ALB health checks; wire django-celery-beat for scheduled reminders.

