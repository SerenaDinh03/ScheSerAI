import uuid

from django.db import models


class Notification(models.Model):
    """Log đơn giản cho thông báo trong app (US 5.3) - không gửi email/SMS/Zalo."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(
        "teacher.Teacher", on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Thông báo"
        ordering = ["-created_at"]

    def __str__(self):
        return self.message[:50]
