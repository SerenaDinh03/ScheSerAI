import logging

logger = logging.getLogger(__name__)


def delete_calendar_event(google_event_id: str) -> None:
    """Stub seam for Epic 1 (tích hợp Google Calendar OAuth/API).

    TODO(Epic 1): gọi Google Calendar API để xóa event google_event_id,
    dùng credentials từ Teacher.load() (google_refresh_token/google_calendar_id).
    Hiện tại chỉ log để EPIC 2 (US 2.5) không bị chặn bởi việc chưa có tích hợp
    Calendar thật.
    """
    logger.info("delete_calendar_event stub called for google_event_id=%s", google_event_id)


def update_calendar_event(google_event_id: str, session) -> None:
    """Stub seam for Epic 1 - cập nhật event đã có, không tạo mới (US 5.1).

    TODO(Epic 1): gọi Google Calendar API update event google_event_id với
    session.session_date/start_time/end_time mới.
    """
    logger.info(
        "update_calendar_event stub called for google_event_id=%s new_date=%s new_start=%s",
        google_event_id,
        session.session_date,
        session.start_time,
    )
