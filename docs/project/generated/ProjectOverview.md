# Project Overview

## Fragmented event management for communities and organizers

Community groups, venues, and independent organizers often rely on spreadsheets, generic form tools, and disconnected chat apps to publish events, sell or assign tickets, and keep attendees informed. That leads to double bookings, weak access control, no audit trail, and poor engagement after signup.

### Pain points

- No single API for organizations to own events, members, and branding
- Manual registration lists without capacity, waitlist, or check-in flows
- Comments and notifications scattered outside the event domain
- Authentication friction across web and mobile clients
- Difficulty scaling traffic without caching and background email delivery

## One API for the full event lifecycle

- **Multi-tenant organizations** — Organizations with memberships, invites, join/leave, and org-scoped event listings for clubs and venues.
- **Rich event domain** — Draft/publish/cancel, categories, tags, recurrence, staff roles (host, co-host, moderator), favorites, and personalized feeds.
- **Registrations & ticketing** — Ticket tiers with pricing and capacity; registrations with pending, confirmed, waitlist, cancelled, attended states and host check-in.
- **Engagement layer** — Threaded comments with likes and host pin/unpin; in-app notifications with read state and email templates.
- **Cloud-ready operations** — Docker on AWS EC2, RDS PostgreSQL, Upstash Redis with project key prefix, optional S3 media, Nginx TLS, Celery workers.

## Platform snapshot

- 7 domain Django apps (users, organizations, events, locations, registrations, comments, notifications)
- REST API under /api/v2/ plus /api/docs/ OpenAPI
- 85+ HTTP operations including ViewSet actions and custom routes
- Redis namespace social-events-api: for cache and Celery broker
- JWT access 60 min / refresh 7 days with rotation and blacklist

## Links

| Resource | URL |
| --- | --- |
| Github | https://github.com/alexisTrejo11/social-events-api |
| Demo | https://api.socialevents.placeholder.example.com/api/docs/ |
| Documentation | https://api.socialevents.placeholder.example.com/api/docs/ |
| Dockerhub | https://hub.docker.com/r/PLACEHOLDER_ORG/social-events-api |

## Social Events API — product views

Screenshots and diagrams for portfolio presentation. Replace placeholder image URLs with Swagger UI, admin, or a frontend screenshot when available.

### API cover

Social Events REST API for organizers and attendees

- **Type:** image | **Category:** screenshot
- ![Social Events API branding placeholder](https://placehold.co/1200x630/1E3A5F/ffffff?text=Social+Events+API)

### OpenAPI documentation

Interactive schema at /api/docs/ via drf-spectacular

- **Type:** image | **Category:** demo
- ![Swagger UI placeholder](https://placehold.co/1200x800/2563EB/ffffff?text=OpenAPI+Swagger)

## Additional media

### Cloud architecture

EC2 (Docker) → RDS PostgreSQL + Upstash Redis + optional S3

### Local Docker stack

Postgres, Redis, API, Nginx, Certbot in docker-compose.local.yml

## Metrics

| Label | Value | Description |
| --- | --- | --- |
| Django apps | 7 | users, organizations, events, locations, registrations, comments, notifications |
| API prefix | /api/v2/ | Notifications at /api/v2/notifications/ |
| Python runtime | 3.11 | docker/dockerfile multi-stage slim image |
| Auth | JWT + OAuth | SimpleJWT plus Google/GitHub via allauth |

## Additional notes

# Overview

> **Audience:** Developers building event discovery apps, community platforms, or internal tools for venues and organizers.

> **Highlight:** Production path targets **AWS EC2** running the Docker `web` service behind **Nginx** (ports 80/443), with **Amazon RDS PostgreSQL** and **Upstash Redis** (`rediss://`) configured via `.env`. Local development uses SQLite and console email unless Docker local profile is used.

> **Warning — permissions gap:** `OrganizationViewSet` currently has no explicit `permission_classes` (defaults to AllowAny). Harden before public production.

> **Warning — WIP flows:** Email verification and password-reset views return placeholder responses; wire Celery email tasks and token storage before marketing “verified accounts.”

> **Useful:** Full interactive endpoint list is always available at `/api/docs/` after deploy—this portfolio YAML documents representative routes, not every action.

