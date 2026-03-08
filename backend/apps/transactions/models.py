"""
transactions — Core Transaction model with payment + token state machine.
"""
import uuid

from django.conf import settings
from django.db import models

from apps.meters.models import DISCOProvider, MeterProfile


class PaymentGateway(models.TextChoices):
    PAYSTACK = "PAYSTACK", "Paystack"
    FLUTTERWAVE = "FLUTTERWAVE", "Flutterwave"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Payment Successful"
    FAILED = "FAILED", "Payment Failed"
    EXPIRED = "EXPIRED", "Payment Expired"


class TokenStatus(models.TextChoices):
    PENDING = "PENDING", "Pending Token"
    DELIVERED = "DELIVERED", "Token Delivered"
    FAILED = "FAILED", "Token Generation Failed"
    RESENT = "RESENT", "Token Resent"


class Transaction(models.Model):
    """
    Core financial record: one row per token purchase attempt.
    Immutable once created — status fields updated as events occur.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Unique idempotency reference (used with payment gateways)
    reference = models.CharField(max_length=100, unique=True, db_index=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    meter = models.ForeignKey(
        MeterProfile,
        on_delete=models.PROTECT,
        related_name="transactions",
        null=True,
        blank=True,
    )

    # Snapshot fields (in case meter profile is later deleted)
    meter_number = models.CharField(max_length=20)
    disco = models.CharField(max_length=20, choices=DISCOProvider.choices)
    meter_owner_name = models.CharField(max_length=255, blank=True)

    # Financial
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Payment
    payment_gateway = models.CharField(
        max_length=20, choices=PaymentGateway.choices, blank=True
    )
    payment_status = models.CharField(
        max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )
    gateway_reference = models.CharField(max_length=255, blank=True, db_index=True)
    payment_confirmed_at = models.DateTimeField(null=True, blank=True)

    # Token
    token_status = models.CharField(
        max_length=10, choices=TokenStatus.choices, default=TokenStatus.PENDING
    )
    # Token stored encrypted — never in plain text
    token_value_encrypted = models.TextField(blank=True)
    disco_reference = models.CharField(max_length=255, blank=True)
    token_delivered_at = models.DateTimeField(null=True, blank=True)

    # Resolution (admin)
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_transactions",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Token resend tracking
    resend_attempts = models.PositiveSmallIntegerField(default=0)
    last_resend_at = models.DateTimeField(null=True, blank=True)

    # Audit / device info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transactions"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["payment_status", "token_status"]),
            models.Index(fields=["disco", "-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"TXN:{self.reference} | {self.meter_number} | ₦{self.amount} | {self.payment_status}/{self.token_status}"

    @property
    def total_amount(self):
        return self.amount + self.service_fee

    @property
    def can_resend_token(self):
        return (
            self.payment_status == PaymentStatus.SUCCESS
            and self.token_status in [TokenStatus.FAILED, TokenStatus.PENDING]
            and self.resend_attempts < 3
        )
