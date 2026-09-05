from rest_framework import serializers

from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    session_date = serializers.DateField(source="session.session_date", read_only=True)

    class Meta:
        model = Attendance
        fields = ["id", "session", "session_date", "status", "is_billable", "marked_at"]
        read_only_fields = ["is_billable", "marked_at"]


class MarkAttendanceSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Attendance.Status.choices)
