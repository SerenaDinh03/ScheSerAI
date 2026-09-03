from django.contrib import admin

from .models import Schedule, Session


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("student", "day_of_week", "start_time", "end_time", "is_active")
    list_filter = ("day_of_week", "is_active")


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("student", "session_date", "start_time", "status", "google_event_id")
    list_filter = ("status",)
    date_hierarchy = "session_date"
