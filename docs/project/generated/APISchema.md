# API Schema

**API type:** REST

## Auth

### `POST` /api/v2/auth/register/

**Register new user**

Creates account with email, username, password strength rules; triggers verification email when Celery wired.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | auth_actions — 10/min |
| **Tags** | auth |

#### Request body

**Content-Type:** `application/json`

**Schema (summary):**

```json
{
  "email": "string",
  "username": "string",
  "password": "string",
  "first_name": "string",
  "last_name": "string"
}
```

**Example:**

```json
{
  "email": "alex@example.com",
  "username": "alext",
  "password": "SecurePass123!",
  "first_name": "Alex",
  "last_name": "Trejo"
}
```

#### Responses

- **201** — User created

```json
{
  "message": "User registered successfully. Please check your email to verify your account.",
  "user": {
    "id": "uuid",
    "email": "alex@example.com"
  }
}
```

- **400** — Validation error

```json
{
  "email": [
    "This field is required."
  ]
}
```

---

### `POST` /api/v2/auth/login/

**Login and obtain JWT**

Email/password authentication returning access and refresh tokens plus user profile.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | auth_actions — 10/min |
| **Tags** | auth |

#### Request body

**Content-Type:** `application/json`

**Schema (summary):**

```json
{
  "email": "string",
  "password": "string"
}
```

**Example:**

```json
{
  "email": "alex@example.com",
  "password": "SecurePass123!"
}
```

#### Responses

- **200** — Tokens issued

```json
{
  "tokens": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  },
  "user": {
    "email": "alex@example.com",
    "username": "alext"
  }
}
```

- **401** — Invalid credentials

```json
{
  "detail": "No active account found with the given credentials"
}
```

---

### `POST` /api/v2/auth/logout/

**Logout and blacklist refresh token**

Invalidates refresh token when token_blacklist app is enabled.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | auth_actions — 10/min |
| **Tags** | auth |

#### Request body

**Content-Type:** `application/json`

**Schema (summary):**

```json
{
  "refresh": "string"
}
```

**Example:**

```json
{
  "refresh": "eyJ..."
}
```

#### Responses

- **200** — Logged out

```json
{
  "message": "Successfully logged out."
}
```

---

### `POST` /api/v2/auth/token/refresh/

**Refresh access token**

Exchange valid refresh token for new access token (SimpleJWT).

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | auth_actions — 10/min |
| **Tags** | auth |

#### Request body

**Content-Type:** `application/json`

**Schema (summary):**

```json
{
  "refresh": "string"
}
```

**Example:**

```json
{
  "refresh": "eyJ..."
}
```

#### Responses

- **200** — New access token

```json
{
  "access": "eyJ..."
}
```

---

## Comments

### `GET` /api/v2/events/{event_slug}/comments/

**List event comments**

Threaded comments for an event (public read).

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | read_heavy — 300/min |
| **Tags** | comments |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| event_slug | path | string | Yes | Event slug |

#### Responses

- **200** — Comments

```json
{
  "results": [
    {
      "id": 1,
      "body": "Looking forward to it!",
      "author_username": "jane"
    }
  ]
}
```

---

### `POST` /api/v2/events/{event_slug}/comments/

**Post comment**

Authenticated user comments on event if allowed.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | write_standard — 60/min |
| **Tags** | comments |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| event_slug | path | string | Yes | Event slug |

#### Request body

**Content-Type:** `application/json`

**Schema (summary):**

```json
{
  "body": "string",
  "parent_id": "integer"
}
```

**Example:**

```json
{
  "body": "See you there!"
}
```

#### Responses

- **201** — Comment created

```json
{
  "id": 2,
  "body": "See you there!"
}
```

---

### `POST` /api/v2/events/{event_slug}/comments/{comment_id}/like/

**Like comment**

Authenticated user likes a comment.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | write_standard — 60/min |
| **Tags** | comments |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| event_slug | path | string | Yes | Event slug |
| comment_id | path | integer | Yes | Comment ID |

#### Responses

- **201** — Liked

```json
{
  "likes_count": 5
}
```

---

## Events

### `GET` /api/v2/events/

**List events**

