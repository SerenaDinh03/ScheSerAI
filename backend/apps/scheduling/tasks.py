"""Entry point cho các job định kỳ chạy qua django-q2 (xem management command
bootstrap_scheduled_jobs)."""

from .models import Schedule


def generate_upcoming_sessions() -> None:
    """Job hàng ngày: mở rộng cửa sổ sinh Session 4-8 tuần tới cho mọi lịch active (US 1.2)."""
    for schedule in Schedule.objects.filter(is_active=True):
        schedule.generate_sessions()


def sync_google_calendar() -> dict:
    """Job định kỳ: polling đồng bộ ngược từ Google Calendar (US 1.4)."""
    from .google_sync import poll_google_calendar

    return poll_google_calendar()
