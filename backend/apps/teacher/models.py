import uuid

from django.db import models

from . import crypto

# Hệ thống chỉ phục vụ 1 giáo viên duy nhất -> luôn dùng cùng 1 PK cố định
# để không thể vô tình tạo bản ghi thứ hai.
SINGLETON_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class Teacher(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    # Lưu dạng đã mã hóa (Fernet, xem apps/teacher/crypto.py) - không bao giờ đọc/ghi
    # trực tiếp field này, luôn qua get_google_refresh_token()/set_google_refresh_token().
    google_refresh_token = models.TextField(blank=True, default="")
    google_calendar_id = models.CharField(max_length=255, blank=True, default="")
    google_account_email = models.EmailField(blank=True, default="")
    google_sync_token = models.TextField(blank=True, default="")
    google_last_sync_at = models.DateTimeField(null=True, blank=True)
    google_last_sync_error = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Giáo viên"

    def save(self, *args, **kwargs):
        self.pk = SINGLETON_ID
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=SINGLETON_ID)
        return obj

    def get_google_refresh_token(self) -> str:
        return crypto.decrypt(self.google_refresh_token)

    def set_google_refresh_token(self, raw_token: str) -> None:
        self.google_refresh_token = crypto.encrypt(raw_token)

    @property
    def is_google_connected(self) -> bool:
        return bool(self.google_refresh_token)

    def disconnect_google(self) -> None:
        self.google_refresh_token = ""
        self.google_calendar_id = ""
        self.google_account_email = ""
        self.google_sync_token = ""
        self.google_last_sync_error = ""
        self.save()

    def __str__(self):
        return self.name or self.email
