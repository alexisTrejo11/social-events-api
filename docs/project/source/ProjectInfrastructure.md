---
metrics:
  - label: "Gunicorn bind"
    value: "0.0.0.0:8000"
    icon: "server"
    description: "Inside web container; exposed via Nginx in local profile"
  - label: "Production host port"
    value: "${PORT:-8000}"
    icon: "network"
    description: "docker-compose.prod.yml maps host port to container 8000 on EC2"
  - label: "Local Postgres"
    value: "5431:5432"
    icon: "database"
    description: "Host port 5431 to avoid conflict with local PostgreSQL"
  - label: "Local Redis"
    value: "6380:6379"
    icon: "redis"
    description: "Host port 6380; production uses Upstash rediss:// endpoint"
  - label: "Redis key prefix"
    value: "social-events-api:"
    icon: "key"
    description: "REDIS_KEY_PREFIX — cache + Celery global_keyprefix"
  - label: "DB pool"
    value: "600s"
    icon: "clock"
    description: "CONN_MAX_AGE on RDS in production settings"

cloudServices:
  - name: "Amazon EC2"
    purpose: "Runs Docker web container (social_events_api) with Gunicorn; Nginx on same host or separate instance for TLS termination (ports 80/443 local compose pattern)"
    icon: "aws-ec2"
    cost: "~$15–40/mo (t3.small placeholder — update when instance type chosen)"
  - name: "Amazon RDS (PostgreSQL 15)"
    purpose: "Managed primary database for all Django models (POSTGRES_HOST / DATABASE_URL in production .env)"
    icon: "aws-rds"
    cost: "~$25–80/mo (db.t4g.micro placeholder — update with actual instance)"
  - name: "Upstash Redis"
    purpose: "TLS Redis (rediss://) for django-redis cache, rate limits, Celery broker (DB 0) and result backend (DB 1) with key prefix social-events-api:"
    icon: "redis"
    cost: "Free tier or ~$10/mo (pay-as-you-go placeholder)"
  - name: "Amazon S3"
    purpose: "Optional media storage for avatars, event covers, org logos when USE_S3=true (django-storages + boto3)"
    icon: "aws-s3"
    cost: "~$1–5/mo low traffic (placeholder)"
  - name: "SMTP / Amazon SES"
    purpose: "Transactional email for registration, password reset, and notification templates"
    icon: "mail"
    cost: "SES ~$0.10/1k emails (placeholder)"
  - name: "Google & GitHub OAuth"
    purpose: "Social login providers configured via Django admin SocialApp or env (see docs/OAUTH_SETUP.md)"
    icon: "oauth"
    cost: "Free (API quotas apply)"

deploymentLayers:
  - name: "Clients"
    color: "#4F46E5"
    components:
      - name: "Web frontend (planned)"
        icon: "layout"
        description: "SPA or mobile app consuming /api/v2/ with JWT (placeholder URL in FRONTEND_URL)"
      - name: "API consumers"
        icon: "smartphone"
        description: "Third-party integrations via Bearer token and OpenAPI client"
      - name: "Swagger UI"
        icon: "book"
        description: "Developers test at /api/docs/ on deployed host"

  - name: "Edge & compute (AWS EC2)"
    color: "#059669"
    components:
      - name: "Nginx reverse proxy"
        icon: "globe"
        description: "TLS, static/media volumes, proxy to Gunicorn (local compose; replicate on EC2)"
      - name: "Docker — social_events_api"
        icon: "docker"
        description: "Built from docker/dockerfile; DJANGO_SETTINGS_MODULE=config.settings.production"
      - name: "Celery worker (recommended)"
        icon: "worker"
        description: "Separate process or container on EC2 for users.send_*_email and common.test_task"
      - name: "Certbot / ACM"
        icon: "lock"
        description: "Let's Encrypt in local compose; use ACM certificate on ALB in AWS (placeholder)"

  - name: "Data & messaging"
    color: "#DC2626"
    components:
      - name: "RDS PostgreSQL"
        icon: "database"
        description: "social_events_db — users, events, registrations, comments, notifications"
      - name: "Upstash Redis"
        icon: "redis"
        description: "Prefixed keys; separate logical DB indexes 0 (broker) and 1 (cache/results)"
      - name: "S3 bucket (optional)"
        icon: "bucket"
        description: "AWS_STORAGE_BUCKET_NAME when USE_S3=true"

  - name: "External integrations"
    color: "#D97706"
    components:
      - name: "Google OAuth"
        icon: "google"
        description: "POST /api/v2/auth/oauth/google/"
      - name: "GitHub OAuth"
        icon: "github"
        description: "POST /api/v2/auth/oauth/github/"
      - name: "Email SMTP"
        icon: "mail"
        description: "DEFAULT_FROM_EMAIL and EMAIL_* from .env"

dockerFiles:
  - service: "docker-compose.local.yml"
    description: "Full local stack: Postgres, Redis, web, Nginx, Certbot on social_events_network."
    content: |
      services:
        postgres:
          image: postgres:15-alpine
          ports: ["5431:5432"]
        redis:
          image: redis:7-alpine
          ports: ["6380:6379"]
        web:
          build: { context: .., dockerfile: docker/dockerfile }
          environment:
            POSTGRES_HOST: postgres
            REDIS_HOST: redis
            REDIS_URL: redis://redis:6379/1
            CELERY_BROKER_URL: redis://redis:6379/0
        nginx:
          ports: ["80:80", "443:443"]

  - service: "docker-compose.prod.yml"
    description: "Production profile: web container only; Postgres and Redis are external (RDS + Upstash)."
    content: |
      services:
        web:
          build: { context: .., dockerfile: docker/dockerfile }
          env_file: ../.env
          environment:
            DJANGO_SETTINGS_MODULE: config.settings.production
          ports: ["${PORT:-8000}:8000"]
          volumes: [logs_volume, static_volume, media_volume]
      # Cloud: RDS + Upstash configured in ../.env

  - service: "entrypoint.sh"
    description: "Waits for REDIS_HOST/POSTGRES_HOST, migrates, optional superuser/populate, starts Celery detached, runs Gunicorn."
    content: |
      # nc -z ${REDIS_HOST} ${REDIS_PORT}
      # nc -z ${POSTGRES_HOST} ${POSTGRES_PORT}
      python manage.py migrate --noinput
      celery -A config worker --detach  # when Redis configured
      gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}

---

# Infrastructure

> **Deploy story (target):** Build image on CI or EC2, run `docker compose -f docker/docker-compose.prod.yml up -d` with `.env` pointing to **RDS** and **Upstash** (`rediss://` + password). Place **Nginx** or **ALB** in front for HTTPS.

> **Highlight:** `REDIS_KEY_PREFIX=social-events-api:` lets this API share one Upstash database with other projects without key collisions.

> **EC2 checklist:** Security group allows 443 from internet; restrict 8000 to VPC if using ALB; store secrets in SSM; attach IAM role for S3/SES if used.

> **Dangerous:** `POPULATE_DB=true` / `CREATE_SUPERUSER=true` only on first non-production boot. Never enable on production RDS.

> **Gap:** Celery beat (`django-celery-beat`) is in requirements but not in `INSTALLED_APPS`—add before scheduling periodic event reminders.
