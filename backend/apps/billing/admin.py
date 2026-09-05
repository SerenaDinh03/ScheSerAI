from django.contrib import admin

from .models import MonthlyReport


@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = ("student", "month", "year", "total_sessions", "total_amount", "generated_at")
    list_filter = ("year", "month")
