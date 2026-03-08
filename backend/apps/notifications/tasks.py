"""
notifications — Celery tasks for WhatsApp SMS and push notifications.
Token delivery/failure alerts are sent via Twilio WhatsApp Messaging API.
OTP is managed separately in accounts/services.py via Django SMTP email.
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_sms_task(self, phone_number: str, message: str):
    """Send a WhatsApp notification via Twilio Messaging API."""
    from .services import send_whatsapp
    try:
        result = send_whatsapp(phone_number, message)
        if not result:
            # Service not configured — don't retry
            logger.info("WhatsApp not configured, skipping for %s", phone_number)
            return
    except Exception as exc:
        logger.error("WhatsApp send failed for %s: %s", phone_number, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_push_notification_task(self, fcm_token: str, title: str, body: str, data: dict = None):
    """Send push notification via Firebase Cloud Messaging."""
    from .services import send_push_notification
    try:
        result = send_push_notification(fcm_token, title, body, data or {})
        if not result:
            # Firebase not configured — don't retry
            logger.info("Push notifications not configured, skipping")
            return
    except Exception as exc:
        logger.error("Push notification failed for token %s: %s", fcm_token[:10], exc)
        raise self.retry(exc=exc)
