"""
accounts app — Custom User model and OTP management.

Auth identifiers:
  Primary login: email + password
  OTP delivery:  email (Twilio Verify, channel='email') +
                 WhatsApp (Twilio Verify, channel='whatsapp') if whatsapp_number is set
"""
import uuid
import random
import string

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for ETIP consumers.

    Primary identifier : email  (used for login + OTP delivery)
    Secondary channel  : whatsapp_number  (optional — used for WhatsApp OTP delivery
                         and transaction notifications if provided)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Primary identifier — required, unique
    email = models.EmailField(unique=True, db_index=True)

    # Optional WhatsApp number — Nigerian local (08XXXXXXXXX) or +234 format
    # Used by Twilio Verify (channel='whatsapp') and for transaction SMS notifications
    whatsapp_number = models.CharField(
        max_length=20, unique=True, null=True, blank=True, db_index=True,
        help_text="Nigerian WhatsApp number e.g. 08140628953 or +2348140628953"
    )

    full_name = models.CharField(max_length=255, blank=True)

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Security
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    # Device token for push notifications
    fcm_token = models.CharField(max_length=512, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.email} ({self.full_name or 'No name'})"

    def save(self, *args, **kwargs):
        # Always store email in lowercase so admin-panel edits and API registrations
        # are consistent — the login serializer does .lower() before lookup.
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    @property
    def is_locked(self):
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False

    def increment_failed_login(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=15)
        self.save(update_fields=["failed_login_attempts", "locked_until"])

    def reset_failed_login(self):
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=["failed_login_attempts", "locked_until"])


class OTPVerification(models.Model):
    """
    Stores OTP codes for phone/email verification and password reset.
    """

    class Purpose(models.TextChoices):
        REGISTRATION = "REGISTRATION", "Registration"
        PASSWORD_RESET = "PASSWORD_RESET", "Password Reset"
        LOGIN = "LOGIN", "Login"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identifier = models.CharField(max_length=255, db_index=True)  # phone or email
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)

    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    resend_count = models.PositiveSmallIntegerField(default=0)
    last_resend_at = models.DateTimeField(null=True, blank=True)

    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "otp_verifications"
        indexes = [
            models.Index(fields=["identifier", "purpose", "is_used"]),
        ]

    @classmethod
    def generate_code(cls):
        return "".join(random.choices(string.digits, k=6))

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired and self.attempts < 5

    def __str__(self):
        return f"OTP[{self.purpose}] for {self.identifier}"


class PasswordResetToken(models.Model):
    """Tracks password reset attempts."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_tokens")
    token = models.CharField(max_length=64, unique=True, db_index=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "password_reset_tokens"

    @property
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
