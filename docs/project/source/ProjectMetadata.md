---
projectId: "social-events-api"
featured: true
name: "Social Events API"
language: "Python"
category: "backend"
framework: "Django REST Framework"
version: "1.0.0"
repositoryUrl: "https://github.com/alexisTrejo11/social-events-api"
liveDemoUrl: "https://api.socialevents.placeholder.example.com/api/docs/"
description: "REST API for discovering, hosting, and attending social events—organizations, ticket tiers, registrations, comments, in-app notifications, OAuth/JWT auth, and Celery-backed async work. Deployed on AWS EC2 with RDS PostgreSQL and Upstash Redis."
techStack:
  - "Python 3.11"
  - "Django 5.1.6"
  - "Django REST Framework 3.15.2"
  - "PostgreSQL 15 (AWS RDS)"
  - "Upstash Redis (TLS) + django-redis"
  - "Celery 5.4.0"
  - "SimpleJWT 5.3.1"
  - "django-allauth + dj-rest-auth (Google, GitHub)"
  - "drf-spectacular 0.27.2"
  - "Docker + Nginx + Gunicorn"
  - "AWS S3 (optional media via django-storages)"
status: "stable"
createdAt: "2025-01-15T00:00:00.000Z"
updatedAt: "2026-06-01T00:00:00.000Z"
---

# Project Metadata

> Portfolio metadata for the Social Events API backend. Replace `api.socialevents.placeholder.example.com` with your real EC2/ALB hostname when the production domain is live.

> **Highlight:** Single Django monolith with ~85 REST operations under `/api/v2/`, OpenAPI at `/api/docs/`, and Redis key prefix `social-events-api:` for safe multi-project Upstash usage.

> **Warning:** Never commit `.env`—it contains Upstash `rediss://` credentials and RDS passwords. Use AWS SSM Parameter Store or sealed secrets on EC2.
