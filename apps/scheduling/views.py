from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.attendance.serializers import AttendanceSerializer, MarkAttendanceSerializer

from .models import Session
from .serializers import SessionSerializer


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SessionSerializer

    def get_queryset(self):
        qs = Session.objects.select_related("student")

        student_id = self.request.query_params.get("student")
        if student_id:
            qs = qs.filter(student_id=student_id)

        date_from = self.request.query_params.get("date_from")
        if date_from:
            qs = qs.filter(session_date__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            qs = qs.filter(session_date__lte=date_to)

        if self.request.query_params.get("pending") == "true":
            qs = qs.pending_attendance()

        return qs

    @action(detail=True, methods=["post"], url_path="mark-attendance")
    def mark_attendance(self, request, pk=None):
        session = self.get_object()
        input_serializer = MarkAttendanceSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            result = session.mark_attendance(input_serializer.validated_data["status"])
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        data = AttendanceSerializer(result["attendance"]).data
        if result["warning"]:
            data["warning"] = result["warning"]
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="bulk-mark-attendance")
    def bulk_mark_attendance(self, request):
        items = request.data if isinstance(request.data, list) else request.data.get("items", [])
        results = []
        for item in items:
            session_id = item.get("session")
            input_serializer = MarkAttendanceSerializer(data=item)
            if not input_serializer.is_valid():
                results.append(
                    {"session": session_id, "ok": False, "error": input_serializer.errors}
                )
                continue
            try:
                session = Session.objects.get(pk=session_id)
                result = session.mark_attendance(input_serializer.validated_data["status"])
                results.append(
                    {"session": session_id, "ok": True, "warning": result["warning"]}
                )
            except Session.DoesNotExist:
                results.append(
                    {"session": session_id, "ok": False, "error": "Không tìm thấy buổi học."}
                )
            except ValueError as exc:
                results.append({"session": session_id, "ok": False, "error": str(exc)})
        return Response(results, status=status.HTTP_200_OK)
