"""
payments — Serializers for payment initiation, verification, and webhooks.
"""
from decimal import Decimal

from rest_framework import serializers

from apps.transactions.models import PaymentGateway


class InitiatePaymentSerializer(serializers.Serializer):
    """Request body for starting a new token purchase."""

    meter_id = serializers.UUIDField(
        help_text="UUID of the customer's saved meter profile."
    )
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2,
        min_value=Decimal("500"),
        max_value=Decimal("100000"),
        help_text="Token amount in Naira (₦500 – ₦100,000)."
    )
    payment_gateway = serializers.ChoiceField(
        choices=[(PaymentGateway.PAYSTACK, "Paystack")],
        default=PaymentGateway.PAYSTACK,
        help_text="Payment gateway: PAYSTACK."
    )

    def validate_amount(self, value):
        """Extra guard: reject amounts outside ₦500–₦100,000."""
        if value < Decimal("500"):
            raise serializers.ValidationError(
                "Minimum purchase amount is ₦500."
            )
        if value > Decimal("100000"):
            raise serializers.ValidationError(
                "Maximum single purchase is ₦100,000. "
                "For larger amounts, please split into multiple purchases."
            )
        return value


class PaymentInitiatedResponseSerializer(serializers.Serializer):
    """Response after successful payment initialisation."""

    transaction_reference = serializers.CharField(help_text="ETIP unique reference.")
    authorization_url = serializers.URLField(
        help_text="Redirect the customer to this URL to complete payment."
    )
    access_code = serializers.CharField(
        help_text="Paystack access code.",
        required=False,
    )


class VerifyPaymentSerializer(serializers.Serializer):
    """Query params for manual payment verification."""

    reference = serializers.CharField(
        help_text="ETIP transaction reference (e.g. ETIP-ABC123DEF456)."
    )
