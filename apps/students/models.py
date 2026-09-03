import uuid
from datetime import date

from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone


class Student(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Đang học"
        INACTIVE = "inactive", "Đã nghỉ"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(
        "teacher.Teacher", on_delete=models.CASCADE, related_name="students"
    )
    name = models.CharField(max_length=255)
    dob = models.DateField(null=True, blank=True)
    start_date = models.DateField()
    price_per_session = models.DecimalField(
        max_digits=12, decimal_places=0, validators=[MinValueValidator(1)]
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Học viên"

    @property
    def age(self):
        if not self.dob:
            return None
        today = date.today()
        had_birthday = (today.month, today.day) >= (self.dob.month, self.dob.day)
        return today.year - self.dob.year - (0 if had_birthday else 1)

    def has_related_data(self) -> bool:
        from apps.attendance.models import Attendance

        return (
            self.schedules.exists()
            or self.sessions.exists()
            or Attendance.objects.filter(session__student=self).exists()
            or self.monthly_reports.exists()
        )

    def upcoming_sessions(self):
        return self.sessions.filter(
            session_date__gte=timezone.localdate(), attendance__isnull=True
        )

    def deactivate(self) -> dict:
        from apps.scheduling.calendar_sync import delete_calendar_event

        with transaction.atomic():
            self.status = self.Status.INACTIVE
            self.save()
            sessions = list(self.upcoming_sessions())
            for session in sessions:
                if session.google_event_id:
                    delete_calendar_event(session.google_event_id)
                session.delete()
        return {"deleted_sessions_count": len(sessions)}

    def save(self, *args, **kwargs):
        # price_per_session cố định vĩnh viễn theo học viên (đã chốt trong backlog) -
        # chặn ở tầng model để không path code nào vô tình sửa được sau khi tạo.
        if self.pk:
            original_price = (
                Student.objects.filter(pk=self.pk)
                .values_list("price_per_session", flat=True)
                .first()
            )
            if original_price is not None and original_price != self.price_per_session:
                raise ValueError("price_per_session không thể thay đổi sau khi tạo học viên")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
