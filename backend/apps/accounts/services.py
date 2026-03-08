"""
accounts — Business logic / service layer.

Auth flow:
  Register  → create_and_send_otp(email, whatsapp_number)
            → OTP sent via email (always) + WhatsApp (if provided)
  Verify    → verify_otp(email, code)
  Login     → email + password (standard Django authenticate)
  Reset     → create_and_send_otp(email) → verify_otp → set new password
"""
import logging

from django.conf import settings
from django.utils import timezone

from .models import OTPVerification, User

logger = logging.getLogger(__name__)


# ── OTP Helpers ────────────────────────────────────────────────────────────────

def create_and_send_otp(
    identifier: str,
    purpose: str,
    whatsapp_number: str = "",
) -> OTPVerification:
    """
    Creates a new OTP for the given identifier (email) and purpose,
    invalidates any previous unused OTPs for same identifier+purpose,
    and dispatches it:
      • Email (always)         — Twilio Verify channel='email'
      • WhatsApp (if provided) — Twilio Verify channel='whatsapp'

    In DEBUG mode the local otp_code is available for testing without
    real email delivery.
    """
    OTPVerification.objects.filter(
        identifier=identifier,
        purpose=purpose,
        is_used=False,
    ).update(is_used=True)

    otp = OTPVerification.objects.create(
        identifier=identifier,
        otp_code=OTPVerification.generate_code(),
        purpose=purpose,
        expires_at=timezone.now() + timezone.timedelta(seconds=settings.OTP_EXPIRY_SECONDS),
    )

    _dispatch_otp(identifier, otp.otp_code, purpose, whatsapp_number)
    logger.info("OTP created for %s [%s]", identifier, purpose)
    return otp


def resend_otp(
    identifier: str,
    purpose: str,
    whatsapp_number: str = "",
) -> OTPVerification:
    """Resends OTP if the cooldown period has passed."""
    existing = OTPVerification.objects.filter(
        identifier=identifier,
        purpose=purpose,
        is_used=False,
    ).order_by("-created_at").first()

    if existing:
        cooldown = settings.OTP_RESEND_COOLDOWN_SECONDS
        if existing.last_resend_at:
            elapsed = (timezone.now() - existing.last_resend_at).total_seconds()
        else:
            elapsed = (timezone.now() - existing.created_at).total_seconds()

        if elapsed < cooldown:
            remaining = int(cooldown - elapsed)
            raise ValueError(f"Please wait {remaining} seconds before resending.")

        existing.resend_count += 1
        existing.last_resend_at = timezone.now()
        existing.save(update_fields=["resend_count", "last_resend_at"])
        _dispatch_otp(identifier, existing.otp_code, purpose, whatsapp_number)
        return existing

    return create_and_send_otp(identifier, purpose, whatsapp_number)


def verify_otp(identifier: str, otp_code: str, purpose: str) -> bool:
    """
    Verifies OTP. Returns True on success, raises ValueError on failure.

    In DEBUG mode: checks local DB otp_code (no Twilio needed).
    In production: calls Twilio Verify — identifier must be the email address
                   used when sending the OTP.
    """
    otp = OTPVerification.objects.filter(
        identifier=identifier,
        purpose=purpose,
        is_used=False,
    ).order_by("-created_at").first()

    if not otp:
        raise ValueError("No active OTP found. Please request a new one.")

    if otp.is_expired:
        raise ValueError("OTP has expired. Please request a new one.")

    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        raise ValueError("Too many attempts. Please request a new OTP.")

    # Verify code against DB record — the same code was emailed to the user
    if otp.otp_code != otp_code:
        otp.attempts += 1
        otp.save(update_fields=["attempts"])
        remaining = settings.OTP_MAX_ATTEMPTS - otp.attempts
        raise ValueError(f"Invalid OTP. {remaining} attempts remaining.")

    otp.is_used = True
    otp.save(update_fields=["is_used"])
    return True


# ── User Creation ──────────────────────────────────────────────────────────────

def register_user(
    email: str,
    password: str,
    full_name: str = "",
    whatsapp_number: str = "",
) -> User:
    """Creates a verified user account after OTP has been confirmed."""
    user = User.objects.create_user(
        email=email,
        password=password,
        full_name=full_name,
        whatsapp_number=whatsapp_number or None,
        is_verified=True,
    )
    logger.info("User registered", extra={"user_id": str(user.id), "email": email})
    return user


# ── Password Reset ─────────────────────────────────────────────────────────────

