from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from events.views.user_views import UserViewSet, UserPreferencesView
from events.views.auth_views import AuthView
from events.views.category_views import CategoryViewSet
from events.views.event_views import EventViewSet
from events.views.registration_views import RegistrationViewSet
from events.views.comment_views import CommentViewSet

comment_router = DefaultRouter()
comment_router.register(r'comments', CommentViewSet, basename='comment')

user_router = DefaultRouter()
user_router.register(r'users', UserViewSet)

category_router = DefaultRouter()
category_router.register(r'categories', CategoryViewSet, basename='category')

event_router = DefaultRouter()
event_router.register(r'events', EventViewSet, basename='event')

registration_router = DefaultRouter()
registration_router.register(r'registrations', RegistrationViewSet, basename='registration')

auth_router = DefaultRouter()
auth_router.register(r'auth', AuthView, basename='auth')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('preferences/', UserPreferencesView.as_view(), name='user-preferences'),

    path('', include(user_router.urls)),
    path('', include(auth_router.urls)),
    path('', include(category_router.urls)),
    path('', include(event_router.urls)),
    path('', include(registration_router.urls)),
    path('', include(comment_router.urls)),
]
