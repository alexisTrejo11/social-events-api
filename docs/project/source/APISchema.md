---
type: REST
httpEndpoints:
- id: openapi-schema
  method: GET
  urlPath: /api/schema/
  summary: OpenAPI schema (JSON)
  description: Machine-readable OpenAPI 3 schema for all registered DRF endpoints.
  tags:
  - service
  authenticated: false
  rateLimit: Exempt (middleware)
  responses:
  - status: 200
    description: OpenAPI document
    example:
      openapi: 3.0.3
      info:
        title: Social Events API
        version: 1.0.0
- id: swagger-ui
  method: GET
  urlPath: /api/docs/
  summary: Swagger UI
  description: Interactive API explorer for developers and portfolio demos.
  tags:
  - service
  authenticated: false
  rateLimit: Exempt (middleware)
  responses:
  - status: 200
    description: HTML Swagger UI
    example:
      note: Open in browser
- id: celery-health
  method: GET
  urlPath: /api/celery-health/
  summary: Celery worker health
  description: Reports whether Celery workers are connected to the Redis broker on EC2.
  tags:
  - service
  authenticated: false
  rateLimit: Exempt
  responses:
  - status: 200
    description: Workers available
    example:
      status: healthy
      workers: 1
- id: auth-register
  method: POST
  urlPath: /api/v2/auth/register/
  summary: Register new user
  description: Creates account with email, username, password strength rules; triggers verification email when Celery wired.
  tags:
  - auth
  authenticated: false
  rateLimit: auth_actions — 10/min
  requestBody:
    contentType: application/json
    schema:
      email: string
      username: string
      password: string
      first_name: string
      last_name: string
    example:
      email: alex@example.com
      username: alext
      password: SecurePass123!
      first_name: Alex
      last_name: Trejo
  responses:
  - status: 201
    description: User created
    example:
      message: User registered successfully. Please check your email to verify your account.
      user:
        id: uuid
        email: alex@example.com
  - status: 400
    description: Validation error
    example:
      email:
      - This field is required.
- id: auth-login
  method: POST
  urlPath: /api/v2/auth/login/
  summary: Login and obtain JWT
  description: Email/password authentication returning access and refresh tokens plus user profile.
  tags:
  - auth
  authenticated: false
  rateLimit: auth_actions — 10/min
  requestBody:
    contentType: application/json
    schema:
      email: string
      password: string
    example:
      email: alex@example.com
      password: SecurePass123!
  responses:
  - status: 200
    description: Tokens issued
    example:
      tokens:
        access: eyJ...
        refresh: eyJ...
      user:
        email: alex@example.com
        username: alext
  - status: 401
    description: Invalid credentials
    example:
      detail: No active account found with the given credentials
- id: auth-logout
  method: POST
  urlPath: /api/v2/auth/logout/
  summary: Logout and blacklist refresh token
  description: Invalidates refresh token when token_blacklist app is enabled.
  tags:
  - auth
  authenticated: true
  rateLimit: auth_actions — 10/min
  requestBody:
    contentType: application/json
    schema:
      refresh: string
    example:
      refresh: eyJ...
  responses:
  - status: 200
    description: Logged out
    example:
      message: Successfully logged out.
- id: auth-token-refresh
  method: POST
  urlPath: /api/v2/auth/token/refresh/
  summary: Refresh access token
  description: Exchange valid refresh token for new access token (SimpleJWT).
  tags:
  - auth
  authenticated: false
  rateLimit: auth_actions — 10/min
  requestBody:
    contentType: application/json
    schema:
      refresh: string
    example:
      refresh: eyJ...
  responses:
  - status: 200
    description: New access token
    example:
      access: eyJ...
- id: oauth-google
  method: POST
  urlPath: /api/v2/auth/oauth/google/
  summary: Google OAuth login
  description: Exchange Google access token for JWT via django-allauth adapter.
  tags:
  - oauth
  authenticated: false
  rateLimit: auth_actions — 10/min
  requestBody:
    contentType: application/json
    schema:
      access_token: string
    example:
      access_token: ya29...
  responses:
  - status: 200
    description: JWT returned
    example:
      tokens:
        access: eyJ...
        refresh: eyJ...
      user:
        email: user@gmail.com
- id: oauth-github
  method: POST
  urlPath: /api/v2/auth/oauth/github/
  summary: GitHub OAuth login
  description: Exchange GitHub access token for JWT.
  tags:
  - oauth
  authenticated: false
  rateLimit: auth_actions — 10/min
  requestBody:
    contentType: application/json
    schema:
      access_token: string
    example:
      access_token: gho_...
  responses:
  - status: 200
    description: JWT returned
    example:
      tokens:
        access: eyJ...
        refresh: eyJ...
