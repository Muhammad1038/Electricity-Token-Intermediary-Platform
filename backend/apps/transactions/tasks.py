"""
transactions — Celery tasks for automated token delivery after payment.

Flow: Webhook confirms payment → verify_payment() → request_disco_token_task
      → DISCO API returns token → store + notify user (email + SMS + push).
"""
import logging
import uuid

import httpx
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


# ── Email helpers for token notifications ─────────────────────────────────────

def _send_token_email(
    email: str,
    full_name: str,
    meter_number: str,
    token_value: str,
    amount: str,
    units: str,
    reference: str,
    disco: str,
):
    """Send a token delivery confirmation email."""
    units_line = f"Units: {units} kWh\n" if units else ""
    subject = f"⚡ Your Electricity Token is Ready — {reference}"
    body = (
        f"Hi {full_name},\n\n"
        f"Your electricity token has been delivered successfully!\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔑 Token: {token_value}\n"
        f"📊 Meter: {meter_number}\n"
        f"🏢 DISCO: {disco}\n"
        f"💰 Amount: ₦{amount}\n"
        f"{units_line}"
        f"📋 Reference: {reference}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Enter this token on your prepaid meter to load the units.\n\n"
        f"If you did not make this purchase, please contact support immediately.\n\n"
        f"Thank you for using ETIP!\n"
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@etip.ng")
    send_mail(subject, body, from_email, [email], fail_silently=False)
    logger.info("Token delivery email sent to %s for ref %s", email, reference)


def _send_token_failure_email(
    email: str,
    full_name: str,
    meter_number: str,
    amount: str,
    reference: str,
):
    """Send a token delivery failure notification email."""
    subject = f"⚠️ Token Delivery Issue — {reference}"
    body = (
        f"Hi {full_name},\n\n"
        f"We were unable to deliver your electricity token.\n\n"
        f"📊 Meter: {meter_number}\n"
        f"💰 Amount: ₦{amount}\n"
        f"📋 Reference: {reference}\n\n"
        f"Your payment is safe — our system will keep retrying automatically.\n"
        f"You can also tap 'Resend Token' in the app to try again manually.\n\n"
        f"If the issue persists, please contact our support team with your "
        f"reference number.\n\n"
        f"Thank you for your patience.\n"
        f"— ETIP Team\n"
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@etip.ng")
    send_mail(subject, body, from_email, [email], fail_silently=False)
    logger.info("Token failure email sent to %s for ref %s", email, reference)


def _request_token_from_disco(
    meter_number: str,
    disco: str,
    amount,
    reference: str,
    phone_number: str = "",
    meter_type: str = "prepaid",
) -> dict:
    """
    Purchase an electricity token from VTPass POST /api/pay.

    VTPass request_id must be unique — our ETIP reference (e.g. ETIP-ABC123DEF456)
    satisfies this requirement perfectly.

    Returns dict with:
        - success: bool
        - token: str  (the electricity token digits the customer loads on their meter)
        - disco_reference: str  (VTPass requestId, for reconciliation)
        - units: str  (kWh credited, e.g. "13.3")
        - error: str  (only on failure)
    """
    api_key    = getattr(settings, "VTPASS_API_KEY",    "")
    secret_key = getattr(settings, "VTPASS_SECRET_KEY", "")
    base_url   = getattr(settings, "VTPASS_BASE_URL",   "https://vtpass.com/api")

    disco_apis = getattr(settings, "DISCO_APIS", {})
    service_id = disco_apis.get(disco, {}).get("vtpass_service_id", "")

    # Hard fail if VTPass is not configured — no fake tokens in production.
    if not api_key or not secret_key:
        raise RuntimeError(
            "VTPass credentials (VTPASS_API_KEY / VTPASS_SECRET_KEY) are not configured."
        )
    if not service_id:
        raise ValueError(
            f"DISCO '{disco}' is not mapped to a VTPass serviceID. Check DISCO_APIS in settings."
        )

    # ── Real VTPass /api/pay call ─────────────────────────────────────────────
    # VTPass POST requests require api-key + secret-key as named headers (not Basic auth)
    headers = {
        "api-key": api_key,
        "secret-key": secret_key,
        "Content-Type": "application/json",
    }
    payload = {
        "request_id": reference,                 # Unique per transaction — must not be reused
        "serviceID": service_id,                 # e.g. "abuja-electric"
        "billersCode": meter_number,
        "variation_code": meter_type.lower(),    # "prepaid" or "postpaid"
        "amount": int(float(amount)),            # Naira integer (NOT kobo)
        "phone": phone_number or "08000000000",  # Customer phone for VTPass records
    }
    timeout = getattr(settings, "DISCO_REQUEST_TIMEOUT_SECONDS", 30)

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(f"{base_url}/pay", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        logger.debug(
            "VTPass /pay response for reference %s: code=%s description=%s",
            reference, data.get("code"), data.get("response_description"),
        )

        if data.get("code") != "000":
            return {
                "success": False,
                "error": data.get("response_description") or f"VTPass error code {data.get('code')}",
            }

        # VTPass returns the token in 'Token' (clean digits) and also in
        # 'purchased_code' as a formatted string like "Token : 47133458396693522090"
        token_value = (data.get("Token") or "").strip()
        if not token_value:
            # Parse the formatted string fallback
            raw = data.get("purchased_code", "")
            token_value = raw.replace("Token :", "").replace("token:", "").strip()

        if not token_value:
            return {"success": False, "error": "VTPass returned no token in response."}

        return {
            "success": True,
            "token": token_value,
            "disco_reference": data.get("requestId", reference),
            "units": str(data.get("PurchasedUnits") or ""),
        }

    except httpx.TimeoutException:
        return {"success": False, "error": "VTPass API timed out. Will retry."}
    except httpx.HTTPStatusError as exc:
        return {"success": False, "error": f"VTPass API error: HTTP {exc.response.status_code}"}
    except Exception as exc:
        return {"success": False, "error": f"VTPass unexpected error: {str(exc)}"}


def _requery_vtpass(reference: str) -> dict:
    """
    Query VTPass /requery to check status of a previous request.
    Used when retry gets 'REQUEST ID ALREADY EXIST' — the original may have succeeded.
    
    Returns same dict format as _request_token_from_disco.
    """
    api_key    = getattr(settings, "VTPASS_API_KEY",    "")
    secret_key = getattr(settings, "VTPASS_SECRET_KEY", "")
    base_url   = getattr(settings, "VTPASS_BASE_URL",   "https://vtpass.com/api")
    
    headers = {
        "api-key": api_key,
        "secret-key": secret_key,
        "Content-Type": "application/json",
    }
    timeout = getattr(settings, "DISCO_REQUEST_TIMEOUT_SECONDS", 30)

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{base_url}/requery",
                json={"request_id": reference},
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        logger.info(
            "VTPass /requery for %s: code=%s description=%s",
            reference, data.get("code"), data.get("response_description"),
        )

        if data.get("code") == "000":
            content = data.get("content", {}) or {}
            transactions = content.get("transactions", {}) or {}
            token_value = (
                transactions.get("Token", "")
                or transactions.get("token", "")
                or ""
            ).strip()
            if not token_value:
                raw = data.get("purchased_code", "") or transactions.get("purchased_code", "")
                token_value = raw.replace("Token :", "").replace("token:", "").strip()

            if token_value:
                return {
                    "success": True,
                    "token": token_value,
                    "disco_reference": data.get("requestId", reference),
                    "units": str(transactions.get("PurchasedUnits") or data.get("PurchasedUnits") or ""),
                }
            else:
                return {"success": False, "error": "Requery returned code 000 but no token."}

        # Non-success — transaction genuinely failed on VTPass side
        return {
            "success": False,
            "error": data.get("response_description") or f"Requery returned code {data.get('code')}",
        }

    except Exception as exc:
        logger.error("VTPass requery failed for %s: %s", reference, exc)
        return {"success": False, "error": f"Requery error: {str(exc)}"}



@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def request_disco_token_task(self, transaction_id: str):
    """
    Celery task: Request electricity token from the DISCO after payment success.

    Retries up to 3 times with 30-second delays on failure.
    On final failure, marks the transaction token as FAILED.
    """
    from apps.transactions.models import PaymentStatus, TokenStatus, Transaction
    from apps.transactions.services import fail_token, store_token

    try:
        txn = Transaction.objects.select_related("user", "meter").get(id=transaction_id)
    except Transaction.DoesNotExist:
        logger.error("Token task: Transaction %s not found.", transaction_id)
        return

    # Guard: only proceed if payment is confirmed and token is still pending
    if txn.payment_status != PaymentStatus.SUCCESS:
        logger.warning("Token task: Payment not SUCCESS for %s, skipping.", txn.reference)
        return
    if txn.token_status == TokenStatus.DELIVERED:
        logger.info("Token task: Token already delivered for %s, skipping.", txn.reference)
        return

    retry_num = self.request.retries
    # Generate unique request_id for retries — VTPass rejects duplicate request_ids
    request_id = txn.reference if retry_num == 0 else f"{txn.reference}-R{retry_num}"

    logger.info(
        "Requesting DISCO token for %s (request_id=%s) | meter=%s disco=%s amount=₦%s",
        txn.reference, request_id, txn.meter_number, txn.disco, txn.amount,
    )

    result = _request_token_from_disco(
        meter_number=txn.meter_number,
        disco=txn.disco,
        amount=txn.amount,
        reference=request_id,
        phone_number=txn.user.whatsapp_number or "",
        meter_type=txn.meter.meter_type if txn.meter else "prepaid",
    )

    if result["success"]:
        store_token(txn, token_value=result["token"], disco_reference=result.get("disco_reference", ""))
        logger.info("Token delivered for %s: %s...", txn.reference, result["token"][:8])

        # Notify user asynchronously (include kWh units from VTPass)
        _notify_user_token_delivered(txn, result["token"], units=result.get("units", ""))
    else:
        error = result.get("error", "Unknown DISCO error")

        # If VTPass says "REQUEST ID ALREADY EXIST", the original request may have
        # succeeded — use /requery to check before giving up.
        if "REQUEST ID ALREADY EXIST" in error.upper() or "REQUEST_ID" in error.upper():
            logger.info("Request ID already exists for %s (request_id=%s) — requerying VTPass...", txn.reference, request_id)
            requery_result = _requery_vtpass(request_id)
            if requery_result["success"]:
                store_token(txn, token_value=requery_result["token"], disco_reference=requery_result.get("disco_reference", ""))
                logger.info("Requery recovered token for %s: %s...", txn.reference, requery_result["token"][:8])
                _notify_user_token_delivered(txn, requery_result["token"], units=requery_result.get("units", ""))
                return
            else:
                logger.warning("Requery for %s also failed: %s", txn.reference, requery_result.get("error"))

        logger.warning(
            "DISCO token request failed for %s (attempt %d/%d): %s",
            txn.reference, self.request.retries + 1, self.max_retries + 1, error,
        )

        if self.request.retries < self.max_retries:
            raise self.retry(exc=Exception(error))
        else:
            # Final failure — mark token as failed
            fail_token(txn, reason=f"DISCO token request failed after {self.max_retries + 1} attempts: {error}")
            _notify_user_token_failed(txn)


def _notify_user_token_delivered(txn, token_value: str, units: str = ""):
    """Send email + optional SMS + push notification for successful token delivery."""
    from apps.notifications.tasks import send_push_notification_task, send_sms_task

    user = txn.user
    meter = txn.meter_number
    units_line = f"Units: {units} kWh\n" if units else ""

    # ── Email notification (primary channel) ──────────────────────────────
    if user.email:
        try:
            _send_token_email(
                email=user.email,
                full_name=user.full_name or "Customer",
                meter_number=meter,
                token_value=token_value,
                amount=str(txn.amount),
                units=units,
                reference=txn.reference,
                disco=txn.disco,
            )
        except Exception as exc:
            logger.error("Failed to send token email for %s: %s", txn.reference, exc)

    # ── WhatsApp SMS (optional — only if configured) ─────────────────────
    try:
        if user.whatsapp_number:
            sms_message = (
                f"ETIP: Your electricity token for meter {meter} is ready!\n"
                f"Token: {token_value}\n"
                f"{units_line}"
                f"Amount: N{txn.amount}\n"
                f"Ref: {txn.reference}"
            )
            send_sms_task.delay(user.whatsapp_number, sms_message)
    except Exception as exc:
        logger.error("Failed to queue SMS for %s: %s", txn.reference, exc)

    # ── Push notification (optional — only if FCM token exists) ──────────
    if getattr(user, 'fcm_token', None):
        try:
            send_push_notification_task.delay(
                user.fcm_token,
                "Token Ready! ⚡",
                f"Your electricity token for meter {meter} has been delivered.",
                {"transaction_id": str(txn.id), "type": "token_delivered"},
            )
        except Exception as exc:
            logger.error("Failed to queue push notification for %s: %s", txn.reference, exc)


def _notify_user_token_failed(txn):
    """Notify user that token delivery failed (email + optional SMS/push)."""
    from apps.notifications.tasks import send_push_notification_task, send_sms_task

    user = txn.user

    # ── Email notification (primary channel) ──────────────────────────────
    if user.email:
        try:
            _send_token_failure_email(
                email=user.email,
                full_name=user.full_name or "Customer",
                meter_number=txn.meter_number,
                amount=str(txn.amount),
                reference=txn.reference,
            )
        except Exception as exc:
            logger.error("Failed to send failure email for %s: %s", txn.reference, exc)

    # ── WhatsApp SMS (optional) ──────────────────────────────────────────
    try:
        if user.whatsapp_number:
            sms_message = (
                f"ETIP: Token delivery failed for meter {txn.meter_number}.\n"
                f"Ref: {txn.reference}\n"
                f"Your payment is safe. We're working on it. "
                f"You can also retry from the app."
            )
            send_sms_task.delay(user.whatsapp_number, sms_message)
    except Exception as exc:
        logger.error("Failed to queue failure SMS for %s: %s", txn.reference, exc)

    # ── Push notification (optional) ─────────────────────────────────────
    if getattr(user, 'fcm_token', None):
        try:
            send_push_notification_task.delay(
                user.fcm_token,
                "Token Delivery Issue",
                f"We couldn't deliver your token for meter {txn.meter_number}. Tap to retry.",
                {"transaction_id": str(txn.id), "type": "token_failed"},
            )
        except Exception as exc:
            logger.error("Failed to queue failure push for %s: %s", txn.reference, exc)
