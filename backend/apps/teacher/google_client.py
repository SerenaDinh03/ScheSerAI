import logging

from django.conf import settings
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"


class GoogleNotConnectedError(Exception):
    """Giáo viên chưa kết nối Google Calendar (chưa có refresh token)."""


def _client_config() -> dict:
    return {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": AUTH_URI,
            "token_uri": TOKEN_URI,
        }
    }


def build_flow() -> Flow:
    return Flow.from_client_config(
        _client_config(), scopes=SCOPES, redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI
    )


def get_authorization_url() -> tuple[str, str]:
    flow = build_flow()
    # access_type=offline + prompt=consent để chắc chắn Google trả về refresh_token
    # (mặc định Google chỉ trả refresh_token ở lần cấp quyền đầu tiên).
    return flow.authorization_url(
        access_type="offline", prompt="consent", include_granted_scopes="true"
    )


def exchange_code(code: str) -> Credentials:
    flow = build_flow()
    flow.fetch_token(code=code)
    return flow.credentials


def fetch_account_email(credentials: Credentials) -> str:
    service = build("oauth2", "v2", credentials=credentials, cache_discovery=False)
    info = service.userinfo().get().execute()
    return info.get("email", "")


def get_calendar_service(teacher):
    """Trả về Google Calendar API client cho teacher, tự refresh access token."""
    refresh_token = teacher.get_google_refresh_token()
    if not refresh_token:
        raise GoogleNotConnectedError("Giáo viên chưa kết nối Google Calendar.")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )
    creds.refresh(GoogleAuthRequest())
    return build("calendar", "v3", credentials=creds, cache_discovery=False)
