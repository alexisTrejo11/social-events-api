from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from events.views.user_views import UserViewSet, UserPreferencesView
from events.views.auth_views import AuthView
from events.views.category_views import CategoryViewSet
from events.views.event_command_views import EventCommandViewSet
from events.views.event_query_views import EventQueryViewSet
from events.views.registration_views import RegistrationViewSet
from events.views.comment_views import CommentViewSet
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

comment_router = DefaultRouter()
comment_router.register(r'comments', CommentViewSet, basename='comment')

user_router = DefaultRouter()
user_router.register(r'users', UserViewSet)

category_router = DefaultRouter()
category_router.register(r'categories', CategoryViewSet, basename='category')

event_router = DefaultRouter()
event_router.register(r'events/commands', EventCommandViewSet, basename='event-commands')
event_router.register(r'events/queries', EventQueryViewSet, basename='event-queries')

registration_router = DefaultRouter()
registration_router.register(r'registrations', RegistrationViewSet, basename='registration')

auth_router = DefaultRouter()
auth_router.register(r'auth', AuthView, basename='auth')

schema_view = get_schema_view(
    openapi.Info(
        title="Social Events API",
        default_version='v1',
        description="API Documentation for Social Event Management",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="marcoalexispt.02@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('preferences/', UserPreferencesView.as_view(), name='user-preferences'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),


    path('', include(user_router.urls)),
    path('', include(auth_router.urls)),
    path('', include(category_router.urls)),
    path('', include(event_router.urls)),
    path('', include(registration_router.urls)),
    path('', include(comment_router.urls)),
]
