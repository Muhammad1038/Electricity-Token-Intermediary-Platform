"""
accounts — Tests for User model, OTP management, auth views.
"""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import OTPVerification, User
from conftest import OTPFactory, UserFactory


# ── Model Tests ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(
            email="TEST@ETIP.COM", password="TestPass123!"
        )
        assert user.email == "test@etip.com"  # lowercased on save
        assert user.check_password("TestPass123!")
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_user_no_email_raises(self):
        with pytest.raises(ValueError, match="Email"):
            User.objects.create_user(email="", password="TestPass123!")

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email="super@etip.test", password="SuperPass123!"
        )
        assert user.is_staff
        assert user.is_superuser
        assert user.is_verified

    def test_email_always_lowercase(self):
        user = UserFactory(email="MiXeD@ETIP.COM")
        user.refresh_from_db()
        assert user.email == "mixed@etip.com"

    def test_account_lockout_after_5_failures(self):
        user = UserFactory()
        for _ in range(5):
            user.increment_failed_login()
        user.refresh_from_db()
        assert user.is_locked
        assert user.locked_until is not None

    def test_reset_failed_login(self):
        user = UserFactory()
        user.increment_failed_login()
        user.increment_failed_login()
        user.reset_failed_login()
        user.refresh_from_db()
        assert user.failed_login_attempts == 0
        assert user.locked_until is None


@pytest.mark.django_db
class TestOTPModel:
    def test_generate_code_is_6_digits(self):
        code = OTPVerification.generate_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_otp_is_expired(self):
        otp = OTPFactory(expires_at=timezone.now() - timedelta(minutes=1))
        assert otp.is_expired

    def test_otp_is_valid(self):
        otp = OTPFactory(expires_at=timezone.now() + timedelta(minutes=10))
        assert otp.is_valid

    def test_otp_invalid_when_used(self):
        otp = OTPFactory(is_used=True)
        assert not otp.is_valid


# ── View / API Tests ────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAuthViews:
    @patch("apps.accounts.services.create_and_send_otp")
    def test_register_sends_otp(self, mock_otp, api_client):
        mock_otp.return_value = {"message": "OTP sent"}
        resp = api_client.post(
            reverse("auth-register"),
            {"email": "new@etip.test", "full_name": "New User"},
            format="json",
        )
        assert resp.status_code == 200
        mock_otp.assert_called_once()

    def test_login_wrong_password(self, api_client, user):
        resp = api_client.post(
            reverse("auth-login"),
            {"email": user.email, "password": "wrongPassword1!"},
            format="json",
        )
        assert resp.status_code == 401

    def test_login_success(self, api_client, user):
        resp = api_client.post(
            reverse("auth-login"),
            {"email": user.email, "password": "TestPass123!"},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.data.get("data", resp.data)
        assert "access" in data
        assert "refresh" in data

    def test_profile_authenticated(self, auth_client, user):
        resp = auth_client.get(reverse("auth-profile"))
        assert resp.status_code == 200

    def test_profile_unauthenticated(self, api_client):
        resp = api_client.get(reverse("auth-profile"))
        assert resp.status_code == 401

    @patch("apps.accounts.services.create_and_send_otp")
    def test_password_reset_request(self, mock_otp, api_client, user):
        mock_otp.return_value = {"message": "OTP sent"}
        resp = api_client.post(
            reverse("auth-password-reset"),
            {"email": user.email},
            format="json",
        )
        # Always returns 200 to prevent email enumeration
        assert resp.status_code == 200
