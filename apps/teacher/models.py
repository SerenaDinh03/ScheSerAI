import uuid

from django.db import models

# Hệ thống chỉ phục vụ 1 giáo viên duy nhất -> luôn dùng cùng 1 PK cố định
# để không thể vô tình tạo bản ghi thứ hai.
SINGLETON_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class Teacher(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    # TODO(US 1.1): mã hóa giá trị này trước khi lưu (Fernet/KMS) - không lưu plaintext,
    # đây là quyền truy cập Google Calendar cá nhân của giáo viên.
    google_refresh_token = models.TextField(blank=True, default="")
    google_calendar_id = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "Giáo viên"

    def save(self, *args, **kwargs):
        self.pk = SINGLETON_ID
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=SINGLETON_ID)
        return obj

    def __str__(self):
        return self.name or self.email
