"""
accounts — Serializers for Auth endpoints.

Auth identifier  : email (primary, required everywhere)
WhatsApp number  : optional — secondary OTP delivery channel + notifications
"""
import re

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import OTPVerification, User


# ── Shared validators ───────────────────────────────────────────────────────────

def _validate_password_strength(value: str) -> str:
    if not re.search(r"[A-Z]", value):
        raise serializers.ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r"\d", value):
        raise serializers.ValidationError("Password must contain at least one number.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise serializers.ValidationError("Password must contain at least one special character.")
    return value


def _normalize_whatsapp(value: str) -> str:
    """Normalize a Nigerian WhatsApp number to E.164 (+2348XXXXXXXXX)."""
    value = re.sub(r"[\s\-]", "", value)
    if value.startswith("+234"):
        return value
    if value.startswith("234") and len(value) == 13:
        return "+" + value
    if value.startswith("0") and len(value) == 11:
        return "+234" + value[1:]
    raise serializers.ValidationError(
        "Enter a valid Nigerian WhatsApp number (e.g. 08012345678 or +2348012345678)."
    )


# ── Auth serializers ────────────────────────────────────────────────────────────

class UserRegistrationSerializer(serializers.Serializer):
    """Step 1: submit email. OTP will be sent to email + WhatsApp (if provided)."""
    email = serializers.EmailField()
    whatsapp_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    full_name = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_whatsapp_number(self, value):
        if not value:
            return value
        return _normalize_whatsapp(value)


class OTPVerifySerializer(serializers.Serializer):
    """Step 2: verify OTP sent to email, then create account with a password."""
    email = serializers.EmailField()
    otp_code = serializers.CharField(min_length=6, max_length=6)
    password = serializers.CharField(min_length=8, write_only=True)
    full_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    whatsapp_number = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_whatsapp_number(self, value):
        if not value:
            return value
        return _normalize_whatsapp(value)

    def validate_password(self, value):
        return _validate_password_strength(value)


class OTPResendSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=OTPVerification.Purpose.choices)

    def validate_email(self, value):
        return value.strip().lower()


class LoginSerializer(serializers.Serializer):
    """Login with email + password."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        return value.strip().lower()


class PasswordResetRequestSerializer(serializers.Serializer):
    """Request a password-reset OTP sent to the registered email."""
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(min_length=8, write_only=True)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_new_password(self, value):
        return _validate_password_strength(value)


class ChangePasswordSerializer(serializers.Serializer):
    """Authenticated password change — requires old password."""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=8, write_only=True)

    def validate_new_password(self, value):
        return _validate_password_strength(value)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "whatsapp_number", "full_name", "is_verified", "is_staff", "created_at"]
        read_only_fields = ["id", "email", "is_verified", "is_staff", "created_at"]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds user info to the JWT token response."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["full_name"] = user.full_name
        token["is_verified"] = user.is_verified
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "whatsapp_number": self.user.whatsapp_number or "",
            "full_name": self.user.full_name,
            "is_verified": self.user.is_verified,
            "is_staff": self.user.is_staff,
        }
        return data
