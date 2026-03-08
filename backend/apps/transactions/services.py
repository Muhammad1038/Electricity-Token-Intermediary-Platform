"""
transactions — Business logic: create, encrypt/decrypt token, resend.
"""
import logging
import uuid

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.utils import timezone

from apps.meters.models import MeterProfile
from apps.meters.services import validate_meter_with_disco

from .models import PaymentStatus, TokenStatus, Transaction

logger = logging.getLogger(__name__)

# ── Encryption helpers ────────────────────────────────────────────────────────


def _get_fernet():
    key = getattr(settings, "TOKEN_ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY is not set in settings.")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token_value(plain_text: str) -> str:
    """Encrypt a token value for storage."""
    return _get_fernet().encrypt(plain_text.encode()).decode()


def decrypt_token_value(cipher_text: str) -> str:
    """Decrypt a stored token value."""
    try:
        return _get_fernet().decrypt(cipher_text.encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt token value — key mismatch or corrupted data.")
        return "[DECRYPTION_ERROR]"


# ── Transaction reference ─────────────────────────────────────────────────────


def generate_reference() -> str:
    """Generate a unique ETIP transaction reference."""
    short_uuid = uuid.uuid4().hex[:12].upper()
    return f"ETIP-{short_uuid}"


# ── Transaction creation (called by payments service) ─────────────────────────


def create_transaction(
    user,
    meter: MeterProfile,
    amount,
    payment_gateway: str,
    service_fee=0,
    ip_address=None,
    user_agent="",
) -> Transaction:
    """
    Create a new PENDING transaction.
    Called by the payments service when a customer initiates a purchase.
    """
    reference = generate_reference()

    txn = Transaction.objects.create(
        reference=reference,
        user=user,
        meter=meter,
        meter_number=meter.meter_number,
        disco=meter.disco,
        meter_owner_name=meter.meter_owner_name,
        amount=amount,
        service_fee=service_fee,
        payment_gateway=payment_gateway,
        payment_status=PaymentStatus.PENDING,
        token_status=TokenStatus.PENDING,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    logger.info(
        "Transaction created: %s for meter %s, amount ₦%s",
        reference, meter.meter_number, amount,
    )
    return txn


# ── Payment confirmation (called by webhooks) ────────────────────────────────


def confirm_payment(txn: Transaction, gateway_reference: str = "") -> Transaction:
    """
    Mark transaction payment as successful.
    Called after webhook verification confirms payment.
    """
    txn.payment_status = PaymentStatus.SUCCESS
    txn.gateway_reference = gateway_reference
    txn.payment_confirmed_at = timezone.now()
    txn.save(update_fields=[
        "payment_status", "gateway_reference", "payment_confirmed_at", "updated_at"
    ])
    logger.info("Payment confirmed for %s (gateway ref: %s)", txn.reference, gateway_reference)
    return txn


def fail_payment(txn: Transaction, reason: str = "") -> Transaction:
    """Mark transaction payment as failed."""
    txn.payment_status = PaymentStatus.FAILED
    txn.resolution_notes = reason
    txn.save(update_fields=["payment_status", "resolution_notes", "updated_at"])
    logger.warning("Payment failed for %s: %s", txn.reference, reason)
    return txn


# ── Token delivery (called after DISCO responds) ─────────────────────────────


def store_token(txn: Transaction, token_value: str, disco_reference: str = "") -> Transaction:
    """
    Encrypt and store the DISCO-generated token on the transaction.
    """
    txn.token_value_encrypted = encrypt_token_value(token_value)
    txn.disco_reference = disco_reference
    txn.token_status = TokenStatus.DELIVERED
    txn.token_delivered_at = timezone.now()
    txn.save(update_fields=[
        "token_value_encrypted", "disco_reference",
        "token_status", "token_delivered_at", "updated_at",
    ])
    logger.info("Token stored for %s (DISCO ref: %s)", txn.reference, disco_reference)
    return txn


def fail_token(txn: Transaction, reason: str = "") -> Transaction:
    """Mark token generation as failed."""
    txn.token_status = TokenStatus.FAILED
    txn.resolution_notes = reason
    txn.save(update_fields=["token_status", "resolution_notes", "updated_at"])
    logger.warning("Token generation failed for %s: %s", txn.reference, reason)
    return txn


# ── Token resend ──────────────────────────────────────────────────────────────


def resend_token(txn: Transaction) -> dict:
    """
    Attempt to resend a token for a transaction.
    Returns a status dict with success/error information.

    Rules:
    - Payment must be SUCCESS
    - Token status must be FAILED or PENDING
    - Maximum 3 resend attempts allowed
    """
    if not txn.can_resend_token:
        if txn.payment_status != PaymentStatus.SUCCESS:
            return {"success": False, "error": "Payment has not been confirmed yet."}
        if txn.token_status == TokenStatus.DELIVERED:
            return {"success": False, "error": "Token has already been delivered."}
        if txn.resend_attempts >= 3:
            return {"success": False, "error": "Maximum resend attempts (3) reached. Contact support."}
        return {"success": False, "error": "Token resend is not available for this transaction."}

    # Increment attempt counter
    txn.resend_attempts += 1
    txn.last_resend_at = timezone.now()
    txn.token_status = TokenStatus.PENDING
    txn.save(update_fields=["resend_attempts", "last_resend_at", "token_status", "updated_at"])

    # Dispatch Celery task to re-call DISCO API for token
    from apps.transactions.tasks import request_disco_token_task
    request_disco_token_task.delay(str(txn.id))

    logger.info(
        "Token resend triggered for %s (attempt %d/3)",
        txn.reference, txn.resend_attempts,
    )
    return {
        "success": True,
        "message": f"Token resend initiated (attempt {txn.resend_attempts}/3).",
        "resend_attempts": txn.resend_attempts,
    }


# ── Read helpers ──────────────────────────────────────────────────────────────


def get_user_transactions(user):
    """Return all transactions for a given customer, newest first."""
    return Transaction.objects.filter(user=user).order_by("-created_at")


def get_user_tokens(user):
    """
    Return transactions for the user's Token Records page, newest first.
    Includes:
      - Delivered tokens (for display + copy)
      - Pending tokens (payment succeeded, waiting for DISCO)
      - Failed tokens (payment succeeded but DISCO delivery failed — can resend)
    """
    return (
        Transaction.objects
        .filter(
            user=user,
            payment_status=PaymentStatus.SUCCESS,
        )
        .order_by("-created_at")
    )


def get_transaction_for_user(user, txn_id) -> Transaction | None:
    """Return a single transaction if it belongs to the given user."""
    try:
        return Transaction.objects.get(id=txn_id, user=user)
    except Transaction.DoesNotExist:
        return None
