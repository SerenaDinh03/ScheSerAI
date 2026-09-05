from rest_framework import serializers

from apps.attendance.models import Attendance
from apps.attendance.serializers import AttendanceSerializer

from .models import Schedule, Session


class ScheduleSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(source="get_day_of_week_display", read_only=True)

    class Meta:
        model = Schedule
        fields = [
            "id",
            "student",
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