- id: users-me
  method: GET
  urlPath: /api/v2/users/me/
  summary: Current user profile
  description: Retrieve authenticated user profile and metadata.
  tags:
  - users
  authenticated: true
  rateLimit: Global auth 1000/min + read_heavy
  responses:
  - status: 200
    description: Profile
    example:
      id: uuid
      email: alex@example.com
      username: alext
      bio: Event organizer
- id: users-me-update
  method: PATCH
  urlPath: /api/v2/users/me/
  summary: Update current user profile
  description: Partial update of profile fields for authenticated user.
  tags:
  - users
  authenticated: true
  rateLimit: write_standard — 60/min
  requestBody:
    contentType: application/json
    schema:
      bio: string
      avatar: url
    example:
      bio: Community events in Austin
  responses:
  - status: 200
    description: Updated profile
    example:
      bio: Community events in Austin
- id: users-public
  method: GET
  urlPath: /api/v2/users/{username}/
  summary: Public user profile
  description: Read-only public profile by username.
  tags:
  - users
  authenticated: false
  rateLimit: Global anon 200/min
  parameters:
  - name: username
    in: path
    type: string
    required: true
    description: Unique username
    example: alext
  responses:
  - status: 200
    description: Public profile
    example:
      username: alext
      first_name: Alex
- id: users-follow
  method: POST
  urlPath: /api/v2/users/{username}/follow/
  summary: Follow user
  description: Authenticated user follows another user by username.
  tags:
  - users
  authenticated: true
  rateLimit: write_standard — 60/min
  parameters:
  - name: username
    in: path
    type: string
    required: true
    description: Target username
    example: jane
  responses:
  - status: 201
    description: Following
    example:
      message: Now following jane
- id: users-feed
  method: GET
  urlPath: /api/v2/users/me/feed/
  summary: Personalized event feed
  description: Events from followed users and organizations (authenticated).
  tags:
  - users
  authenticated: true
  rateLimit: read_heavy — 300/min
  responses:
  - status: 200
    description: Feed page
    example:
      count: 10
      results:
      - title: Summer Meetup
        slug: summer-meetup
- id: events-list
  method: GET
  urlPath: /api/v2/events/
  summary: List events
  description: Paginated published events; authenticated users also see own drafts and hosted events. Supports category, location,
    date filters.
  tags:
  - events
  authenticated: false
  rateLimit: read_heavy — 300/min
  parameters:
  - name: category
    in: query
    type: string
    required: false
    description: Category slug
    example: music
  - name: start_date_after
    in: query
    type: date
    required: false
    description: Events starting after date
    example: '2026-06-01'
  responses:
  - status: 200
    description: Event list
    example:
      count: 1
      results:
      - title: Tech Meetup
        slug: tech-meetup
        status: published
- id: events-create
  method: POST
  urlPath: /api/v2/events/
  summary: Create event
  description: Creates draft event; requires verified authenticated user.
  tags:
  - events
  authenticated: true
  rateLimit: write_sensitive — 20/min
  requestBody:
    contentType: application/json
    schema:
      title: string
      description: string
      start_datetime: datetime
      location: integer
    example:
      title: Open Mic Night
      description: Monthly open mic
      start_datetime: '2026-07-01T19:00:00Z'
  responses:
  - status: 201
    description: Event created
    example:
      slug: open-mic-night
      status: draft
- id: events-detail
  method: GET
  urlPath: /api/v2/events/{slug}/
  summary: Get event by slug
  description: Retrieve single event if published/public or caller is host.
  tags:
  - events
  authenticated: false
  rateLimit: read_heavy — 300/min
  parameters:
  - name: slug
    in: path
    type: string
    required: true
    description: Event slug
    example: tech-meetup
  responses:
  - status: 200
    description: Event detail
    example:
      title: Tech Meetup
      slug: tech-meetup
      status: published
- id: events-publish
  method: POST
  urlPath: /api/v2/events/{slug}/publish/
  summary: Publish event
  description: Organizer publishes draft event to make it discoverable.
  tags:
  - events
  authenticated: true
  rateLimit: write_sensitive — 20/min
  parameters:
  - name: slug
    in: path
    type: string
    required: true
    description: Event slug
    example: tech-meetup
  responses:
  - status: 200
    description: Published
    example:
      status: published
      published_at: '2026-06-01T12:00:00Z'