Paginated published events; authenticated users also see own drafts and hosted events. Supports category, location, date filters.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | read_heavy — 300/min |
| **Tags** | events |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| category | query | string | No | Category slug |
| start_date_after | query | date | No | Events starting after date |

#### Responses

- **200** — Event list

```json
{
  "count": 1,
  "results": [
    {
      "title": "Tech Meetup",
      "slug": "tech-meetup",
      "status": "published"
    }
  ]
}
```

---

### `POST` /api/v2/events/

**Create event**

Creates draft event; requires verified authenticated user.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | write_sensitive — 20/min |
| **Tags** | events |

#### Request body

**Content-Type:** `application/json`

**Schema (summary):**

```json
{
  "title": "string",
  "description": "string",
  "start_datetime": "datetime",
  "location": "integer"
}
```

**Example:**

```json
{
  "title": "Open Mic Night",
  "description": "Monthly open mic",
  "start_datetime": "2026-07-01T19:00:00Z"
}
```

#### Responses

- **201** — Event created

```json
{
  "slug": "open-mic-night",
  "status": "draft"
}
```

---

### `GET` /api/v2/events/{slug}/

**Get event by slug**

Retrieve single event if published/public or caller is host.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | read_heavy — 300/min |
| **Tags** | events |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| slug | path | string | Yes | Event slug |

#### Responses

- **200** — Event detail

```json
{
  "title": "Tech Meetup",
  "slug": "tech-meetup",
  "status": "published"
}
```

---

### `POST` /api/v2/events/{slug}/publish/

**Publish event**

Organizer publishes draft event to make it discoverable.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | write_sensitive — 20/min |
| **Tags** | events |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| slug | path | string | Yes | Event slug |

#### Responses

- **200** — Published

```json
{
  "status": "published",
  "published_at": "2026-06-01T12:00:00Z"
}
```

---

### `POST` /api/v2/events/{slug}/favorite/

**Favorite event**

Authenticated user adds event to favorites.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | write_standard — 60/min |
| **Tags** | events |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| slug | path | string | Yes | Event slug |

#### Responses

- **201** — Favorited

```json
{
  "message": "Event added to favorites"
}
```

---

### `GET` /api/v2/categories/

**List event categories**

Read-only list of event categories for filtering.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | read_heavy — 300/min |
| **Tags** | events |

#### Responses

- **200** — Categories

```json
{
  "results": [
    {
      "name": "Music",
      "slug": "music"
    }
  ]
}
```

---

## Locations

### `GET` /api/v2/locations/

**List locations**

Venues and virtual locations for events (JWT required).

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | read_heavy — 300/min |
| **Tags** | locations |

#### Responses

- **200** — Locations

```json
{
  "results": [
    {
      "name": "Community Hall",
      "city": "Austin"
    }
  ]
}
```

---

## Notifications

### `GET` /api/v2/notifications/

**List notifications**

In-app notifications for authenticated user.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | read_heavy — 300/min |
| **Tags** | notifications |

#### Responses

- **200** — Notifications

```json
{
  "results": [
    {
      "id": 1,
      "title": "Registration confirmed",
      "is_read": false
    }
  ]
}
```

---

### `POST` /api/v2/notifications/{notification_id}/read/

**Mark notification read**

Marks single notification as read.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | write_standard — 60/min |
| **Tags** | notifications |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| notification_id | path | integer | Yes | Notification ID |

#### Responses

- **200** — Marked read

```json
{
  "is_read": true
}
```

---

### `POST` /api/v2/notifications/mark-all-read/

**Mark all notifications read**

Bulk mark all user notifications as read.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | write_standard — 60/min |
| **Tags** | notifications |

#### Responses

- **200** — All marked

```json
{
  "updated_count": 12
}
```

---

## Oauth

### `POST` /api/v2/auth/oauth/google/

**Google OAuth login**

Exchange Google access token for JWT via django-allauth adapter.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | auth_actions — 10/min |
| **Tags** | oauth |

#### Request body

**Content-Type:** `application/json`

**Schema (summary):**

```json
{
  "access_token": "string"
}
```

**Example:**

```json
{
  "access_token": "ya29..."
}
```

#### Responses

