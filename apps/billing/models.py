import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class MonthlyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        "students.Student", on_delete=models.CASCADE, related_name="monthly_reports"
    )
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.IntegerField()
    total_sessions = models.IntegerField()
    total_amount = models.DecimalField(max_digits=14, decimal_places=0)
    file_url = models.CharField(max_length=500)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Báo cáo học phí"
        # Chỉ giữ 1 bản/tháng/học viên - xuất lại sẽ ghi đè bản cũ (US 4.2).
        constraints = [
            models.UniqueConstraint(
                fields=["student", "month", "year"], name="unique_report_per_student_month"
            )
        ]

    def __str__(self):
        return f"{self.student.name} - {self.month}/{self.year}"
