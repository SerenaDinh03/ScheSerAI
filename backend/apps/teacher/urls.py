from django.urls import path

from .views import (
    CsrfView,
    GoogleCallbackView,
    GoogleConnectView,
    GoogleDisconnectView,
    GoogleStatusView,
    LoginView,
    LogoutView,
    MeView,
)

urlpatterns = [
    path("auth/csrf/", CsrfView.as_view(), name="auth-csrf"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("google/connect/", GoogleConnectView.as_view(), name="google-connect"),
    path("google/callback/", GoogleCallbackView.as_view(), name="google-callback"),
    path("google/status/", GoogleStatusView.as_view(), name="google-status"),
    path("google/disconnect/", GoogleDisconnectView.as_view(), name="google-disconnect"),
]
