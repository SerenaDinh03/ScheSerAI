import uuid
from datetime import date, datetime

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

DAY_OF_WEEK_CHOICES = [
    (0, "Thứ Hai"),
    (1, "Thứ Ba"),
    (2, "Thứ Tư"),
    (3, "Thứ Năm"),
    (4, "Thứ Sáu"),
    (5, "Thứ Bảy"),
    (6, "Chủ Nhật"),
]


class Schedule(models.Model):
    """Khuôn mẫu lịch học cố định hàng tuần của 1 học viên."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        "students.Student", on_delete=models.CASCADE, related_name="schedules"
    )
    day_of_week = models.IntegerField(
        choices=DAY_OF_WEEK_CHOICES, validators=[MinValueValidator(0), MaxValueValidator(6)]
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Lịch cố định"

    def __str__(self):
        return f"{self.student.name} - {self.get_day_of_week_display()} {self.start_time}"


class SessionQuerySet(models.QuerySet):
    def started(self):
        """Các buổi mà giờ bắt đầu đã tới/qua (so với thời điểm hiện tại)."""
        now = timezone.localtime()
        return self.filter(
            models.Q(session_date__lt=now.date())
            | models.Q(session_date=now.date(), start_time__lte=now.time())
        )

    def pending_attendance(self):
        """Buổi đã qua giờ học nhưng chưa điểm danh (US 3.3)."""
        return self.started().filter(attendance__isnull=True)


class Session(models.Model):
    """Một buổi học cụ thể trên 1 ngày - sinh ra từ Schedule, có thể tách rời khi dời lịch.

    status chỉ còn scheduled/rescheduled: buổi bị hủy hẳn sẽ bị xóa bản ghi
    (US 5.2), còn completed được suy ra gián tiếp qua sự tồn tại của Attendance.
    """

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Đã lên lịch"
        RESCHEDULED = "rescheduled", "Đã dời lịch"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        "students.Student", on_delete=models.CASCADE, related_name="sessions"
    )
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
    )
    session_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.SCHEDULED
    )
    google_event_id = models.CharField(max_length=255, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    objects = SessionQuerySet.as_manager()

    class Meta:
        verbose_name = "Buổi học"
        ordering = ["session_date", "start_time"]

    def has_started(self) -> bool:
        """Giờ học đã tới/qua chưa - buổi tương lai không được điểm danh trước (US 3.1)."""
        now = timezone.localtime()
        return (self.session_date, self.start_time) <= (now.date(), now.time())

    def mark_attendance(self, status: str) -> dict:
        """Tạo mới hoặc sửa lại điểm danh (US 3.1 + US 3.2).

        Buổi chưa tới giờ học không cho điểm danh lần đầu, nhưng điểm danh bù
        cho buổi đã qua thì không giới hạn thời gian - nên chỉ chặn khi tạo mới.
        Sửa điểm danh đã có luôn được phép, kèm cảnh báo nếu tháng đó đã xuất
        báo cáo học phí (báo cáo cũ sẽ lệch, cần xuất lại).
        """
        from apps.attendance.models import Attendance
        from apps.billing.models import MonthlyReport

        try:
            attendance = self.attendance
        except Attendance.DoesNotExist:
            attendance = None

        if attendance is None:
            if not self.has_started():
                raise ValueError("Buổi học chưa đến giờ bắt đầu, không thể điểm danh trước.")
            attendance = Attendance.objects.create(session=self, status=status)
        else:
            attendance.status = status
            attendance.save()

        warning = None
        if MonthlyReport.objects.filter(
            student=self.student,
            month=self.session_date.month,
            year=self.session_date.year,
        ).exists():
            warning = (
                "Buổi học này thuộc tháng đã xuất báo cáo học phí. "
                "Vui lòng xuất lại báo cáo để cập nhật (báo cáo cũ sẽ bị ghi đè)."
            )
        return {"attendance": attendance, "warning": warning}

    def has_attendance(self) -> bool:
        from apps.attendance.models import Attendance

        try:
            self.attendance
            return True
        except Attendance.DoesNotExist:
            return False

    def reschedule(self, session_date, start_time, end_time=None) -> dict:
        """Dời buổi học sang ngày/giờ khác (US 5.1).

        Chỉ ảnh hưởng buổi này (không đổi Schedule gốc - vốn đã tách biệt vì
        Session là bản ghi riêng). Nếu không truyền end_time mới, giữ nguyên
        thời lượng buổi học cũ.
        """
        from apps.notifications.models import Notification
        from apps.scheduling.calendar_sync import update_calendar_event

        if end_time is None:
            duration = datetime.combine(date.min, self.end_time) - datetime.combine(
                date.min, self.start_time
            )
            end_time = (datetime.combine(date.min, start_time) + duration).time()

        old_date, old_start = self.session_date, self.start_time
        self.session_date = session_date
        self.start_time = start_time
        self.end_time = end_time
        self.status = self.Status.RESCHEDULED
        self.save()

        if self.google_event_id:
            update_calendar_event(self.google_event_id, self)

        Notification.objects.create(
            teacher=self.student.teacher,
            message=(
                f"Buổi học của {self.student.name} đã được dời từ "
                f"{old_date.strftime('%d/%m/%Y')} {old_start.strftime('%H:%M')} "
                f"sang {session_date.strftime('%d/%m/%Y')} {start_time.strftime('%H:%M')}."
            ),
        )
        return {"session": self}

    def cancel(self) -> dict:
        """Hủy hẳn buổi học (US 5.2) - chặn nếu đã điểm danh để không mất dữ liệu học phí."""
        from apps.notifications.models import Notification
        from apps.scheduling.calendar_sync import delete_calendar_event

        if self.has_attendance():
            raise ValueError(
                "Không thể hủy buổi học đã điểm danh - dữ liệu học phí sẽ bị mất."
            )

        if self.google_event_id:
            delete_calendar_event(self.google_event_id)

        Notification.objects.create(
            teacher=self.student.teacher,
            message=(
                f"Buổi học của {self.student.name} ngày "
                f"{self.session_date.strftime('%d/%m/%Y')} {self.start_time.strftime('%H:%M')} "
                "đã bị hủy."
            ),
        )
        self.delete()
        return {"cancelled": True}

    def __str__(self):
        return f"{self.student.name} - {self.session_date} {self.start_time}"
