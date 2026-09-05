from django.urls import path

from .views import GoogleCallbackView, GoogleConnectView, GoogleDisconnectView, GoogleStatusView

urlpatterns = [
    path("google/connect/", GoogleConnectView.as_view(), name="google-connect"),
    path("google/callback/", GoogleCallbackView.as_view(), name="google-callback"),
    path("google/status/", GoogleStatusView.as_view(), name="google-status"),
    path("google/disconnect/", GoogleDisconnectView.as_view(), name="google-disconnect"),
]
