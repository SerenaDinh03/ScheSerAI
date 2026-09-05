from rest_framework import serializers

from apps.students.models import Student

from .models import MonthlyReport


class MonthlyReportSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.name", read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = MonthlyReport
        fields = [
            "id",
            "student",
            "student_name",
            "month",
            "year",
            "total_sessions",
            "total_amount",
            "generated_at",
            "download_url",
        ]
        read_only_fields = fields

    def get_download_url(self, obj):
        return f"/api/monthly-reports/{obj.id}/download/"


class GenerateReportSerializer(serializers.Serializer):
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())
    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField(min_value=2000, max_value=2100)
    format = serializers.ChoiceField(choices=["pdf", "png"], default="pdf")
