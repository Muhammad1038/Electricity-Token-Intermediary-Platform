"""
notifications — Service layer for WhatsApp SMS (Twilio) and FCM push notifications.

Token delivery alerts and failure notices go via Twilio WhatsApp Messaging API,
using the user's whatsapp_number.

OTP specifically uses Django SMTP email (managed in accounts/services.py).

Twilio Console: https://www.twilio.com/console
WhatsApp docs:  https://www.twilio.com/docs/whatsapp/api
"""
import logging

logger = logging.getLogger(__name__)


def send_whatsapp(whatsapp_number: str, message: str) -> bool:
    """
    Sends a non-OTP notification via Twilio WhatsApp Messaging API.
    Raises on failure so the Celery task can retry.

    Returns False (no-op) if Twilio is not configured — this prevents
    the Celery task from retrying 3 times for no reason.

    whatsapp_number is accepted in Nigerian local format (08XXXXXXXXX) or E.164.
    Twilio WhatsApp requires both from_ and to to have the 'whatsapp:' prefix.
    """
    from django.conf import settings

    account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
    auth_token  = getattr(settings, "TWILIO_AUTH_TOKEN",  "")
    from_number = getattr(settings, "TWILIO_PHONE_NUMBER", "")

    if not account_sid or not auth_token or not from_number:
        logger.info(
            "Twilio not configured — skipping WhatsApp message to %s",
            whatsapp_number,
        )
        return False

    try:
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioRestException
    except ImportError:
        logger.warning("twilio package not installed — skipping WhatsApp message")
        return False

    from apps.accounts.services import _to_e164_nigeria

    e164 = _to_e164_nigeria(whatsapp_number)
    client = Client(account_sid, auth_token)
    try:
        msg = client.messages.create(
            body=message,
            from_=f"whatsapp:{from_number}",   # e.g. whatsapp:+14155238886
            to=f"whatsapp:{e164}",             # e.g. whatsapp:+2348140628953
        )
        logger.info("Twilio WhatsApp sent to %s (SID=%s)", e164, msg.sid)
        return True
    except TwilioRestException as exc:
        logger.error("Twilio WhatsApp failed for %s: %s", e164, exc)
        raise  # Let Celery retry


# Keep legacy name as an alias so existing callers don't break
send_sms = send_whatsapp


def send_push_notification(fcm_token: str, title: str, body: str, data: dict = None) -> bool:
    """
    Sends a push notification via Firebase Cloud Messaging.
    Returns False (no-op) if Firebase is not configured.
    """
    from django.conf import settings
    import os

    creds_path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", "")
    if not creds_path or not os.path.exists(creds_path):
        logger.info("Firebase credentials not found at '%s' — skipping push notification", creds_path)
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
    except ImportError:
        logger.warning("firebase-admin package not installed — skipping push notification")
        return False

    if not firebase_admin._apps:
        cred = credentials.Certificate(creds_path)
        firebase_admin.initialize_app(cred)

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data={k: str(v) for k, v in (data or {}).items()},
        token=fcm_token,
    )
    messaging.send(message)
    logger.info("Push notification sent to FCM token: %s...", fcm_token[:10])
    return True
