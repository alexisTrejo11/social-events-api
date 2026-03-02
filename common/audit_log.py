import time
import json
import logging

audit_logger = logging.getLogger("audit")

SENSITIVE_FIELDS = {"password", "token", "access", "refresh"}


def sanitize_data(data):
    if not isinstance(data, dict):
        return None

    return {
        key: ("***" if key.lower() in SENSITIVE_FIELDS else value)
        for key, value in data.items()
    }


class AuditLogMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration_ms = round((time.time() - start_time) * 1000, 2)

        try:
            request_body = None
            if request.body:
                try:
                    request_body = sanitize_data(
                        json.loads(request.body.decode("utf-8"))
                    )
                except Exception:
                    request_body = None

            user = (
                request.user.id
                if hasattr(request, "user") and request.user.is_authenticated
                else None
            )

            audit_logger.info(
                json.dumps(
                    {
                        "method": request.method,
                        "path": request.get_full_path(),
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                        "user_id": user,
                        "ip": self.get_client_ip(request),
                        "request_body": request_body,
                    }
                )
            )
        except Exception:
            pass

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")
