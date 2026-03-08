"""
admin_panel — Serializers for the admin/operator dashboard API.
"""
from rest_framework import serializers

from apps.accounts.models import User
from apps.transactions.models import Transaction

from .models import AdminRole, AdminUser, AuditLog


# ── Admin auth ────────────────────────────────────────────────────────────────


class AdminLoginSerializer(serializers.Serializer):
    """Admin login with email + password."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class AdminProfileSerializer(serializers.ModelSerializer):
    """Read-only admin profile."""
    class Meta:
        model = AdminUser
        fields = [
            "id", "email", "full_name", "role",
            "is_active", "mfa_enabled", "last_login", "created_at",
        ]
        read_only_fields = fields


class AdminCreateSerializer(serializers.ModelSerializer):
    """Create a new operator account (SUPER_ADMIN only)."""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = AdminUser
        fields = ["email", "full_name", "role", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        admin = AdminUser(**validated_data)
        admin.set_password(password)
        admin.save()
        return admin


# ── Dashboard ─────────────────────────────────────────────────────────────────


class DashboardStatsSerializer(serializers.Serializer):
    """Summary statistics for the admin dashboard."""
    total_users = serializers.IntegerField()
    total_transactions = serializers.IntegerField()
    pending_payments = serializers.IntegerField()
    successful_payments = serializers.IntegerField()
    failed_payments = serializers.IntegerField()
    pending_tokens = serializers.IntegerField()
    delivered_tokens = serializers.IntegerField()
    failed_tokens = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)


# ── User management ──────────────────────────────────────────────────────────


class CustomerListSerializer(serializers.ModelSerializer):
    """List of consumer accounts for admin review."""
    transaction_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "whatsapp_number", "full_name",
            "is_active", "is_verified", "created_at",
            "transaction_count",
        ]
        read_only_fields = fields


class CustomerEditSerializer(serializers.ModelSerializer):
    """Admin editable fields for a customer account."""
    class Meta:
        model = User
        fields = ["full_name", "email", "is_active"]

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value


class CustomerSuspendSerializer(serializers.Serializer):
    """Suspend or reactivate a customer account."""
    suspend = serializers.BooleanField(
        help_text="True to suspend, False to reactivate.",
    )
    reason = serializers.CharField(
        max_length=500, required=False, default="",
        help_text="Reason for suspension/reactivation.",
    )


# ── Transaction management ───────────────────────────────────────────────────


class AdminTransactionListSerializer(serializers.ModelSerializer):
    """Transaction list for admin — includes user info."""
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_whatsapp = serializers.CharField(source="user.whatsapp_number", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    token_code = serializers.SerializerMethodField(
        help_text="Decrypted token for admin list view (only when delivered)."
    )
    disco_display = serializers.CharField(source="get_disco_display", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id", "reference", "user_email", "user_whatsapp", "user_name",
            "meter_number", "disco", "disco_display", "meter_owner_name",
            "amount", "service_fee", "total_amount",
            "payment_gateway", "payment_status", "token_status",
            "token_code",
            "is_resolved", "created_at",
        ]
        read_only_fields = fields

    def get_token_code(self, obj):
        """Return decrypted token for delivered transactions."""
        if (
            obj.token_status in ('DELIVERED', 'RESENT')
            and obj.token_value_encrypted
        ):
            from apps.transactions.services import decrypt_token_value
            return decrypt_token_value(obj.token_value_encrypted)
        return None


class AdminTransactionDetailSerializer(serializers.ModelSerializer):
    """Full transaction detail for admins."""
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_whatsapp = serializers.CharField(source="user.whatsapp_number", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    can_resend_token = serializers.BooleanField(read_only=True)
    resolved_by_email = serializers.SerializerMethodField()
    electricity_token = serializers.SerializerMethodField(
        help_text="Decrypted electricity token value (admin view)."
    )
    disco_display = serializers.CharField(source="get_disco_display", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id", "reference",
            "user_email", "user_whatsapp", "user_name",
            "meter_number", "disco", "disco_display", "meter_owner_name",
            "amount", "service_fee", "total_amount",
            "payment_gateway", "payment_status",
            "gateway_reference", "payment_confirmed_at",
            "token_status", "electricity_token", "token_delivered_at",
            "disco_reference", "resend_attempts", "can_resend_token",
            "is_resolved", "resolution_notes", "resolved_by_email", "resolved_at",
            "ip_address", "user_agent",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_resolved_by_email(self, obj):
        if obj.resolved_by:
            return obj.resolved_by.email
        return None

    def get_electricity_token(self, obj):
        """Admin can see decrypted token whenever it exists."""
        if obj.token_value_encrypted:
            from apps.transactions.services import decrypt_token_value
            return decrypt_token_value(obj.token_value_encrypted)
        return None


class ResolveTransactionSerializer(serializers.Serializer):
    """Mark a transaction as resolved."""
    resolution_notes = serializers.CharField(
        max_length=1000,
        help_text="Notes describing how the issue was resolved.",
    )


# ── Audit log ─────────────────────────────────────────────────────────────────


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id", "actor_label", "action",
            "target_type", "target_id", "metadata",
            "ip_address", "timestamp",
        ]
        read_only_fields = fields


# ── Meters admin ────────────────────────────────────────────────────────────────────────────────


class AdminMeterListSerializer(serializers.Serializer):
    """Meter profile list for admin panel."""
    id = serializers.UUIDField()
    meter_number = serializers.CharField()
    disco = serializers.CharField()
    disco_display = serializers.CharField()
    nickname = serializers.CharField()
    meter_owner_name = serializers.CharField()
    meter_type = serializers.CharField()
    is_active = serializers.BooleanField()
    is_default = serializers.BooleanField()
    user_email = serializers.CharField()
    user_name = serializers.CharField()
    created_at = serializers.DateTimeField()
