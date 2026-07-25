---
layers:
  - name: "Presentation (clients)"
    description: "Web and mobile clients for attendees, organizers, and organization admins."
    color: "#6366F1"
    expanded: true
    components:
      - "Event discovery UI (placeholder)"
      - "Organizer dashboard (placeholder)"
      - "Registration & ticket flow"
    responsibilities:
      - "Store JWT access token securely"
      - "Call REST JSON under /api/v2/"
    technologies:
      - "HTTPS"
      - "Bearer JWT"
      - "OpenAPI-generated clients (optional)"

  - name: "API gateway & edge"
    description: "TLS termination and reverse proxy to Gunicorn on AWS EC2."
    color: "#10B981"
    expanded: false
    components:
      - "Nginx (local Docker / EC2)"
      - "AWS ALB (recommended placeholder)"
      - "CORS via django-cors-headers"
    responsibilities:
      - "SSL termination and static file serving"
      - "Proxy to Gunicorn :8000"
    technologies:
      - "Nginx"
      - "Let's Encrypt / ACM"

  - name: "Application layer"
    description: "Django 5 + DRF monolith with domain apps and shared common package."
    color: "#F59E0B"
    expanded: true
    components:
      - "config.urls — routing"
      - "apps/users — auth & profiles"
      - "apps/organizations — tenants"
      - "apps/events — events & roles"
      - "apps/locations — venues"
      - "apps/registrations — tickets & check-in"
      - "apps/comments — engagement"
      - "apps/notifications — inbox & email"
      - "common — throttling, audit, pagination"
    responsibilities:
      - "Permission classes per resource"
      - "DRF serializers and filters"
      - "Signals for side effects"
    technologies:
      - "Django REST Framework"
      - "SimpleJWT"
      - "drf-spectacular"
      - "Gunicorn WSGI"

  - name: "Data & cache"
    description: "RDS PostgreSQL for transactional data; Upstash Redis for cache, rate limits, and Celery."
    color: "#EF4444"
    expanded: true
    components:
      - "Amazon RDS PostgreSQL 15"
      - "Upstash Redis — cache (REDIS_URL DB 1)"
      - "Upstash Redis — Celery broker (DB 0)"
    responsibilities:
      - "ACID persistence for events and registrations"
      - "Prefixed keys (social-events-api:)"
    technologies:
      - "psycopg2-binary"
      - "django-redis"

  - name: "Async & integrations"
    description: "Background email tasks and OAuth providers."
    color: "#8B5CF6"
    expanded: false
    components:
      - "Celery workers on EC2"
      - "Google / GitHub OAuth"
      - "SMTP or Amazon SES"
      - "Amazon S3 (optional media)"
    responsibilities:
      - "Async verification and welcome emails"
      - "Store uploaded media when USE_S3=true"
    technologies:
      - "Celery 5.4"
      - "boto3 / django-storages"

designPatterns:
  - title: "App per bounded context"
    emoji: "🧩"
    description: "Each domain (events, registrations, comments) is a Django app with models, serializers, views, and optional signals."
    category: "Structural"
    badge: "Django"
  - title: "Service layer (selective)"
    emoji: "🏗️"
    description: "Notification and email logic lives in apps/notifications/services/; views stay thin with permission checks."
    category: "Structural"
    badge: "DRF"
  - title: "Custom permissions"
    emoji: "🔐"
    description: "Object-level permissions (IsEventHost, CanManageRegistrations) compose with organization membership."
    category: "Security"
    badge: "Events"
  - title: "Middleware cross-cutting"
    emoji: "🎀"
    description: "RateLimitMiddleware and AuditLogMiddleware wrap all requests before DRF."
    category: "Behavioral"
    badge: "common"
  - title: "Observer — signals"
    emoji: "👁️"
    description: "users, registrations, and comments apps register signals for future notification hooks."
    category: "Behavioral"
    badge: "Async"
  - title: "Soft delete base model"
    emoji: "🗑️"
    description: "common.models.BaseModel provides timestamps and soft-delete fields shared by domain models."
    category: "Data"
    badge: "ORM"

scalabilityStrategies:
  - title: "Stateless API containers"
    description: "Run multiple Gunicorn workers per EC2 instance; add EC2 instances behind ALB as traffic grows."
  - title: "Amazon RDS"
    description: "Managed PostgreSQL with backups; scale instance class or add read replica for reporting (placeholder)."
  - title: "Upstash Redis"
    description: "Offload rate-limit counters and cache; prefix keys when sharing instance across projects."
  - title: "Celery workers"
    description: "Decouple email and long tasks from HTTP threads; scale workers independently on EC2."
  - title: "S3 for media"
    description: "Avoid filling EC2 disk—serve uploads from S3 when USE_S3 is enabled."

