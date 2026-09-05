from django.core.management.base import BaseCommand
from django_q.models import Schedule as QSchedule


class Command(BaseCommand):
    help = (
        "Đăng ký (idempotent) các job định kỳ chạy qua django-q2: sinh Session "
        "trước 4-8 tuần (US 1.2) và polling đồng bộ ngược Google Calendar (US 1.4)."
    )

    def handle(self, *args, **options):
        QSchedule.objects.update_or_create(
            name="generate_upcoming_sessions",
            defaults={
                "func": "apps.scheduling.tasks.generate_upcoming_sessions",
                "schedule_type": QSchedule.DAILY,
            },
        )
        QSchedule.objects.update_or_create(
            name="sync_google_calendar",
            defaults={
                "func": "apps.scheduling.tasks.sync_google_calendar",
                "schedule_type": QSchedule.MINUTES,
                "minutes": 15,
            },
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Đã đăng ký: generate_upcoming_sessions (daily), "
                "sync_google_calendar (mỗi 15 phút)."
            )
        )
