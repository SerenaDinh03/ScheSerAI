from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "price_per_session", "start_date")
    list_filter = ("status",)
    search_fields = ("name",)