securityStrategies:
  - title: "JWT + per-view permissions"
    description: "Default authentication is JWT; each viewset declares IsAuthenticated, IsEventHost, or AllowAny explicitly."
  - title: "Production TLS & HSTS"
    description: "SECURE_SSL_REDIRECT, secure cookies, HSTS, and SECURE_PROXY_SSL_HEADER in production.py."
  - title: "Audit logging"
    description: "AuditLogMiddleware with sanitized bodies; sensitive fields redacted."
  - title: "Layered throttling"
    description: "Global middleware plus DRF AuthActionsThrottle, RegistrationThrottle, CheckInThrottle."
  - title: "OAuth via allauth"
    description: "Social tokens handled by django-allauth; API returns JWT via custom oauth views."

cacheStrategies:
  - name: "Django default cache"
    description: "django-redis with KEY_PREFIX social-events-api: on Upstash (rediss://)"
    ttl: "Default backend timeout (300s typical)"
    coverage: "Rate limit windows, optional view cache"
  - name: "Celery broker & results"
    description: "Redis DB 0 broker, DB 1 result backend; same global_keyprefix"
    ttl: "N/A (queue semantics)"
    coverage: "Async tasks and task results"
  - name: "Fail-open rate limits"
    description: "Middleware allows traffic if Redis is down—documented tradeoff"
    ttl: "60s windows"
    coverage: "All non-exempt HTTP paths"

architectureFeatures:
  - title: "OpenAPI-first"
    emoji: "📖"
    description: "drf-spectacular documents ViewSets at /api/schema/ and /api/docs/."
  - title: "Slug-based URLs"
    emoji: "🔗"
    description: "Events and organizations use slugs for readable public URLs."
  - title: "Celery observability"
    emoji: "📊"
    description: "GET /api/celery-health/ and task status endpoints for ops."
  - title: "Docker profiles"
    emoji: "🐳"
    description: "Local full stack vs production web-only compose files."

architectureDiagram:
  legendItems:
    - type: "client"
      label: "Client"
      color: "#6366F1"
      icon: "monitor"
    - type: "gateway"
      label: "Gateway"
      color: "#10B981"
      icon: "shield"
    - type: "service"
      label: "API service"
      color: "#F59E0B"
      icon: "server"
    - type: "database"
      label: "Database"
      color: "#EF4444"
      icon: "database"
    - type: "queue"
      label: "Queue / cache"
      color: "#8B5CF6"
      icon: "layers"
    - type: "monitoring"
      label: "External"
      color: "#64748B"
      icon: "cloud"

  nodes:
    - id: "clients"
      label: "Web / mobile clients"
      type: "client"
      x: 80
      y: 120
      connections: ["nginx"]
      status: "healthy"
      traffic: 200
    - id: "nginx"
      label: "Nginx / ALB (TLS)"
      type: "gateway"
      x: 280
      y: 120
      connections: ["api"]
      status: "healthy"
      traffic: 200
    - id: "api"
      label: "Social Events API (EC2 Docker)"
      type: "service"
      x: 480
      y: 120
      connections: ["rds", "upstash", "celery", "s3"]
      status: "healthy"
      traffic: 150
    - id: "rds"
      label: "AWS RDS PostgreSQL"
      type: "database"
      x: 720
      y: 60
      connections: []
      status: "healthy"
      traffic: 90
    - id: "upstash"
      label: "Upstash Redis"
      type: "queue"
      x: 720
      y: 180
      connections: []
      status: "healthy"
      traffic: 80
    - id: "celery"
      label: "Celery worker (EC2)"
      type: "service"
      x: 480
      y: 280
      connections: ["upstash", "smtp"]
      status: "healthy"
      traffic: 40
    - id: "s3"
      label: "AWS S3 (optional)"
      type: "database"
      x: 720
      y: 280
      connections: []
      status: "healthy"
      traffic: 25
    - id: "smtp"
      label: "SMTP / SES"
      type: "monitoring"
      x: 280
      y: 280
      connections: []
      status: "healthy"
      traffic: 30
    - id: "oauth"
      label: "Google / GitHub"
      type: "monitoring"
      x: 80
      y: 280
      connections: ["api"]
      status: "healthy"
      traffic: 20

  connections:
    - id: "c1"
      from: "clients"
      to: "nginx"
      label: "HTTPS"
      protocol: "TLS 1.2+"
      isActive: true
    - id: "c2"
      from: "nginx"
      to: "api"
      label: "Proxy"
      protocol: "HTTP"
      isActive: true
    - id: "c3"
      from: "api"
      to: "rds"
      label: "SQL"
      protocol: "PostgreSQL"
      isActive: true
    - id: "c4"
      from: "api"
      to: "upstash"
      label: "Cache / broker"
      protocol: "rediss"
      isActive: true
    - id: "c5"
      from: "api"
      to: "celery"
      label: "Enqueue"
      protocol: "Redis"
      isActive: true
    - id: "c6"
      from: "celery"
      to: "upstash"
      label: "Broker"
      protocol: "Redis"
      isActive: true
    - id: "c7"
      from: "celery"
      to: "smtp"
      label: "Email"
      protocol: "SMTP"
      isActive: true
    - id: "c8"
      from: "api"
      to: "s3"
      label: "Media"
      protocol: "HTTPS"
      isActive: true
    - id: "c9"
      from: "clients"
      to: "oauth"
      label: "OAuth"
      protocol: "HTTPS"
      isActive: true
    - id: "c10"
      from: "oauth"
      to: "api"
      label: "Token exchange"
      protocol: "REST"
      isActive: true

