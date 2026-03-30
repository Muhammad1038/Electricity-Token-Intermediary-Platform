"""
payments — Gateway integration: Paystack only.

Responsibilities:
  • Initialise payments (get hosted checkout URL)
  • Verify payments (confirm transaction status)
  • Validate Paystack webhook signatures
"""
import hashlib
import hmac
import logging
from decimal import Decimal

import httpx
from django.conf import settings

from apps.meters.models import MeterProfile
from apps.transactions.models import PaymentGateway, PaymentStatus
from apps.transactions.services import (
    confirm_payment,
    create_transaction,
    fail_payment,
)

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 15       # seconds — for initiate calls
VERIFY_TIMEOUT = 30    # seconds — verify needs more time; payment already made
SERVICE_FEE_RATE = Decimal("0.00")  # 0% for MVP — change later

# Minimum purchase amounts per DISCO (VTPass sandbox enforces these)
DISCO_MINIMUMS: dict[str, Decimal] = {
    "IBEDC":  Decimal("1500"),  # Ibadan
    "KAEDCO": Decimal("1500"),  # Kaduna
    "EEDC":   Decimal("1000"),  # Enugu
    "EKEDC":  Decimal("1000"),  # Eko
    "IKEDC":  Decimal("1000"),  # Ikeja
    "AEDC":   Decimal("1000"),  # Abuja
    "KEDCO":  Decimal("1000"),  # Kano
    "JED":    Decimal("1000"),  # Jos
    "YEDC":   Decimal("1000"),  # Yola
    "PHED":   Decimal("1000"),  # Port Harcourt
    "BEDC":   Decimal("1000"),  # Benin
    "ABA":    Decimal("1000"),  # Aba
}
DEFAULT_MIN = Decimal("1000")  # fallback for unknown DISCOs


# ━━ Helpers ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _service_fee(amount: Decimal) -> Decimal:
    """Calculate service fee for a given purchase amount."""
    return (amount * SERVICE_FEE_RATE).quantize(Decimal("0.01"))


def _kobo(amount: Decimal) -> int:
    """Convert Naira (Decimal) → kobo (int) for Paystack."""
    return int(amount * 100)


# ━━ Paystack ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _paystack_headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def _normalize_phone(raw: str | None) -> str | None:
    """
    Normalize a Nigerian phone number to E.164 (+234XXXXXXXXXX).
    Accepts: 08XXXXXXXXX, 234XXXXXXXXXX, +234XXXXXXXXXX.
    Returns None if input is empty/None.
    """
    if not raw:
        return None
    digits = raw.strip().lstrip("+")
    if digits.startswith("234") and len(digits) == 13:
        return f"+{digits}"
    if digits.startswith("0") and len(digits) == 11:
        return f"+234{digits[1:]}"
    # Already looks like E.164 digits (e.g. 2348140628953)
    if digits.startswith("234"):
        return f"+{digits}"
    return None  # unrecognised — don't send


def _paystack_initialize(reference: str, amount_naira: Decimal, email: str, phone: str | None = None) -> dict:
    """
    POST /transaction/initialize on Paystack.
    Returns {authorization_url, access_code, reference}.
    """
    url = f"{settings.PAYSTACK_BASE_URL}/transaction/initialize"
    # Deep-link callback — Paystack redirects the browser here after payment.
    # The custom scheme (etip://) makes the OS open the app directly,
    # skipping the blank localhost page entirely.
    # Use an HTTPS callback URL so WebView can intercept it without
    # triggering the OS Intent resolver (which opens the system browser).
    # This URL does NOT need to exist — the in-app WebView catches it.
    callback_url = getattr(
        settings,
        "PAYSTACK_CALLBACK_URL",
        "https://etip-app.callback/payment/verify",
    )
    payload = {
        "reference": reference,
        "amount": _kobo(amount_naira),
        "email": email,
        "currency": "NGN",
        "channels": ["card", "bank", "ussd", "bank_transfer", "qr", "mobile_money", "eft"],
        "callback_url": callback_url,
    }
    # phone is required by Paystack for USSD — without it USSD fails
    if phone:
        payload["phone"] = phone
        payload["metadata"] = {"phone": phone}

    # Sandbox stub when secret key is placeholder
    if not settings.PAYSTACK_SECRET_KEY or settings.PAYSTACK_SECRET_KEY.startswith("sk_test_your"):
        logger.warning("Paystack sandbox stub — no real API call.")
        return {
            "authorization_url": f"https://checkout.paystack.com/sandbox/{reference}",
            "access_code": f"SANDBOX_{reference}",
            "reference": reference,
        }

    with httpx.Client(timeout=HTTP_TIMEOUT) as client:
        resp = client.post(url, json=payload, headers=_paystack_headers())
        resp.raise_for_status()
        data = resp.json()

    if not data.get("status"):
        raise ValueError(f"Paystack init failed: {data.get('message', 'unknown')}")

    return data["data"]


def _paystack_verify(reference: str) -> dict:
    """
    GET /transaction/verify/:reference on Paystack.
    Returns the gateway's transaction data dict.
    """
    # Sandbox stub
    if not settings.PAYSTACK_SECRET_KEY or settings.PAYSTACK_SECRET_KEY.startswith("sk_test_your"):
        logger.warning("Paystack sandbox stub — returning mock success.")
        return {
            "status": "success",
            "reference": reference,
            "gateway_response": "Approved",
            "amount": 0,
        }

    url = f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}"
    with httpx.Client(timeout=VERIFY_TIMEOUT) as client:
        resp = client.get(url, headers=_paystack_headers())
        resp.raise_for_status()
        data = resp.json()

    if not data.get("status"):
        raise ValueError(f"Paystack verify failed: {data.get('message', 'unknown')}")

    return data["data"]


