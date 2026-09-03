from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.teacher.models import Teacher

from .models import Student
from .serializers import (
    StudentCreateSerializer,
    StudentDetailSerializer,
    StudentListSerializer,
    StudentUpdateSerializer,
)


class StudentViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action == "list":
            return StudentListSerializer
        if self.action == "create":
            return StudentCreateSerializer
        if self.action in ("update", "partial_update"):
            return StudentUpdateSerializer
        return StudentDetailSerializer

    def get_queryset(self):
        qs = Student.objects.all().order_by("name")
        if self.action == "list":
            status_param = self.request.query_params.get("status")
            qs = qs.filter(status=status_param) if status_param else qs.filter(
                status=Student.Status.ACTIVE
            )
            search = self.request.query_params.get("search")
            if search:
                qs = qs.filter(name__icontains=search)
        return qs

    def perform_create(self, serializer):
        serializer.save(teacher=Teacher.load())

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        start_date_changed = (
            "start_date" in serializer.validated_data
            and serializer.validated_data["start_date"] != instance.start_date
        )
        confirmed = bool(request.data.get("confirm"))

        if start_date_changed and instance.has_related_data() and not confirmed:
            return Response(
                {
                    "requires_confirmation": True,
                    "warning": (
                        "Học viên đã có lịch học/buổi học/điểm danh/báo cáo liên quan. "
                        "Đổi ngày bắt đầu học có thể ảnh hưởng dữ liệu này. "
                        'Gửi lại request với "confirm": true để xác nhận.'
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )

        serializer.save()
        return Response(StudentDetailSerializer(instance).data)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        student = self.get_object()
        with transaction.atomic():
            result = student.deactivate()
        return Response({"status": student.status, **result}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="billing-preview")
    def billing_preview(self, request, pk=None):
        student = self.get_object()
        today = timezone.localdate()
        try:
            month = int(request.query_params.get("month", today.month))
            year = int(request.query_params.get("year", today.year))
        except ValueError:
            return Response(
                {"detail": "month/year phải là số nguyên."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not 1 <= month <= 12:
            return Response(
                {"detail": "month phải trong khoảng 1-12."}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(student.billing_preview(month, year))