- **200** — JWT returned

```json
{
  "tokens": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  },
  "user": {
    "email": "user@gmail.com"
  }
}
```

---

### `POST` /api/v2/auth/oauth/github/

**GitHub OAuth login**

Exchange GitHub access token for JWT.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | auth_actions — 10/min |
| **Tags** | oauth |

#### Request body

**Content-Type:** `application/json`

**Schema (summary):**

```json
{
  "access_token": "string"
}
```

**Example:**

```json
{
  "access_token": "gho_..."
}
```

#### Responses

- **200** — JWT returned

```json
{
  "tokens": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  }
}
```

---

## Organizations

### `GET` /api/v2/organizations/

**List organizations**

List organizations (permission hardening recommended before production).

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | read_heavy — 300/min |
| **Tags** | organizations |

#### Responses

- **200** — Organizations

```json
{
  "results": [
    {
      "name": "Austin Tech",
      "slug": "austin-tech"
    }
  ]
}
```

---

### `POST` /api/v2/organizations/

**Create organization**

Creates a new organization record.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | write_sensitive — 20/min |
| **Tags** | organizations |

#### Request body

**Content-Type:** `application/json`

**Schema (summary):**

```json
{
  "name": "string",
  "description": "string"
}
```

**Example:**

```json
{
  "name": "Austin Tech",
  "description": "Local tech community"
}
```

#### Responses

- **201** — Created

```json
{
  "slug": "austin-tech",
  "name": "Austin Tech"
}
```

---

### `POST` /api/v2/organizations/{slug}/members/invite/

**Invite organization member**

Invite user to organization by email or username.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | write_sensitive — 20/min |
| **Tags** | organizations |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| slug | path | string | Yes | Organization slug |

#### Request body

**Content-Type:** `application/json`

**Schema (summary):**

```json
{
  "email": "string",
  "role": "string"
}
```

**Example:**

```json
{
  "email": "member@example.com",
  "role": "member"
}
```

#### Responses

- **201** — Invitation sent

```json
{
  "message": "Invitation created"
}
```

---

## Registrations

### `GET` /api/v2/events/{event_slug}/ticket-tiers/

**List ticket tiers**

Ticket types for an event with price and capacity.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | read_heavy — 300/min |
| **Tags** | registrations |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| event_slug | path | string | Yes | Event slug |

#### Responses

- **200** — Tiers

```json
{
  "results": [
    {
      "name": "General Admission",
      "price": "0.00",
      "capacity": 100
    }
  ]
}
```

---

### `POST` /api/v2/events/{event_slug}/register/

**Register for event**

Authenticated user registers for event; may enter waitlist if full.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | registration — 10/min |
| **Tags** | registrations |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| event_slug | path | string | Yes | Event slug |

#### Request body

**Content-Type:** `application/json`

**Schema (summary):**

```json
{
  "ticket_tier_id": "integer",
  "notes": "string"
}
```

**Example:**

```json
{
  "ticket_tier_id": 1,
  "notes": "Vegetarian meal"
}
```

#### Responses

- **201** — Registered

```json
{
  "id": 42,
  "status": "confirmed"
}
```

---

### `DELETE` /api/v2/events/{event_slug}/register/

**Cancel own registration**

Registration owner cancels their spot.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | write_standard — 60/min |
| **Tags** | registrations |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| event_slug | path | string | Yes | Event slug |

#### Responses

- **200** — Cancelled

```json
{
  "message": "Registration cancelled"
}
```

---

### `POST` /api/v2/events/{event_slug}/registrations/{registration_id}/check-in/

**Check in attendee**

Event host checks in attendee at door.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | check_in — 120/min |
| **Tags** | registrations |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| event_slug | path | string | Yes | Event slug |
| registration_id | path | integer | Yes | Registration ID |

#### Responses

- **200** — Checked in

```json
{
  "status": "attended",
  "checked_in_at": "2026-07-01T18:55:00Z"
}
```

---

### `GET` /api/v2/users/me/registrations/

**List my registrations**

All event registrations for the authenticated user.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | read_heavy — 300/min |
| **Tags** | registrations |

#### Responses

- **200** — Registrations

