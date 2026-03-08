"""
transactions — Django Admin configuration.
"""
from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "meter_number",
        "disco",
        "amount",
        "payment_status",
        "token_status",
        "payment_gateway",
        "created_at",
    ]
    list_filter = [
        "payment_status",
        "token_status",
        "disco",
        "payment_gateway",
        "created_at",
    ]
    search_fields = [
        "reference",
        "meter_number",
        "meter_owner_name",
        "gateway_reference",
    ]
    readonly_fields = [
        "id",
        "reference",
        "user",
        "meter",
        "meter_number",
        "disco",
        "meter_owner_name",
        "amount",
        "service_fee",
        "payment_gateway",
        "gateway_reference",
        "payment_confirmed_at",
        "token_value_encrypted",
        "disco_reference",
        "token_delivered_at",
        "ip_address",
        "user_agent",
        "created_at",
        "updated_at",
    ]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]
