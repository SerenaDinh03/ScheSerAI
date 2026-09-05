from django.http import HttpResponseRedirect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import google_client
from .models import Teacher


class GoogleConnectView(APIView):
    def get(self, request):
        auth_url, state = google_client.get_authorization_url()
        request.session["google_oauth_state"] = state
        return HttpResponseRedirect(auth_url)


class GoogleCallbackView(APIView):
    def get(self, request):
        error = request.query_params.get("error")
        if error:
            return Response(
                {"detail": f"Google từ chối cấp quyền: {error}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        state = request.query_params.get("state")
        session_state = request.session.get("google_oauth_state")
        if not state or state != session_state:
            return Response(
                {"detail": "State không hợp lệ, vui lòng thử kết nối lại."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        code = request.query_params.get("code")
        if not code:
            return Response(
                {"detail": "Thiếu mã xác thực từ Google."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            credentials = google_client.exchange_code(code)
        except Exception as exc:
            return Response(
                {"detail": f"Không thể trao đổi mã xác thực: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not credentials.refresh_token:
            return Response(
                {
                    "detail": (
                        "Google không trả về refresh token. Vào Google Account > Bảo mật > "
                        "Ứng dụng của bên thứ ba, gỡ quyền truy cập của ứng dụng này rồi thử "
                        "kết nối lại."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        teacher = Teacher.load()
        teacher.set_google_refresh_token(credentials.refresh_token)
        teacher.google_calendar_id = "primary"
        teacher.google_account_email = google_client.fetch_account_email(credentials)
        teacher.google_last_sync_error = ""
        teacher.save()

        return Response({"connected": True, "email": teacher.google_account_email})


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
