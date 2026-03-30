from django.contrib import admin

from .models import MeterProfile
from .models_inquiry import MeterInquiry


@admin.register(MeterProfile)
class MeterProfileAdmin(admin.ModelAdmin):
    list_display = [
        "meter_number",
        "disco",
        "meter_type",
        "meter_owner_name",
        "user",
        "nickname",
        "is_default",
        "is_active",
        "created_at",
    ]
    list_filter = ["disco", "meter_type", "is_default", "is_active"]
    search_fields = ["meter_number", "meter_owner_name", "user__email"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]


@admin.register(MeterInquiry)
class MeterInquiryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "description")
