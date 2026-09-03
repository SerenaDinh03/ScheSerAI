from rest_framework import serializers

from apps.attendance.models import Attendance
from apps.attendance.serializers import AttendanceSerializer

from .models import Session


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
