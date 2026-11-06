from django.urls import path
from .views import *

app_name = "ProfilePageApp"

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
    path("get-profile/<int:profile_id>/", GetProfileView.as_view(), name="get-profile"),
    path(
        "search-profile/<str:search_text>/",
        GetTextSearchProfileView.as_view(),
        name="search-profile",
    ),
    path(
        "edit-profile/<int:profile_id>/", EditProfileView.as_view(), name="edit-profile"
    ),
    path(
        "delete-profile/<int:profile_id>/",
        DeleteProfileView.as_view(),
        name="delete-profile",
    ),
    path(
        "toggle-follow-profile/<int:profile_id>/",
        ToggleFollowProfileView.as_view(),
        name="toggle-follow-profile",
    ),
    path(
        "toggle-block-profile/<int:profile_id>/",
        ToggleBlockProfileView.as_view(),
        name="toggle-block-profile",
    ),
    path(
        "profiles-following-symmetric/",
        GetSymmetricFollowedProfilesView.as_view(),
        name="profiles-following-symmetric",
    ),
    path(
        "profiles-messaging/",
        GetMessagingProfilesView.as_view(),
        name="profiles-messaging",
    ),
    path(
        "owned-chapters-and-portfolios/",
        GetOwnedChaptersAndPortfoliosView.as_view(),
        name="owned-chapters-and-portfolios",
    ),
    path("message/", ProfileMessageView.as_view(), name="profile-message"),
    path(
        "send-message/<int:profile_id>/",
        CreateProfileMessageView.as_view(),
        name="create-profile-message",
    ),
    path(
        "get-messages/<int:profile_id>/",
        GetProfileMessageView.as_view(),
        name="get-profile-messages",
    ),
    path(
        "read-messages/<int:profile_id>/<int:last_message_id>/",
        ReadProfileMessageView.as_view(),
        name="read-profile-messages",
    ),
    # For register/login/logout
    path("csrf/", CsrfTokenView.as_view(), name="csrf"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("verify/<str:token>/", VerifyView.as_view(), name="verify"),
    path(
        "reset-verification/",
        ResetVerificationView.as_view(),
        name="reset-verification",
    ),
    path("google-auth/", GoogleAuthView.as_view(), name="google-auth"),
]
