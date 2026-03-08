"""
admin_panel — Django Admin registration for AdminUser and AuditLog.
"""
from django.contrib import admin

from .models import AdminUser, AuditLog


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ["email", "full_name", "role", "is_active", "mfa_enabled", "created_at"]
    list_filter = ["role", "is_active", "mfa_enabled"]
    search_fields = ["email", "full_name"]
    readonly_fields = ["id", "created_at", "last_login"]
    ordering = ["-created_at"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "actor_label", "action", "target_type", "target_id", "ip_address"]
    list_filter = ["action", "target_type"]
    search_fields = ["actor_label", "action", "target_type", "target_id"]
    readonly_fields = [
        "id", "admin_actor", "user_actor", "actor_label",
        "action", "target_type", "target_id", "metadata",
        "ip_address", "timestamp",
    ]
    date_hierarchy = "timestamp"
    ordering = ["-timestamp"]

    def has_change_permission(self, request, obj=None):
        return False  # Audit logs are immutable

    def has_delete_permission(self, request, obj=None):
        return False  # Audit logs are immutable
