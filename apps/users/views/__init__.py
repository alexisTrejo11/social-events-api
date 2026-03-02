from .auth_views import (
    RegisterView,
    LoginView,
    LogoutView,
    VerifyEmailView,
    ResendVerificationView,
    PasswordChangeView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)
from .user_profile_views import (
    UserProfileView,
    DeactivateAccountView,
    PublicUserProfileView,
    UserPreferencesView,
)
from .social_views import (
    UserFollowersView,
    UserFollowingView,
    FollowUserView,
    UnfollowUserView,
    UserFeedView,
)
from .oauth_views import (
    GoogleLoginView,
    GitHubLoginView,
    ListSocialAccountsView,
    DisconnectSocialAccountView,
)

__all__ = [
    # Auth
    "RegisterView",
    "LoginView",
    "LogoutView",
    "VerifyEmailView",
    "ResendVerificationView",
    "PasswordChangeView",
    "PasswordResetRequestView",
    "PasswordResetConfirmView",
    # Profile
    "UserProfileView",
    "DeactivateAccountView",
    "PublicUserProfileView",
    "UserPreferencesView",
    # Social
    "UserFollowersView",
    "UserFollowingView",
    "FollowUserView",
    "UnfollowUserView",
    "UserFeedView",
    # OAuth
    "GoogleLoginView",
    "GitHubLoginView",
    "ListSocialAccountsView",
    "DisconnectSocialAccountView",
]
