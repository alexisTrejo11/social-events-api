---
problemStatement:
  problemTitle: "Fragmented event management for communities and organizers"
  problemDescription: "Community groups, venues, and independent organizers often rely on spreadsheets, generic form tools, and disconnected chat apps to publish events, sell or assign tickets, and keep attendees informed. That leads to double bookings, weak access control, no audit trail, and poor engagement after signup."
  problemList:
    - "No single API for organizations to own events, members, and branding"
    - "Manual registration lists without capacity, waitlist, or check-in flows"
    - "Comments and notifications scattered outside the event domain"
    - "Authentication friction across web and mobile clients"
    - "Difficulty scaling traffic without caching and background email delivery"

solution:
  solutionTitle: "One API for the full event lifecycle"
  solutionList:
    - title: "Multi-tenant organizations"
      description: "Organizations with memberships, invites, join/leave, and org-scoped event listings for clubs and venues."
    - title: "Rich event domain"
      description: "Draft/publish/cancel, categories, tags, recurrence, staff roles (host, co-host, moderator), favorites, and personalized feeds."
    - title: "Registrations & ticketing"
      description: "Ticket tiers with pricing and capacity; registrations with pending, confirmed, waitlist, cancelled, attended states and host check-in."
    - title: "Engagement layer"
      description: "Threaded comments with likes and host pin/unpin; in-app notifications with read state and email templates."
    - title: "Cloud-ready operations"
      description: "Docker on AWS EC2, RDS PostgreSQL, Upstash Redis with project key prefix, optional S3 media, Nginx TLS, Celery workers."

keyMetrics:
  metricsTitle: "Platform snapshot"
  metricsList:
    - "7 domain Django apps (users, organizations, events, locations, registrations, comments, notifications)"
    - "REST API under /api/v2/ plus /api/docs/ OpenAPI"
    - "85+ HTTP operations including ViewSet actions and custom routes"
    - "Redis namespace social-events-api: for cache and Celery broker"
    - "JWT access 60 min / refresh 7 days with rotation and blacklist"

links:
  github: "https://github.com/alexisTrejo11/social-events-api"
  demo: "https://api.socialevents.placeholder.example.com/api/docs/"
  documentation: "https://api.socialevents.placeholder.example.com/api/docs/"
  dockerHub: "https://hub.docker.com/r/PLACEHOLDER_ORG/social-events-api"

mediaGallery:
  title: "Social Events API — product views"
  description: "Screenshots and diagrams for portfolio presentation. Replace placeholder image URLs with Swagger UI, admin, or a frontend screenshot when available."
  items:
    - type: "image"
      url: "https://placehold.co/1200x630/1E3A5F/ffffff?text=Social+Events+API"
      thumbnail: "https://placehold.co/400x210/1E3A5F/ffffff?text=Events+API"
      title: "API cover"
      description: "Social Events REST API for organizers and attendees"
      alt: "Social Events API branding placeholder"
      category: "screenshot"
    - type: "image"
      url: "https://placehold.co/1200x800/2563EB/ffffff?text=OpenAPI+Swagger"
      thumbnail: "https://placehold.co/400x267/2563EB/ffffff?text=Swagger"
      title: "OpenAPI documentation"
      description: "Interactive schema at /api/docs/ via drf-spectacular"
      alt: "Swagger UI placeholder"
      category: "demo"

mediaItems:
  - type: "image"
    url: "https://placehold.co/800x500/059669/ffffff?text=AWS+Architecture"
    thumbnail: "https://placehold.co/320x200/059669/ffffff?text=AWS"
    title: "Cloud architecture"
    description: "EC2 (Docker) → RDS PostgreSQL + Upstash Redis + optional S3"
    alt: "AWS architecture diagram placeholder"
    category: "architecture"
  - type: "image"
    url: "https://placehold.co/800x500/DC2626/ffffff?text=Docker+Compose"
    thumbnail: "https://placehold.co/320x200/DC2626/ffffff?text=Docker"
    title: "Local Docker stack"
    description: "Postgres, Redis, API, Nginx, Certbot in docker-compose.local.yml"
    alt: "Docker compose placeholder"
    category: "diagram"

metrics:
  - label: "Django apps"
    value: "7"
    description: "users, organizations, events, locations, registrations, comments, notifications"
  - label: "API prefix"
    value: "/api/v2/"
    description: "Notifications at /api/v2/notifications/"
  - label: "Python runtime"
    value: "3.11"
    description: "docker/dockerfile multi-stage slim image"
  - label: "Auth"
    value: "JWT + OAuth"
    description: "SimpleJWT plus Google/GitHub via allauth"
---

# Overview

> **Audience:** Developers building event discovery apps, community platforms, or internal tools for venues and organizers.

> **Highlight:** Production path targets **AWS EC2** running the Docker `web` service behind **Nginx** (ports 80/443), with **Amazon RDS PostgreSQL** and **Upstash Redis** (`rediss://`) configured via `.env`. Local development uses SQLite and console email unless Docker local profile is used.

> **Warning — permissions gap:** `OrganizationViewSet` currently has no explicit `permission_classes` (defaults to AllowAny). Harden before public production.

> **Warning — WIP flows:** Email verification and password-reset views return placeholder responses; wire Celery email tasks and token storage before marketing “verified accounts.”

> **Useful:** Full interactive endpoint list is always available at `/api/docs/` after deploy—this portfolio YAML documents representative routes, not every action.
