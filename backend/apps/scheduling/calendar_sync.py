import logging
from contextlib import contextmanager
from datetime import datetime

from django.utils import timezone

logger = logging.getLogger(__name__)


def _event_body(session) -> dict:
    tz_name = timezone.get_current_timezone_name()
    start_dt = timezone.make_aware(datetime.combine(session.session_date, session.start_time))
    end_dt = timezone.make_aware(datetime.combine(session.session_date, session.end_time))
    return {
        "summary": f"Học: {session.student.name}",
        "start": {"dateTime": start_dt.isoformat(), "timeZone": tz_name},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": tz_name},
    }


def _calendar_id(teacher) -> str:
    return teacher.google_calendar_id or "primary"


def _record_sync_success(teacher) -> None:
    teacher.google_last_sync_at = timezone.now()
    teacher.google_last_sync_error = ""
    teacher.save(update_fields=["google_last_sync_at", "google_last_sync_error"])


def _record_sync_error(teacher, exc: Exception) -> None:
    logger.warning("Google Calendar sync error: %s", exc)
    teacher.google_last_sync_error = str(exc)
    teacher.save(update_fields=["google_last_sync_error"])


@contextmanager
def _calendar_service(teacher):
    """Yield Calendar API service cho teacher, hoặc None nếu chưa kết nối/lỗi -
    gom lại phần try/except từng lặp lại ở mọi hàm gọi API bên dưới."""
    from apps.teacher.google_client import GoogleNotConnectedError, get_calendar_service

    try:
        service = get_calendar_service(teacher)
    except GoogleNotConnectedError:
        yield None
        return
    except Exception as exc:
        _record_sync_error(teacher, exc)
        yield None
        return
    yield service


def _execute(teacher, request, ignore_statuses: tuple = ()):
    """Chạy 1 request Calendar API và ghi lại kết quả sync (thành công/lỗi).

    ignore_statuses: mã HTTP coi như "không phải lỗi" (vd 404/410 khi event đã
    không còn tồn tại) - vẫn ghi nhận là sync thành công.
    """
    from googleapiclient.errors import HttpError

    try:
        result = request.execute()
        _record_sync_success(teacher)
        return result
    except HttpError as exc:
        if exc.resp.status in ignore_statuses:
            _record_sync_success(teacher)
            return None
        _record_sync_error(teacher, exc)
        return None


def create_calendar_event(session) -> str:
    """Tạo event Google Calendar cho 1 Session mới (US 1.2). Trả về "" nếu chưa
    kết nối Google hoặc gọi API thất bại - không chặn việc tạo Session cục bộ."""
    from apps.teacher.models import Teacher

    teacher = Teacher.load()
    with _calendar_service(teacher) as service:
        if service is None:
            return ""
        request = service.events().insert(
            calendarId=_calendar_id(teacher), body=_event_body(session)
        )
        result = _execute(teacher, request)
        return result.get("id", "") if result else ""


def update_calendar_event(google_event_id: str, session) -> None:
    """Cập nhật event đã có, không tạo mới (US 5.1)."""
    from apps.teacher.models import Teacher

    teacher = Teacher.load()
    with _calendar_service(teacher) as service:
        if service is None:
            return
        request = service.events().update(
            calendarId=_calendar_id(teacher), eventId=google_event_id, body=_event_body(session)
        )
        _execute(teacher, request)


def delete_calendar_event(google_event_id: str) -> None:
    """Xóa event trên Calendar (US 2.5, US 5.2)."""
    from apps.teacher.models import Teacher

    teacher = Teacher.load()
    with _calendar_service(teacher) as service:
        if service is None:
            return
        request = service.events().delete(
            calendarId=_calendar_id(teacher), eventId=google_event_id
        )
        # 404/410 = event đã không còn trên Calendar (vd vừa bị đồng bộ ngược) - không phải lỗi.
        _execute(teacher, request, ignore_statuses=(404, 410))
