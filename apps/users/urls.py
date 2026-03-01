from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.views import (
    # Auth
    RegisterView,
    LoginView,
    LogoutView,
    VerifyEmailView,
    ResendVerificationView,
    PasswordChangeView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    # Profile
    UserProfileView,
    DeactivateAccountView,
    PublicUserProfileView,
    UserPreferencesView,
    # Social
    UserFollowersView,
    UserFollowingView,
    FollowUserView,
    UnfollowUserView,
    UserFeedView,
)

urlpatterns = [
    # ========================================================================
    # Authentication
    # ========================================================================
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('auth/resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    path('auth/password/change/', PasswordChangeView.as_view(), name='password-change'),
    path('auth/password/reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('auth/password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # ========================================================================
    # User Profile
    # ========================================================================
    path('users/me/', UserProfileView.as_view(), name='user-profile'),
    path('users/me/deactivate/', DeactivateAccountView.as_view(), name='deactivate-account'),
    path('users/me/preferences/', UserPreferencesView.as_view(), name='user-preferences'),
    path('users/<str:username>/', PublicUserProfileView.as_view(), name='public-user-profile'),
    
    # ========================================================================
    # Social
    # ========================================================================
    path('users/<str:username>/followers/', UserFollowersView.as_view(), name='user-followers'),
    path('users/<str:username>/following/', UserFollowingView.as_view(), name='user-following'),
    path('users/<str:username>/follow/', FollowUserView.as_view(), name='follow-user'),
    path('users/<str:username>/follow/', UnfollowUserView.as_view(), name='unfollow-user'),
    path('users/me/feed/', UserFeedView.as_view(), name='user-feed'),
]
