# Infrastructure

## Metrics

| Label | Value | Description |
| --- | --- | --- |
| Gunicorn bind | 0.0.0.0:8000 | Inside web container; exposed via Nginx in local profile |
| Production host port | ${PORT:-8000} | docker-compose.prod.yml maps host port to container 8000 on EC2 |
| Local Postgres | 5431:5432 | Host port 5431 to avoid conflict with local PostgreSQL |
| Local Redis | 6380:6379 | Host port 6380; production uses Upstash rediss:// endpoint |
| Redis key prefix | social-events-api: | REDIS_KEY_PREFIX — cache + Celery global_keyprefix |
| DB pool | 600s | CONN_MAX_AGE on RDS in production settings |

## Cloud services

| Service | Purpose | Est. cost |
| --- | --- | --- |
| Amazon EC2 | Runs Docker web container (social_events_api) with Gunicorn; Nginx on same host or separate instance for TLS termination (ports 80/443 local compose pattern) | ~$15–40/mo (t3.small placeholder — update when instance type chosen) |
| Amazon RDS (PostgreSQL 15) | Managed primary database for all Django models (POSTGRES_HOST / DATABASE_URL in production .env) | ~$25–80/mo (db.t4g.micro placeholder — update with actual instance) |
| Upstash Redis | TLS Redis (rediss://) for django-redis cache, rate limits, Celery broker (DB 0) and result backend (DB 1) with key prefix social-events-api: | Free tier or ~$10/mo (pay-as-you-go placeholder) |
| Amazon S3 | Optional media storage for avatars, event covers, org logos when USE_S3=true (django-storages + boto3) | ~$1–5/mo low traffic (placeholder) |
| SMTP / Amazon SES | Transactional email for registration, password reset, and notification templates | SES ~$0.10/1k emails (placeholder) |
| Google & GitHub OAuth | Social login providers configured via Django admin SocialApp or env (see docs/OAUTH_SETUP.md) | Free (API quotas apply) |

## Deployment layers

### Clients

- **Web frontend (planned)** — SPA or mobile app consuming /api/v2/ with JWT (placeholder URL in FRONTEND_URL)
- **API consumers** — Third-party integrations via Bearer token and OpenAPI client
- **Swagger UI** — Developers test at /api/docs/ on deployed host

### Edge & compute (AWS EC2)

- **Nginx reverse proxy** — TLS, static/media volumes, proxy to Gunicorn (local compose; replicate on EC2)
- **Docker — social_events_api** — Built from docker/dockerfile; DJANGO_SETTINGS_MODULE=config.settings.production
- **Celery worker (recommended)** — Separate process or container on EC2 for users.send_*_email and common.test_task
- **Certbot / ACM** — Let's Encrypt in local compose; use ACM certificate on ALB in AWS (placeholder)

### Data & messaging

- **RDS PostgreSQL** — social_events_db — users, events, registrations, comments, notifications
- **Upstash Redis** — Prefixed keys; separate logical DB indexes 0 (broker) and 1 (cache/results)
- **S3 bucket (optional)** — AWS_STORAGE_BUCKET_NAME when USE_S3=true

### External integrations

- **Google OAuth** — POST /api/v2/auth/oauth/google/
- **GitHub OAuth** — POST /api/v2/auth/oauth/github/
- **Email SMTP** — DEFAULT_FROM_EMAIL and EMAIL_* from .env

## Docker configuration

### docker-compose.local.yml

Full local stack: Postgres, Redis, web, Nginx, Certbot on social_events_network.

```yaml
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
```

### docker-compose.prod.yml

Production profile: web container only; Postgres and Redis are external (RDS + Upstash).

```yaml
services:
  web:
    build: { context: .., dockerfile: docker/dockerfile }
    env_file: ../.env
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.production
    ports: ["${PORT:-8000}:8000"]
    volumes: [logs_volume, static_volume, media_volume]
# Cloud: RDS + Upstash configured in ../.env
```

### entrypoint.sh

Waits for REDIS_HOST/POSTGRES_HOST, migrates, optional superuser/populate, starts Celery detached, runs Gunicorn.

```yaml
# nc -z ${REDIS_HOST} ${REDIS_PORT}
# nc -z ${POSTGRES_HOST} ${POSTGRES_PORT}
python manage.py migrate --noinput
celery -A config worker --detach  # when Redis configured
gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
```

## Additional notes

# Infrastructure

> **Deploy story (target):** Build image on CI or EC2, run `docker compose -f docker/docker-compose.prod.yml up -d` with `.env` pointing to **RDS** and **Upstash** (`rediss://` + password). Place **Nginx** or **ALB** in front for HTTPS.

> **Highlight:** `REDIS_KEY_PREFIX=social-events-api:` lets this API share one Upstash database with other projects without key collisions.

> **EC2 checklist:** Security group allows 443 from internet; restrict 8000 to VPC if using ALB; store secrets in SSM; attach IAM role for S3/SES if used.

> **Dangerous:** `POPULATE_DB=true` / `CREATE_SUPERUSER=true` only on first non-production boot. Never enable on production RDS.

> **Gap:** Celery beat (`django-celery-beat`) is in requirements but not in `INSTALLED_APPS`—add before scheduling periodic event reminders.

