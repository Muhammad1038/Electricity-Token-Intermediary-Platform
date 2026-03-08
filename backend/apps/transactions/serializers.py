"""
transactions — Serializers for customer-facing transaction endpoints.
"""
from decimal import Decimal

from rest_framework import serializers

from apps.meters.models import DISCOProvider

from .models import PaymentGateway, PaymentStatus, TokenStatus, Transaction


class TransactionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the transaction history list."""

    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    disco_display = serializers.CharField(source="get_disco_display", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "reference",
            "meter_number",
            "disco",
            "disco_display",
            "meter_owner_name",
            "amount",
            "service_fee",
            "total_amount",
            "payment_gateway",
            "payment_status",
            "token_status",
            "created_at",
        ]
        read_only_fields = fields


class TransactionDetailSerializer(serializers.ModelSerializer):
    """Full detail view of a single transaction."""

    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    can_resend_token = serializers.BooleanField(read_only=True)
    disco_display = serializers.CharField(source="get_disco_display", read_only=True)
    electricity_token = serializers.SerializerMethodField(
        help_text="Decrypted electricity token value. Only returned when payment is successful and token is delivered."
    )

    class Meta:
        model = Transaction
        fields = [
            "id",
            "reference",
            "meter_number",
            "disco",
            "disco_display",
            "meter_owner_name",
            "amount",
            "service_fee",
            "total_amount",
            "payment_gateway",
            "payment_status",
            "gateway_reference",
            "payment_confirmed_at",
            "token_status",
            "electricity_token",
            "token_delivered_at",
            "disco_reference",
            "resend_attempts",
            "can_resend_token",
            "is_resolved",
            "resolution_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_electricity_token(self, obj):
        """Return decrypted token only when payment succeeded and token was delivered."""
        if (
            obj.payment_status == PaymentStatus.SUCCESS
            and obj.token_status in (TokenStatus.DELIVERED, TokenStatus.RESENT)
            and obj.token_value_encrypted
        ):
            from apps.transactions.services import decrypt_token_value
            return decrypt_token_value(obj.token_value_encrypted)
        return None


class TokenRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for the user's token records page.
    Includes delivered tokens with decrypted values,
    plus PENDING/FAILED tokens so users can track + resend.
    """
    electricity_token = serializers.SerializerMethodField()
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    disco_display = serializers.CharField(source="get_disco_display", read_only=True)
    can_resend_token = serializers.BooleanField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "reference",
            "meter_number",
            "disco",
            "disco_display",
            "meter_owner_name",
            "amount",
            "service_fee",
            "total_amount",
            "electricity_token",
            "token_status",
            "token_delivered_at",
            "can_resend_token",
            "resend_attempts",
            "created_at",
        ]
        read_only_fields = fields

    def get_electricity_token(self, obj):
        """Return decrypted token when delivered, None otherwise."""
        if obj.token_value_encrypted and obj.token_status in (
            TokenStatus.DELIVERED, TokenStatus.RESENT
        ):
            from apps.transactions.services import decrypt_token_value
            return decrypt_token_value(obj.token_value_encrypted)
        return None


class TokenResendSerializer(serializers.Serializer):
    """Request body for the token resend endpoint."""

    transaction_id = serializers.UUIDField(
        help_text="UUID of the transaction to resend the token for."
    )


class TransactionCreateSerializer(serializers.Serializer):
    """
    Used internally (by the payments service) to create a new transaction.
    Not exposed as a public API endpoint — customers don't create
    transactions directly; the payment flow does.
    """

    meter_id = serializers.UUIDField(help_text="UUID of the saved meter profile.")
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("1"),
        help_text="Token amount in Naira."
    )
    payment_gateway = serializers.ChoiceField(
        choices=PaymentGateway.choices,
        help_text="Payment gateway to use (PAYSTACK or FLUTTERWAVE)."
    )
