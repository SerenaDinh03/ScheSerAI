import uuid

from django.db import models


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
    price_per_session = models.DecimalField(max_digits=12, decimal_places=0)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Học viên"

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
