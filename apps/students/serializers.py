from django.utils import timezone
from rest_framework import serializers

from apps.attendance.models import Attendance
from apps.scheduling.models import Schedule

from .models import Student


class ScheduleNestedSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(source="get_day_of_week_display", read_only=True)

    class Meta:
        model = Schedule
        fields = ["id", "day_of_week", "day_of_week_display", "start_time", "end_time", "is_active"]


class AttendanceNestedSerializer(serializers.ModelSerializer):
    session_date = serializers.DateField(source="session.session_date", read_only=True)

    class Meta:
        model = Attendance
        fields = ["id", "session_date", "status", "is_billable", "marked_at"]


class StudentListSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = Student
        fields = ["id", "name", "age", "price_per_session", "status"]


class StudentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["id", "name", "dob", "start_date", "price_per_session", "note"]
        read_only_fields = ["id"]


class StudentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["name", "dob", "note", "start_date"]

    def validate(self, attrs):
        forbidden = {"price_per_session", "status", "teacher", "created_at", "id"}
        sent_forbidden = forbidden & set(self.initial_data.keys())
        if sent_forbidden:
            raise serializers.ValidationError(
                {field: "Trường này không được phép chỉnh sửa." for field in sent_forbidden}
            )
        return attrs


class StudentDetailSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(read_only=True)
    schedules = ScheduleNestedSerializer(many=True, read_only=True)
    recent_attendance = serializers.SerializerMethodField()
    sessions_this_month_count = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "id",
            "name",
            "dob",
            "age",
            "start_date",
            "price_per_session",
            "status",
            "note",
            "created_at",
            "schedules",
            "recent_attendance",
            "sessions_this_month_count",
        ]

    def get_recent_attendance(self, obj):
        qs = (
            Attendance.objects.filter(session__student=obj)
            .select_related("session")
            .order_by("-session__session_date")[:10]
        )
        return AttendanceNestedSerializer(qs, many=True).data

    def get_sessions_this_month_count(self, obj):
        today = timezone.localdate()
        return Attendance.objects.filter(
            session__student=obj,
            is_billable=True,
            session__session_date__year=today.year,
            session__session_date__month=today.month,
        ).count()