- id: events-favorite
  method: POST
  urlPath: /api/v2/events/{slug}/favorite/
  summary: Favorite event
  description: Authenticated user adds event to favorites.
  tags:
  - events
  authenticated: true
  rateLimit: write_standard — 60/min
  parameters:
  - name: slug
    in: path
    type: string
    required: true
    description: Event slug
    example: tech-meetup
  responses:
  - status: 201
    description: Favorited
    example:
      message: Event added to favorites
- id: categories-list
  method: GET
  urlPath: /api/v2/categories/
  summary: List event categories
  description: Read-only list of event categories for filtering.
  tags:
  - events
  authenticated: false
  rateLimit: read_heavy — 300/min
  responses:
  - status: 200
    description: Categories
    example:
      results:
      - name: Music
        slug: music
- id: organizations-list
  method: GET
  urlPath: /api/v2/organizations/
  summary: List organizations
  description: List organizations (permission hardening recommended before production).
  tags:
  - organizations
  authenticated: false
  rateLimit: read_heavy — 300/min
  responses:
  - status: 200
    description: Organizations
    example:
      results:
      - name: Austin Tech
        slug: austin-tech
- id: organizations-create
  method: POST
  urlPath: /api/v2/organizations/
  summary: Create organization
  description: Creates a new organization record.
  tags:
  - organizations
  authenticated: false
  rateLimit: write_sensitive — 20/min
  requestBody:
    contentType: application/json
    schema:
      name: string
      description: string
    example:
      name: Austin Tech
      description: Local tech community
  responses:
  - status: 201
    description: Created
    example:
      slug: austin-tech
      name: Austin Tech
- id: organizations-invite
  method: POST
  urlPath: /api/v2/organizations/{slug}/members/invite/
  summary: Invite organization member
  description: Invite user to organization by email or username.
  tags:
  - organizations
  authenticated: false
  rateLimit: write_sensitive — 20/min
  parameters:
  - name: slug
    in: path
    type: string
    required: true
    description: Organization slug
    example: austin-tech
  requestBody:
    contentType: application/json
    schema:
      email: string
      role: string
    example:
      email: member@example.com
      role: member
  responses:
  - status: 201
    description: Invitation sent
    example:
      message: Invitation created
- id: locations-list
  method: GET
  urlPath: /api/v2/locations/
  summary: List locations
  description: Venues and virtual locations for events (JWT required).
  tags:
  - locations
  authenticated: true
  rateLimit: read_heavy — 300/min
  responses:
  - status: 200
    description: Locations
    example:
      results:
      - name: Community Hall
        city: Austin
- id: ticket-tiers-list
  method: GET
  urlPath: /api/v2/events/{event_slug}/ticket-tiers/
  summary: List ticket tiers
  description: Ticket types for an event with price and capacity.
  tags:
  - registrations
  authenticated: false
  rateLimit: read_heavy — 300/min
  parameters:
  - name: event_slug
    in: path
    type: string
    required: true
    description: Event slug
    example: tech-meetup
  responses:
  - status: 200
    description: Tiers
    example:
      results:
      - name: General Admission
        price: '0.00'
        capacity: 100
- id: register-event
  method: POST
  urlPath: /api/v2/events/{event_slug}/register/
  summary: Register for event
  description: Authenticated user registers for event; may enter waitlist if full.
  tags:
  - registrations
  authenticated: true
  rateLimit: registration — 10/min
  parameters:
  - name: event_slug
    in: path
    type: string
    required: true
    description: Event slug
    example: tech-meetup
  requestBody:
    contentType: application/json
    schema:
      ticket_tier_id: integer
      notes: string
    example:
      ticket_tier_id: 1
      notes: Vegetarian meal
  responses:
  - status: 201
    description: Registered
    example:
      id: 42
      status: confirmed
- id: cancel-registration
  method: DELETE
  urlPath: /api/v2/events/{event_slug}/register/
  summary: Cancel own registration
  description: Registration owner cancels their spot.
  tags:
  - registrations
  authenticated: true
  rateLimit: write_standard — 60/min
  parameters:
  - name: event_slug
    in: path
    type: string
    required: true
    description: Event slug
    example: tech-meetup
  responses:
  - status: 200
    description: Cancelled
    example:
      message: Registration cancelled
- id: check-in
  method: POST
  urlPath: /api/v2/events/{event_slug}/registrations/{registration_id}/check-in/
  summary: Check in attendee
  description: Event host checks in attendee at door.
  tags:
  - registrations
  authenticated: true
  rateLimit: check_in — 120/min
  parameters:
  - name: event_slug
    in: path
    type: string
    required: true
    description: Event slug
    example: tech-meetup
  - name: registration_id
    in: path
    type: integer
    required: true
    description: Registration ID
    example: 42
  responses:
  - status: 200
    description: Checked in
    example:
      status: attended
      checked_in_at: '2026-07-01T18:55:00Z'
