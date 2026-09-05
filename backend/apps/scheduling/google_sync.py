import logging
from datetime import datetime

from django.utils import timezone

logger = logging.getLogger(__name__)


def _parse_event_times(event: dict):
    """Trả về (date, start_time, end_time) từ 1 event Google, hoặc (None, None, None)
    nếu là all-day event (không có dateTime) - không thuộc phạm vi hệ thống này."""
    start_raw = event.get("start", {}).get("dateTime")
    end_raw = event.get("end", {}).get("dateTime")
    if not start_raw or not end_raw:
        return None, None, None
    start_dt = timezone.localtime(datetime.fromisoformat(start_raw))
    end_dt = timezone.localtime(datetime.fromisoformat(end_raw))
    return (
        start_dt.date(),
        start_dt.time().replace(microsecond=0),
        end_dt.time().replace(microsecond=0),
    )


def poll_google_calendar() -> dict:
    """Đồng bộ ngược Calendar -> hệ thống bằng polling + sync token (US 1.4).

    Chỉ áp dụng cho event do chính hệ thống tạo (khớp google_event_id với 1
    Session). Cập nhật Session bằng queryset.update() trực tiếp thay vì gọi
    Session.reschedule()/cancel() - 2 hàm đó lại đẩy ngược thay đổi lên Google,
    tách riêng đường vào (từ Google) và đường ra (lên Google) là cách chống
    vòng lặp đồng bộ ở đây.
    """
    from googleapiclient.errors import HttpError

    from apps.notifications.models import Notification
    from apps.teacher.google_client import GoogleNotConnectedError, get_calendar_service
    from apps.teacher.models import Teacher

    from .models import Session

    teacher = Teacher.load()
    try:
        service = get_calendar_service(teacher)
    except GoogleNotConnectedError:
        return {"skipped": "not_connected"}

    calendar_id = teacher.google_calendar_id or "primary"
    sync_token = teacher.google_sync_token or None

    list_kwargs = {"calendarId": calendar_id, "singleEvents": True}
    if sync_token:
        list_kwargs["syncToken"] = sync_token
    else:
        list_kwargs["timeMin"] = timezone.now().isoformat()

    events = []
    next_sync_token = None
    page_token = None
    try:
        while True:
            if page_token:
                list_kwargs["pageToken"] = page_token
            resp = service.events().list(**list_kwargs).execute()
            events.extend(resp.get("items", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                next_sync_token = resp.get("nextSyncToken")
                break
    except HttpError as exc:
        if exc.resp.status == 410:
            # sync token hết hạn/không hợp lệ -> reset và full resync
            teacher.google_sync_token = ""
            teacher.save(update_fields=["google_sync_token"])
            return poll_google_calendar()
        teacher.google_last_sync_error = str(exc)
        teacher.save(update_fields=["google_last_sync_error"])
        raise

    updated_count = 0
    deleted_count = 0
    for event in events:
        session = (
            Session.objects.filter(google_event_id=event["id"])
            .select_related("student")
            .first()
        )
        if not session:
            continue

        if event.get("status") == "cancelled":
            Notification.objects.create(
                teacher=teacher,
                message=(
                    f"Buổi học của {session.student.name} ngày "
                    f"{session.session_date.strftime('%d/%m/%Y')} đã bị xóa trên Google Calendar."
                ),
            )
            session.delete()
            deleted_count += 1
            continue

        new_date, new_start, new_end = _parse_event_times(event)
        if new_date is None:
            continue

        if (new_date, new_start, new_end) != (session.session_date, session.start_time, session.end_time):
            Session.objects.filter(pk=session.pk).update(
                session_date=new_date,
                start_time=new_start,
                end_time=new_end,
                status=Session.Status.RESCHEDULED,
            )
            Notification.objects.create(
                teacher=teacher,
                message=(
                    f"Buổi học của {session.student.name} đã được đổi giờ trên Google Calendar "
                    f"sang {new_date.strftime('%d/%m/%Y')} {new_start.strftime('%H:%M')}."
                ),
            )
            updated_count += 1

    teacher.google_sync_token = next_sync_token or teacher.google_sync_token
    teacher.google_last_sync_at = timezone.now()
    teacher.google_last_sync_error = ""
    teacher.save(
        update_fields=["google_sync_token", "google_last_sync_at", "google_last_sync_error"]
    )
    return {"updated": updated_count, "deleted": deleted_count}
