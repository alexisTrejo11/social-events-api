from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    method = models.CharField(max_length=10)
    path = models.TextField()
    status_code = models.IntegerField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    duration_ms = models.FloatField()
    request_body = models.JSONField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code}"
