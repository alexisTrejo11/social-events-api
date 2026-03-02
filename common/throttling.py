import hashlib
import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse

from rest_framework.throttling import SimpleRateThrottle

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Global rate limit middleware. Sits at the Django layer, before DRF.

    Limits:
        - Unauthenticated:  200 requests / minute  (IP-based)
        - Authenticated:   1000 requests / minute  (user-id-based)

    Behavior on Redis failure:
        Logs the error and ALLOWS the request through (fail-open).
        This is intentional — a Redis outage should not take down the API.
        Change to fail-closed if your use case requires it.

    Headers returned on every response:
        X-RateLimit-Limit     — max requests allowed in the window
        X-RateLimit-Remaining — requests left in the current window
        X-RateLimit-Reset     — Unix timestamp when the window resets
    """

    # (limit, window_seconds)
    ANON_LIMIT = (200, 60)
    AUTH_LIMIT = (1000, 60)

    # Paths that bypass the middleware entirely
    EXEMPT_PATHS = {
        "/health/",
        "/api/schema/",
        "/api/docs/",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in self.EXEMPT_PATHS:
            return self.get_response(request)

        limit, window = self._get_limit(request)
        cache_key = self._build_key(request)

        allowed, remaining, reset_at = self._check_limit(cache_key, limit, window)

        if not allowed:
            response = JsonResponse(
                {
                    "error": {
                        "code": "rate_limit_exceeded",
                        "message": "Too many requests. Please slow down.",
                        "detail": None,
                    }
                },
                status=429,
            )
            self._set_headers(response, limit, 0, reset_at)
            return response

        response = self.get_response(request)
        self._set_headers(response, limit, remaining, reset_at)
        return response

    def _get_limit(self, request):
        if hasattr(request, "user") and request.user.is_authenticated:
            return self.AUTH_LIMIT
        return self.ANON_LIMIT

    def _build_key(self, request) -> str:
        """
        Authenticated  → keyed by user id (fair across IPs, handles proxies).
        Anonymous      → keyed by IP address.
        """
        if hasattr(request, "user") and request.user.is_authenticated:
            identifier = f"user:{request.user.pk}"
        else:
            identifier = f"ip:{self._get_ip(request)}"

        # Hash so keys are a fixed length regardless of IPv6 or UUID length
        hashed = hashlib.sha256(identifier.encode()).hexdigest()
        return f"rl:global:{hashed}"

    def _get_ip(self, request) -> str:
        """Handles X-Forwarded-For from reverse proxies (nginx, load balancers)."""
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            # Take the first IP — the original client
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

    def _check_limit(self, key: str, limit: int, window: int):
        """
        Sliding window counter using Redis INCR + EXPIRE.

        Returns:
            allowed   (bool)
            remaining (int)
            reset_at  (int) — Unix timestamp
        """
        reset_at = int(time.time()) + window

        try:
            count = cache.get(key)

            if count is None:
                # First request in this window
                cache.set(key, 1, timeout=window)
                return True, limit - 1, reset_at

            count = int(count)

            if count >= limit:
                return False, 0, reset_at

            # Increment without resetting the TTL
            cache.incr(key)
            return True, limit - count - 1, reset_at

        except Exception as exc:
            # Redis is unavailable — fail open, log the error
            logger.error("RateLimitMiddleware: cache error, failing open. %s", exc)
            return True, limit, reset_at

    @staticmethod
    def _set_headers(response, limit: int, remaining: int, reset_at: int):
        response["X-RateLimit-Limit"] = str(limit)
        response["X-RateLimit-Remaining"] = str(max(remaining, 0))
        response["X-RateLimit-Reset"] = str(reset_at)


class _BaseThrottle(SimpleRateThrottle):
    """
    Base class for all custom throttles.
    Overrides get_cache_key to prefix by scope so different
    throttles never collide in Redis.
    """

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }


class AuthenticatedUserThrottle(_BaseThrottle):
    """1000 requests/day for any authenticated user — global safety net."""

    scope = "authenticated"


class AnonThrottle(_BaseThrottle):
    """100 requests/day for unauthenticated clients — global safety net."""

    scope = "anon"


class AuthActionsThrottle(_BaseThrottle):
    """
    10 requests / minute.
    Use on: POST /auth/register/, POST /auth/login/,
            POST /auth/password/reset/, POST /auth/verify-email/
    """

    scope = "auth_actions"


class ReadHeavyThrottle(_BaseThrottle):
    """
    300 requests / minute.
    Use on: GET /events/, GET /organizations/, GET /users/{username}/
    """

    scope = "read_heavy"


class WriteStandardThrottle(_BaseThrottle):
    """
    60 requests / minute.
    Use on: POST /events/{slug}/comments/, POST /users/{username}/follow/,
            POST /events/{slug}/favorite/
    """

    scope = "write_standard"


class WriteSensitiveThrottle(_BaseThrottle):
    """
    20 requests / minute.
    Use on: POST /events/, POST /organizations/, PATCH /users/me/
    """

    scope = "write_sensitive"


class SearchThrottle(_BaseThrottle):
    """
    30 requests / minute.
    Use on: GET /events/?search=..., GET /tags/, GET /categories/
    """

    scope = "search"


class RegistrationThrottle(_BaseThrottle):
    """
    10 requests / minute.
    Use on: POST /events/{slug}/register/
    """

    scope = "registration"


class CheckInThrottle(_BaseThrottle):
    """
    120 requests / minute.
    Use on: POST /events/{slug}/registrations/{id}/check-in/
    """

    scope = "check_in"


class NotificationReadThrottle(_BaseThrottle):
    """
    60 requests / minute.
    Use on: GET /notifications/, PATCH /notifications/{id}/read/
    """

    scope = "notification_read"
