import uuid

from django.db import models
from django.utils import timezone


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Có mặt"
        ABSENT = "absent", "Nghỉ"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(
        "scheduling.Session", on_delete=models.CASCADE, related_name="attendance"
    )
    status = models.CharField(max_length=10, choices=Status.choices)
    is_billable = models.BooleanField(editable=False)
    marked_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Điểm danh"
        verbose_name_plural = "Điểm danh"

    def save(self, *args, **kwargs):
        # is_billable luôn suy ra từ status, không cho nhập tay để tránh lệch dữ liệu
        # dùng trực tiếp cho tính báo cáo học phí (US 3.4).
        self.is_billable = self.status == self.Status.PRESENT
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.session} - {self.get_status_display()}"
