from rest_framework import serializers

from apps.attendance.models import Attendance
from apps.attendance.serializers import AttendanceSerializer

from .models import Schedule, Session


class ScheduleSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(source="get_day_of_week_display", read_only=True)
    student_name = serializers.CharField(source="student.name", read_only=True)

    class Meta:
        model = Schedule
        fields = [
            "id",
            "student",
            "student_name",
            "day_of_week",
            "day_of_week_display",
            "start_time",
            "end_time",
            "is_active",
        ]
        read_only_fields = ["id", "is_active"]


class SessionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.name", read_only=True)
    attendance = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = [
            "id",
            "student",
            "student_name",
            "session_date",
            "start_time",
            "end_time",
            "status",
            "google_event_id",
            "attendance",
        ]

    def get_attendance(self, obj):
        try:
            return AttendanceSerializer(obj.attendance).data
        except Attendance.DoesNotExist:
            return None


class RescheduleSerializer(serializers.Serializer):
    session_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField(required=False, default=None)


class SessionCreateSerializer(serializers.ModelSerializer):
    """Thêm 1 buổi học lẻ thủ công (US 5.3) - vd buổi đã diễn ra trước khi giáo
    viên nhập lịch cố định vào hệ thống, nên không nằm trong cửa sổ sinh tự động
    của Schedule.generate_sessions(). Không gắn với Schedule nào (schedule=None)."""

    class Meta:
        model = Session
        fields = ["id", "student", "session_date", "start_time", "end_time"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        return Session.create_and_sync(**validated_data)