```json
{
  "results": [
    {
      "event_title": "Tech Meetup",
      "status": "confirmed"
    }
  ]
}
```

---

## Service

### `GET` /api/schema/

**OpenAPI schema (JSON)**

Machine-readable OpenAPI 3 schema for all registered DRF endpoints.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | Exempt (middleware) |
| **Tags** | service |

#### Responses

- **200** — OpenAPI document

```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "Social Events API",
    "version": "1.0.0"
  }
}
```

---

### `GET` /api/docs/

**Swagger UI**

Interactive API explorer for developers and portfolio demos.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | Exempt (middleware) |
| **Tags** | service |

#### Responses

- **200** — HTML Swagger UI

```json
{
  "note": "Open in browser"
}
```

---

### `GET` /api/celery-health/

**Celery worker health**

Reports whether Celery workers are connected to the Redis broker on EC2.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | Exempt |
| **Tags** | service |

#### Responses

- **200** — Workers available

```json
{
  "status": "healthy",
  "workers": 1
}
```

---

### `GET` /api/task-status/{task_id}/

**Celery task status**

Poll async task result by Celery task ID.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | Exempt |
| **Tags** | service |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| task_id | path | string | Yes | Celery task UUID |

#### Responses

- **200** — Task state

```json
{
  "task_id": "a1b2...",
  "status": "SUCCESS",
  "result": {
    "ok": true
  }
}
```

---

## Users

### `GET` /api/v2/users/me/

**Current user profile**

Retrieve authenticated user profile and metadata.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | Global auth 1000/min + read_heavy |
| **Tags** | users |

#### Responses

- **200** — Profile

```json
{
  "id": "uuid",
  "email": "alex@example.com",
  "username": "alext",
  "bio": "Event organizer"
}
```

---

### `PATCH` /api/v2/users/me/

**Update current user profile**

Partial update of profile fields for authenticated user.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | write_standard — 60/min |
| **Tags** | users |

#### Request body

**Content-Type:** `application/json`

**Schema (summary):**

```json
{
  "bio": "string",
  "avatar": "url"
}
```

**Example:**

```json
{
  "bio": "Community events in Austin"
}
```

#### Responses

- **200** — Updated profile

```json
{
  "bio": "Community events in Austin"
}
```

---

### `GET` /api/v2/users/{username}/

**Public user profile**

Read-only public profile by username.

| | |
|---|---|
| **Auth required** | No |
| **Rate limit** | Global anon 200/min |
| **Tags** | users |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| username | path | string | Yes | Unique username |

#### Responses

- **200** — Public profile

```json
{
  "username": "alext",
  "first_name": "Alex"
}
```

---

### `POST` /api/v2/users/{username}/follow/

**Follow user**

Authenticated user follows another user by username.

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | write_standard — 60/min |
| **Tags** | users |

#### Parameters

| Name | In | Type | Required | Description |
| --- | --- | --- | --- | --- |
| username | path | string | Yes | Target username |

#### Responses

- **201** — Following

```json
{
  "message": "Now following jane"
}
```

---

### `GET` /api/v2/users/me/feed/

**Personalized event feed**

Events from followed users and organizations (authenticated).

| | |
|---|---|
| **Auth required** | Yes |
| **Rate limit** | read_heavy — 300/min |
| **Tags** | users |

#### Responses

- **200** — Feed page

```json
{
  "count": 10,
  "results": [
    {
      "title": "Summer Meetup",
      "slug": "summer-meetup"
    }
  ]
}
```

---

## Additional notes

# API Schema

> **Base URL (production placeholder):** `https://api.socialevents.placeholder.example.com`

> **Auth header:** `Authorization: Bearer <access_token>` for protected routes.

> **Highlight:** Interactive docs at `/api/docs/` (drf-spectacular). This file documents representative routes; the OpenAPI schema lists every ViewSet action.

> **Warning:** `/api/task-revoke/` and `/api/celery-health/` are unauthenticated—lock down in production.

> **Warning:** Organization ViewSet defaults to AllowAny—treat as known gap before go-live.

> **Useful:** Redis-backed throttles use cache keys prefixed with `social-events-api:` on Upstash.

