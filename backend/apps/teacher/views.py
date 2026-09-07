from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import google_client
from .models import Teacher


@method_decorator(ensure_csrf_cookie, name="get")
class CsrfView(APIView):
    """SPA gọi 1 lần khi khởi động để trình duyệt nhận cookie csrftoken -
    cần cho các request POST/PATCH/DELETE sau khi đăng nhập (US: bảo vệ CSRF
    cho phiên làm việc qua session, xem SessionAuthentication.enforce_csrf)."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"detail": "CSRF cookie set"})


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Sai tên đăng nhập hoặc mật khẩu."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user)
        return Response({"username": user.username})


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        teacher = Teacher.load()
        return Response(
            {
                "username": request.user.username,
                "name": teacher.name,
                "email": teacher.email,
            }
        )


class GoogleConnectView(APIView):
    def get(self, request):
        auth_url, state, code_verifier = google_client.get_authorization_url()
        request.session["google_oauth_state"] = state
        request.session["google_oauth_code_verifier"] = code_verifier
        return HttpResponseRedirect(auth_url)


class GoogleCallbackView(APIView):
    """Google redirect thẳng trình duyệt về đây sau màn hình cấp quyền - nên kết
    quả (thành công lẫn lỗi) phải trả về bằng redirect sang frontend, không phải
    JSON thô (người dùng sẽ nhìn thấy trang này trực tiếp, không phải gọi qua fetch)."""

    def _redirect_to_frontend(self, **params):
        query = urlencode(params)
        return HttpResponseRedirect(f"{settings.FRONTEND_URL}/?{query}")

    def get(self, request):
        error = request.query_params.get("error")
        if error:
            return self._redirect_to_frontend(google_error=f"Google từ chối cấp quyền: {error}")

        state = request.query_params.get("state")
        session_state = request.session.get("google_oauth_state")
        if not state or state != session_state:
            return self._redirect_to_frontend(
                google_error="State không hợp lệ, vui lòng thử kết nối lại."
            )

        code = request.query_params.get("code")
        if not code:
            return self._redirect_to_frontend(google_error="Thiếu mã xác thực từ Google.")

        code_verifier = request.session.get("google_oauth_code_verifier")

        try:
            credentials = google_client.exchange_code(code, code_verifier)
        except Exception as exc:
            return self._redirect_to_frontend(google_error=f"Không thể trao đổi mã xác thực: {exc}")

        if not credentials.refresh_token:
            return self._redirect_to_frontend(
                google_error=(
                    "Google không trả về refresh token. Vào Google Account > Bảo mật > "
                    "Ứng dụng của bên thứ ba, gỡ quyền truy cập của ứng dụng này rồi thử "
                    "kết nối lại."
                )
            )

        teacher = Teacher.load()
        teacher.set_google_refresh_token(credentials.refresh_token)
        # Ưu tiên calendar "Teaching" nếu giáo viên đã có sẵn (thói quen dùng
        # trước khi có ScheSerAI) - không thì mới rơi về "primary".
        teacher.google_calendar_id = (
            google_client.find_calendar_id_by_name(credentials, "Teaching") or "primary"
        )
        teacher.google_account_email = google_client.fetch_account_email(credentials)
        teacher.google_last_sync_error = ""
        teacher.save()

        return self._redirect_to_frontend(google_connected=teacher.google_account_email)


class GoogleStatusView(APIView):
    def get(self, request):
        teacher = Teacher.load()
        return Response(
            {
                "connected": teacher.is_google_connected,
                "email": teacher.google_account_email,
                "last_sync_at": teacher.google_last_sync_at,
                "last_sync_error": teacher.google_last_sync_error or None,
            }
        )


class GoogleDisconnectView(APIView):
    def post(self, request):
        teacher = Teacher.load()
        teacher.disconnect_google()
        return Response(status=status.HTTP_204_NO_CONTENT)