dataFlow:
  requestFlow:
    - number: 1
      title: "Client request"
      description: "Client sends HTTPS request with Bearer JWT for protected routes (events, registrations, profile)."
      icon: "send"
    - number: 2
      title: "Middleware"
      description: "RateLimitMiddleware and AuditLogMiddleware run; DRF authenticates JWT and applies throttles."
      icon: "filter"
    - number: 3
      title: "View & permissions"
      description: "ViewSet or APIView checks IsEventHost, CanManageRegistrations, etc., then validates serializer."
      icon: "shield"
    - number: 4
      title: "Persistence"
      description: "ORM reads/writes RDS; cache keys updated in Upstash with social-events-api: prefix."
      icon: "database"
    - number: 5
      title: "JSON response"
      description: "DRF Response returns serializer data or standard error shape to client."
      icon: "reply"

  eventFlow:
    - number: 1
      title: "Domain action"
      description: "User registers, books event, or comments—signal or view may trigger async work."
      icon: "zap"
    - number: 2
      title: "Celery enqueue"
      description: "Task published to Redis broker DB 0 with prefixed keys."
      icon: "inbox"
    - number: 3
      title: "Worker execution"
      description: "Celery worker on EC2 runs users.send_verification_email or common.test_task."
      icon: "cpu"
    - number: 4
      title: "Delivery"
      description: "SMTP sends HTML email from apps/notifications/templates/; in-app Notification row created when wired."
      icon: "mail"

techDecisions:
  decisions:
    - title: "Django monolith on EC2"
      problem: "Need rapid feature delivery for event MVP without Kubernetes complexity."
      solution: "Single repo, Docker image, Gunicorn on EC2; domain split into Django apps."
      alternatives:
        - "Microservices per bounded context"
        - "Serverless API Gateway + Lambda"
      outcome: "Simple deploy path documented in docker/README.md; scale EC2/RDS vertically first."
      icon: "layers"
    - title: "Amazon RDS PostgreSQL"
      problem: "Relational model for organizations, events, registrations, and foreign keys."
      solution: "RDS in production; SQLite only in config.settings.development for local runserver."
      alternatives:
        - "Self-managed Postgres on EC2"
        - "PlanetScale / serverless SQL"
      outcome: "CONN_MAX_AGE 600 reduces connection overhead from Docker web container."
      icon: "database"
    - title: "Upstash Redis with key prefix"
      problem: "One Redis account shared across multiple portfolio projects on Upstash."
      solution: "REDIS_KEY_PREFIX and Celery global_keyprefix social-events-api:."
      alternatives:
        - "Dedicated Redis per environment"
        - "Separate Upstash database per project"
      outcome: "No key collisions; rediss:// for TLS to Upstash endpoint."
      icon: "redis"
    - title: "SimpleJWT + allauth"
      problem: "SPA needs stateless auth; users want Google/GitHub sign-in."
      solution: "JWT for API; allauth stores social accounts; custom views return tokens."
      alternatives:
        - "Session-only auth"
        - "Auth0 / Cognito"
      outcome: "Consistent Bearer flow; blacklist on logout when token_blacklist enabled."
      icon: "key"
    - title: "drf-spectacular for API contract"
      problem: "Frontend and portfolio need discoverable endpoint documentation."
      solution: "Schema at /api/schema/, Swagger UI at /api/docs/."
      alternatives:
        - "Manual OpenAPI YAML"
        - "GraphQL"
      outcome: "Schema stays in sync with ViewSet decorators."
      icon: "book"
---

# Architecture

> **Cloud target:** EC2 runs Docker `web`; **RDS** holds data; **Upstash** handles cache and Celery; **S3** optional for uploads. Treat as deployed architecture for portfolio—even if EC2 provisioning is still in progress, `.env` is already shaped for this layout.

> **Highlight:** Request path is Nginx → Gunicorn → DRF → RDS/Upstash; async path is API → Celery → Upstash broker → SMTP.

> **Warning:** Without a Celery worker process on EC2, eventFlow steps 2–4 only run for synchronous code paths.

> **Dangerous:** Organization endpoints need auth before exposing production RDS to the internet.

> **Debt:** Add `/health/` route for ALB health checks; wire django-celery-beat for scheduled reminders.
