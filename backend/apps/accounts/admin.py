"""
accounts — Django Admin registration for User and OTPVerification models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import OTPVerification, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "full_name", "whatsapp_number", "is_verified", "is_active", "is_staff", "created_at"]
    list_filter = ["is_verified", "is_active", "is_staff", "is_superuser"]
    search_fields = ["email", "full_name", "whatsapp_number"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("full_name", "whatsapp_number")}),
        ("Permissions", {"fields": ("is_active", "is_verified", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Security", {"fields": ("failed_login_attempts", "locked_until")}),
        ("Push Notifications", {"fields": ("fcm_token",)}),
        ("Meta", {"fields": ("id", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "full_name", "whatsapp_number", "is_staff", "is_superuser"),
        }),
    )


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ["identifier", "purpose", "is_used", "created_at", "expires_at"]
    list_filter = ["purpose", "is_used"]
    search_fields = ["identifier"]
    readonly_fields = ["id", "otp_code", "created_at"]
    ordering = ["-created_at"]
