import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

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

    class Meta:
        verbose_name = "Buổi học"
        ordering = ["session_date", "start_time"]

    def __str__(self):
        return f"{self.student.name} - {self.session_date} {self.start_time}"