- id: my-registrations
  method: GET
  urlPath: /api/v2/users/me/registrations/
  summary: List my registrations
  description: All event registrations for the authenticated user.
  tags:
  - registrations
  authenticated: true
  rateLimit: read_heavy — 300/min
  responses:
  - status: 200
    description: Registrations
    example:
      results:
      - event_title: Tech Meetup
        status: confirmed
- id: comments-list
  method: GET
  urlPath: /api/v2/events/{event_slug}/comments/
  summary: List event comments
  description: Threaded comments for an event (public read).
  tags:
  - comments
  authenticated: false
  rateLimit: read_heavy — 300/min
  parameters:
  - name: event_slug
    in: path
    type: string
    required: true
    description: Event slug
    example: tech-meetup
  responses:
  - status: 200
    description: Comments
    example:
      results:
      - id: 1
        body: Looking forward to it!
        author_username: jane
- id: comments-create
  method: POST
  urlPath: /api/v2/events/{event_slug}/comments/
  summary: Post comment
  description: Authenticated user comments on event if allowed.
  tags:
  - comments
  authenticated: true
  rateLimit: write_standard — 60/min
  parameters:
  - name: event_slug
    in: path
    type: string
    required: true
    description: Event slug
    example: tech-meetup
  requestBody:
    contentType: application/json
    schema:
      body: string
      parent_id: integer
    example:
      body: See you there!
  responses:
  - status: 201
    description: Comment created
    example:
      id: 2
      body: See you there!
- id: comments-like
  method: POST
  urlPath: /api/v2/events/{event_slug}/comments/{comment_id}/like/
  summary: Like comment
  description: Authenticated user likes a comment.
  tags:
  - comments
  authenticated: true
  rateLimit: write_standard — 60/min
  parameters:
  - name: event_slug
    in: path
    type: string
    required: true
    description: Event slug
    example: tech-meetup
  - name: comment_id
    in: path
    type: integer
    required: true
    description: Comment ID
    example: 1
  responses:
  - status: 201
    description: Liked
    example:
      likes_count: 5
- id: notifications-list
  method: GET
  urlPath: /api/v2/notifications/
  summary: List notifications
  description: In-app notifications for authenticated user.
  tags:
  - notifications
  authenticated: true
  rateLimit: read_heavy — 300/min
  responses:
  - status: 200
    description: Notifications
    example:
      results:
      - id: 1
        title: Registration confirmed
        is_read: false
- id: notifications-mark-read
  method: POST
  urlPath: /api/v2/notifications/{notification_id}/read/
  summary: Mark notification read
  description: Marks single notification as read.
  tags:
  - notifications
  authenticated: true
  rateLimit: write_standard — 60/min
  parameters:
  - name: notification_id
    in: path
    type: integer
    required: true
    description: Notification ID
    example: 1
  responses:
  - status: 200
    description: Marked read
    example:
      is_read: true
- id: notifications-mark-all
  method: POST
  urlPath: /api/v2/notifications/mark-all-read/
  summary: Mark all notifications read
  description: Bulk mark all user notifications as read.
  tags:
  - notifications
  authenticated: true
  rateLimit: write_standard — 60/min
  responses:
  - status: 200
    description: All marked
    example:
      updated_count: 12
- id: task-status
  method: GET
  urlPath: /api/task-status/{task_id}/
  summary: Celery task status
  description: Poll async task result by Celery task ID.
  tags:
  - service
  authenticated: false
  rateLimit: Exempt
  parameters:
  - name: task_id
    in: path
    type: string
    required: true
    description: Celery task UUID
    example: a1b2c3d4-e5f6-7890-abcd-ef1234567890
  responses:
  - status: 200
    description: Task state
    example:
      task_id: a1b2...
      status: SUCCESS
      result:
        ok: true
---

# API Schema

> **Base URL (production placeholder):** `https://api.socialevents.placeholder.example.com`

> **Auth header:** `Authorization: Bearer <access_token>` for protected routes.

> **Highlight:** Interactive docs at `/api/docs/` (drf-spectacular). This file documents representative routes; the OpenAPI schema lists every ViewSet action.

> **Warning:** `/api/task-revoke/` and `/api/celery-health/` are unauthenticated—lock down in production.

> **Warning:** Organization ViewSet defaults to AllowAny—treat as known gap before go-live.

> **Useful:** Redis-backed throttles use cache keys prefixed with `social-events-api:` on Upstash.
