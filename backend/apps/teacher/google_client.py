import logging

from django.conf import settings
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    # Chỉ để đọc danh sách calendar lúc kết nối (tìm calendar "Teaching" nếu có) -
    # calendar.events không đủ quyền gọi calendarList().list().
    "https://www.googleapis.com/auth/calendar.calendarlist.readonly",
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


def build_flow(code_verifier: str | None = None) -> Flow:
    flow = Flow.from_client_config(
        _client_config(), scopes=SCOPES, redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI
    )
    if code_verifier:
        flow.code_verifier = code_verifier
    return flow


def get_authorization_url() -> tuple[str, str, str]:
    flow = build_flow()
    # access_type=offline + prompt=consent để chắc chắn Google trả về refresh_token
    # (mặc định Google chỉ trả refresh_token ở lần cấp quyền đầu tiên).
    auth_url, state = flow.authorization_url(
        access_type="offline", prompt="consent", include_granted_scopes="true"
    )
    # Flow tự sinh PKCE code_verifier khi build authorization_url (thể hiện qua
    # code_challenge trong URL) - phải lưu lại để dùng đúng flow đó lúc đổi mã ở
    # exchange_code(), vì mỗi request là 1 Flow instance mới, không tự nhớ nhau.
    return auth_url, state, flow.code_verifier


def exchange_code(code: str, code_verifier: str) -> Credentials:
    flow = build_flow(code_verifier=code_verifier)
    flow.fetch_token(code=code)
    return flow.credentials


def fetch_account_email(credentials: Credentials) -> str:
    service = build("oauth2", "v2", credentials=credentials, cache_discovery=False)
    info = service.userinfo().get().execute()
    return info.get("email", "")


def find_calendar_id_by_name(credentials: Credentials, name: str) -> str | None:
    """Tìm calendar theo tên hiển thị (không phân biệt hoa/thường) trong danh sách
    calendar của giáo viên - dùng lúc kết nối để ưu tiên 1 calendar có sẵn (vd
    "Teaching") thay vì luôn tạo event vào calendar "primary" mặc định."""
    service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
    calendar_list = service.calendarList().list().execute()
    for entry in calendar_list.get("items", []):
        if entry.get("summary", "").strip().lower() == name.strip().lower():
            return entry["id"]
    return None


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
