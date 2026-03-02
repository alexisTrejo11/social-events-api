from django.apps import AppConfig


class RegistrationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.registrations"

    def ready(self):
        """Import signals when app is ready."""
        import apps.registrations.signals  # noqa: F401
