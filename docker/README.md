# Docker deployment profiles

This project uses a **single** `.env` file at the repository root. Compose files live under `docker/` and pick different profiles:

| Profile | Compose file | What runs |
|--------|----------------|-----------|
| **Local** | `docker-compose.local.yml` | Postgres, Redis, API, Nginx, Certbot |
| **Production** | `docker-compose.prod.yml` | API only (DB/Redis are external) |

For **local**, the `web` service **overrides** database and Redis hostnames so containers use Docker service names (`postgres`, `redis`), even if your `.env` still says `localhost`.

For **production**, set real cloud endpoints in `.env` (`POSTGRES_HOST`, `REDIS_HOST`, etc.). Nothing is overridden in compose.

---

## Prerequisites

1. Copy the example env file (once):

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` for your case (see sections below).

3. Run all commands from the **repository root** so paths and `--env-file .env` resolve correctly.

---

## Local profile (full stack)

### `.env` hints for local

- `DJANGO_SETTINGS_MODULE=config.settings.production` (or keep as in example; compose also sets this on `web`).
- `POSTGRES_*` / `DB_*` credentials can stay as defaults; **hosts in `.env` are ignored for `web`** — compose forces `postgres` / `redis`.
- Optional: `CREATE_SUPERUSER=true`, `POPULATE_DB=true` for first boot.
- `DOMAIN_NAME=localhost` if you use Nginx without real SSL yet.

### Commands

```bash
# Build and start everything
docker compose --env-file .env -f docker/docker-compose.local.yml up -d --build

# Follow logs
docker compose --env-file .env -f docker/docker-compose.local.yml logs -f

# Stop and remove containers (keeps volumes)
docker compose --env-file .env -f docker/docker-compose.local.yml down

# Stop and remove containers + volumes (wipes DB data)
docker compose --env-file .env -f docker/docker-compose.local.yml down -v
```

### Useful local endpoints

| Service | From host machine |
|---------|-------------------|
| API (via Nginx) | http://localhost |
| Postgres | `localhost:5431` (user/db from `.env`) |
| Redis | `localhost:6380` |

### One-off Django commands (local)

```bash
docker compose --env-file .env -f docker/docker-compose.local.yml exec web python manage.py migrate
docker compose --env-file .env -f docker/docker-compose.local.yml exec web python manage.py createsuperuser
```

### HTTPS (Let's Encrypt) on local stack

Use the init script from the repo root (it targets the **local** compose file):

```bash
./scripts/init-letsencrypt.sh yourdomain.com admin@yourdomain.com 0
```

See also `docs/HTTPS_SETUP.md` and `docs/QUICK_START_HTTPS.md`.

---

## Production profile (app only)

### `.env` requirements for production

Point at your **managed** Postgres and Redis (or ElastiCache, etc.):

```env
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
SECRET_KEY=<strong-secret>
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

POSTGRES_HOST=<cloud-postgres-host>
POSTGRES_PORT=5432
POSTGRES_DB=social_events_db
POSTGRES_USER=<user>
POSTGRES_PASSWORD=<password>

REDIS_HOST=<cloud-redis-host>
REDIS_PORT=6379
REDIS_URL=redis://<cloud-redis-host>:6379/1
CELERY_BROKER_URL=redis://<cloud-redis-host>:6379/0
REDIS_KEY_PREFIX=social-events-api:

CREATE_SUPERUSER=false
POPULATE_DB=false
```

You can use `DATABASE_URL` instead of individual `POSTGRES_*` variables if you prefer (see `config/settings/production.py`).

Ensure the host running Docker can reach those endpoints (VPC, security groups, TLS if required by your provider).

### Commands

```bash
# Build and run API only
docker compose --env-file .env -f docker/docker-compose.prod.yml up -d --build

# Logs
docker compose --env-file .env -f docker/docker-compose.prod.yml logs -f web

# Stop
docker compose --env-file .env -f docker/docker-compose.prod.yml down
```

The API listens on port `8000` by default (`PORT` in `.env` maps host → container).

Put a reverse proxy / load balancer (ALB, Cloudflare, platform ingress) in front of this container in real production; this compose file does not start Nginx.

---

## Quick reference

```bash
# Local — full stack
docker compose --env-file .env -f docker/docker-compose.local.yml up -d --build

# Production — app only, external DB/Redis
docker compose --env-file .env -f docker/docker-compose.prod.yml up -d --build
```

---

## Files

| File | Purpose |
|------|---------|
| `docker-compose.local.yml` | Local dev/staging with bundled Postgres & Redis |
| `docker-compose.prod.yml` | Production API container |
| `dockerfile` | Multi-stage image build |
| `nginx/` | Reverse proxy templates (local profile only) |

Legacy single-file `docker-compose.yml` was split into the two profiles above.
