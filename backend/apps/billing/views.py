from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.students.models import Student

from .models import MonthlyReport
from .report_builder import build_report_data, generate_report
from .serializers import GenerateReportSerializer, MonthlyReportSerializer


class MonthlyReportViewSet(viewsets.ReadOnlyModelViewSet):
    """Lịch sử báo cáo đã xuất (US 4.3) + preview/generate (US 4.1, US 4.2).

    Không có update/destroy - báo cáo cũ chỉ có thể xuất lại (ghi đè qua
    action generate), không sửa trực tiếp.
    """

    serializer_class = MonthlyReportSerializer

    def get_queryset(self):
        qs = MonthlyReport.objects.select_related("student").order_by("-year", "-month")
        student_id = self.request.query_params.get("student")
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs

    @action(detail=False, methods=["get"])
    def preview(self, request):
        student_id = request.query_params.get("student")
        student = Student.objects.filter(pk=student_id).first() if student_id else None
        if not student:
            return Response(
                {"detail": "Thiếu student hoặc không tìm thấy học viên."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            month = int(request.query_params.get("month"))
            year = int(request.query_params.get("year"))
        except (TypeError, ValueError):
            return Response(
                {"detail": "month/year không hợp lệ."}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(build_report_data(student, month, year))

    @action(detail=False, methods=["post"])
    def generate(self, request):
        input_serializer = GenerateReportSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data
        report = generate_report(data["student"], data["month"], data["year"], data["format"])
        return Response(MonthlyReportSerializer(report).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        report = self.get_object()
        full_path = Path(settings.MEDIA_ROOT) / report.file_url
        if not full_path.exists():
            raise Http404("File báo cáo không tồn tại.")
        content_type = "application/pdf" if full_path.suffix == ".pdf" else "image/png"
        filename = f"baocao_{report.student.name}_{report.month:02d}_{report.year}{full_path.suffix}"
        return FileResponse(
            open(full_path, "rb"), content_type=content_type, as_attachment=True, filename=filename
        )
