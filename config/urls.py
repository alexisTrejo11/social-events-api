"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from common.view import task_status, revoke_task, celery_health, test

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API v2
    path("api/v2/", include("apps.users.urls")),
    path("api/v2/", include("apps.organizations.urls")),
    path("api/v2/", include("apps.locations.urls")),
    path("api/v2/", include("apps.events.urls")),
    path("api/v2/", include("apps.registrations.urls")),
    path("api/v2/", include("apps.comments.urls")),
    path("api/v2/notifications/", include("apps.notifications.urls")),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # Testing & Monitoring
    path("api/test/", test, name="test"),
    path("api/task-status/<str:task_id>/", task_status, name="task-status"),
    path("api/task-revoke/<str:task_id>/", revoke_task, name="task-revoke"),
    path("api/celery-health/", celery_health, name="celery-health"),
    # Allauth (for OAuth administration)
    path("accounts/", include("allauth.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