def verify_paystack_webhook(payload_body: bytes, signature: str) -> bool:
    """Validate Paystack webhook X-Paystack-Signature header (HMAC-SHA512)."""
    secret = settings.PAYSTACK_SECRET_KEY.encode()
    expected = hmac.new(secret, payload_body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature)



# ━━ Public API ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def initiate_payment(user, meter_id, amount: Decimal, payment_gateway: str, ip_address=None, user_agent="") -> dict:
    """
    Orchestrator: create a transaction + initialise the chosen payment gateway.

    Returns {
        "transaction_reference": ...,
        "authorization_url": ...,
        "access_code": ...,
    }
    """
    # Validate meter belongs to user
    try:
        meter = MeterProfile.objects.get(id=meter_id, user=user, is_active=True)
    except MeterProfile.DoesNotExist:
        raise ValueError("Meter profile not found or does not belong to you.")

    # Paystack requires a valid email — check BEFORE creating transaction
    if not user.email:
        raise ValueError(
            "An email address is required to process payments. "
            "Please update your profile with a valid email."
        )
    email = user.email

    # Enforce per-DISCO minimum purchase amount before charging the user
    # (skipped in test mode — any amount is fine for sandbox testing)
    if not getattr(settings, "VTPASS_TEST_MODE", False):
        disco_min = DISCO_MINIMUMS.get(meter.disco, DEFAULT_MIN)
        if amount < disco_min:
            raise ValueError(
                f"Minimum purchase amount for {meter.disco} is "
                f"\u20a6{disco_min:,.0f}. You entered \u20a6{amount:,.0f}."
            )

    fee = _service_fee(amount)
    total = amount + fee
    phone = _normalize_phone(getattr(user, "whatsapp_number", None))

    # Create pending transaction
    txn = create_transaction(
        user=user,
        meter=meter,
        amount=amount,
        payment_gateway=payment_gateway,
        service_fee=fee,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    try:
        if payment_gateway == PaymentGateway.PAYSTACK:
            gw_data = _paystack_initialize(txn.reference, total, email, phone=phone)
            return {
                "transaction_reference": txn.reference,
                "authorization_url": gw_data["authorization_url"],
                "access_code": gw_data.get("access_code", ""),
                "email": email,
                "amount_kobo": _kobo(total),
            }
        else:
            raise ValueError(f"Unsupported payment gateway: {payment_gateway}")
    except Exception as e:
        fail_payment(txn, reason=str(e))
        raise


def verify_payment(reference: str) -> dict:
    """
    Verify payment status with the appropriate gateway.
    Updates transaction status accordingly.

    Returns {"status": "success"|"failed", "transaction_reference": ..., ...}
    """
    from apps.transactions.models import Transaction

    try:
        txn = Transaction.objects.get(reference=reference)
    except Transaction.DoesNotExist:
        raise ValueError(f"Transaction not found: {reference}")

    # Already confirmed — skip re-verification
    if txn.payment_status == PaymentStatus.SUCCESS:
        return {
            "status": "success",
            "transaction_reference": txn.reference,
            "message": "Payment already confirmed.",
        }

    try:
        if txn.payment_gateway == PaymentGateway.PAYSTACK:
            gw_data = _paystack_verify(reference)
            if gw_data.get("status") == "success":
                confirm_payment(txn, gateway_reference=gw_data.get("reference", ""))
                # Dispatch DISCO token request asynchronously
                from apps.transactions.tasks import request_disco_token_task
                request_disco_token_task.delay(str(txn.id))
                return {
                    "status": "success",
                    "transaction_reference": txn.reference,
                    "message": "Payment verified. Token delivery in progress.",
                }
            else:
                fail_payment(txn, reason=gw_data.get("gateway_response", "Failed"))
                return {
                    "status": "failed",
                    "transaction_reference": txn.reference,
                    "message": f"Payment failed: {gw_data.get('gateway_response', 'Unknown')}",
                }

        else:
            # Gateway no longer supported for new verifications
            raise ValueError(f"Payment gateway '{txn.payment_gateway}' is not supported for verification.")

    except httpx.TimeoutException as e:
        logger.error("Gateway verification timed out for %s: %s", reference, e)
        return {
            "status": "error",
            "transaction_reference": txn.reference,
            "message": "Payment gateway timed out. Please try again.",
        }
    except httpx.HTTPStatusError as e:
        logger.error("Gateway verification HTTP error for %s: %s", reference, e)
        return {
            "status": "error",
            "transaction_reference": txn.reference,
            "message": "Could not reach payment gateway. Try again later.",
        }
    except httpx.RequestError as e:
        logger.error("Gateway verification network error for %s: %s", reference, e)
        return {
            "status": "error",
            "transaction_reference": txn.reference,
            "message": "Network error contacting payment gateway. Try again later.",
        }


def handle_paystack_webhook(payload: dict) -> dict:
    """
    Process a verified Paystack webhook event.
    Only handles 'charge.success' for now.
    """
    event = payload.get("event", "")
    if event != "charge.success":
        logger.info("Ignoring Paystack event: %s", event)
        return {"status": "ignored", "event": event}

    data = payload.get("data", {})
    reference = data.get("reference", "")
    if not reference:
        return {"status": "error", "message": "No reference in webhook payload."}

    return verify_payment(reference)