def initiate_password_reset(email: str):
    """
    Sends OTP to registered email for password reset.
    Silent if user doesn't exist (security — don't reveal account existence).
    """
    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        logger.info("Password reset attempted for non-existent email: %s", email)
        return None
    return create_and_send_otp(
        email,
        OTPVerification.Purpose.PASSWORD_RESET,
        whatsapp_number=user.whatsapp_number or "",
    )


def confirm_password_reset(email: str, otp_code: str, new_password: str) -> None:
    """Verifies OTP and sets new password; invalidates all existing sessions."""
    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        raise ValueError("Account not found.")

    verify_otp(email, otp_code, OTPVerification.Purpose.PASSWORD_RESET)

    user.set_password(new_password)
    user.failed_login_attempts = 0
    user.locked_until = None
    user.save(update_fields=["password", "failed_login_attempts", "locked_until"])
    logger.info("Password reset completed", extra={"user_id": str(user.id)})


# ── Twilio Verify helpers ─────────────────────────────────────────────────────

def _to_e164_nigeria(phone: str) -> str:
    """
    Convert a Nigerian WhatsApp number to E.164 format required by Twilio.

    08140628953    →  +2348140628953
    2348140628953  →  +2348140628953
    +2348140628953 →  +2348140628953  (unchanged)
    """
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+234"):
        return phone
    if phone.startswith("234"):
        return f"+{phone}"
    if phone.startswith("0") and len(phone) == 11:
        return f"+234{phone[1:]}"
    raise ValueError(
        f"Cannot convert '{phone}' to E.164 — expected Nigerian 08XXXXXXXXX or +234 format."
    )


def _send_otp_email(email: str, otp_code: str, purpose: str) -> None:
    """
    Send the OTP code to the user's email via Django SMTP.
    No Twilio dependency — works with any SMTP provider (Gmail, etc.).
    """
    from django.core.mail import send_mail

    purpose_labels = {
        "REGISTRATION": "Account Verification",
        "PASSWORD_RESET": "Password Reset",
    }
    label = purpose_labels.get(purpose, "Verification")

    subject = f"Your ETIP {label} Code: {otp_code}"
    body = (
        f"Hello,\n\n"
        f"Your ETIP {label} code is:\n\n"
        f"    {otp_code}\n\n"
        f"This code expires in {settings.OTP_EXPIRY_SECONDS // 60} minutes.\n"
        f"Do not share this code with anyone.\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"— The ETIP Team"
    )
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
    logger.info("OTP email sent to %s (purpose=%s)", email, purpose)


def _send_otp_whatsapp(whatsapp_number: str, otp_code: str, purpose: str) -> None:
    """
    Send the OTP code to the user's WhatsApp number via Twilio Messaging API.
    Non-fatal — WhatsApp is a convenience copy; email is the primary channel.
    """
    from twilio.rest import Client

    purpose_labels = {
        "REGISTRATION": "account verification",
        "PASSWORD_RESET": "password reset",
    }
    label = purpose_labels.get(purpose, "verification")

    try:
        e164 = _to_e164_nigeria(whatsapp_number)
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=(
                f"Your ETIP {label} code is: *{otp_code}*\n"
                f"Valid for {settings.OTP_EXPIRY_SECONDS // 60} minutes. Do not share it."
            ),
            from_=f"whatsapp:{settings.TWILIO_PHONE_NUMBER}",
            to=f"whatsapp:{e164}",
        )
        logger.info("OTP WhatsApp sent to %s (purpose=%s)", e164, purpose)
    except Exception as exc:  # noqa: BLE001
        logger.warning("WhatsApp OTP delivery failed for %s (non-fatal): %s", whatsapp_number, exc)


# ── Internal dispatcher ────────────────────────────────────────────────────────

def _dispatch_otp(
    email: str,
    otp_code: str,
    purpose: str,
    whatsapp_number: str = "",
) -> None:
    """
    Dispatches OTP to up to two channels:
      1. Email   (always)             — Django SMTP, code embedded in message
      2. WhatsApp (if number given)   — Twilio WhatsApp message (non-fatal)

    OTP verification checks the code against the DB record (not Twilio Verify).
    """
    # Email — primary (and currently only) channel
    _send_otp_email(email, otp_code, purpose)

    # WhatsApp disabled until a production Twilio WhatsApp number is configured.
    # Uncomment the block below when ready:
    # if whatsapp_number:
    #     _send_otp_whatsapp(whatsapp_number, otp_code, purpose)
