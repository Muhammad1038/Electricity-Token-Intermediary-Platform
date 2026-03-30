"""
ETIP Backend — Shared pytest fixtures and factories.
"""
import uuid
from datetime import timedelta
from decimal import Decimal

import factory
import pytest
from django.utils import timezone
from rest_framework.test import APIClient


# ── Factories ────────────────────────────────────────────────────────────────


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for the custom User model."""

    class Meta:
        model = "accounts.User"
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@etip.test")
    full_name = factory.Faker("name")
    password = factory.PostGenerationMethodCall("set_password", "TestPass123!")
    is_verified = True
    is_active = True


class MeterProfileFactory(factory.django.DjangoModelFactory):
    """Factory for MeterProfile."""

    class Meta:
        model = "meters.MeterProfile"

    user = factory.SubFactory(UserFactory)
    meter_number = factory.Sequence(lambda n: f"4581109{n:04d}")
    disco = "EEDC"
    meter_type = "PREPAID"
    nickname = factory.LazyAttribute(lambda o: f"Meter {o.meter_number[-4:]}")
    meter_owner_name = factory.Faker("name")
    is_active = True
    is_default = False


class TransactionFactory(factory.django.DjangoModelFactory):
    """Factory for Transaction."""

    class Meta:
        model = "transactions.Transaction"

    user = factory.SubFactory(UserFactory)
    meter = factory.SubFactory(MeterProfileFactory, user=factory.SelfAttribute("..user"))
    reference = factory.LazyFunction(lambda: f"ETIP-{uuid.uuid4().hex[:12].upper()}")
    meter_number = factory.LazyAttribute(lambda o: o.meter.meter_number)
    disco = factory.LazyAttribute(lambda o: o.meter.disco)
    meter_owner_name = factory.LazyAttribute(lambda o: o.meter.meter_owner_name)
    amount = Decimal("5000.00")
    service_fee = Decimal("0.00")
    payment_gateway = "PAYSTACK"
    payment_status = "PENDING"
    token_status = "PENDING"


class OTPFactory(factory.django.DjangoModelFactory):
    """Factory for OTPVerification."""

    class Meta:
        model = "accounts.OTPVerification"

    identifier = factory.Sequence(lambda n: f"user{n}@etip.test")
    otp_code = "123456"
    purpose = "REGISTRATION"
    expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(minutes=10))


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def user(db):
    """A verified, active user."""
    return UserFactory()


@pytest.fixture
def staff_user(db):
    """A verified, active staff user (admin)."""
    return UserFactory(
        email="admin@etip.test",
        is_staff=True,
        is_verified=True,
    )


@pytest.fixture
def api_client():
    """Unauthenticated DRF APIClient."""
    return APIClient()


@pytest.fixture
def auth_client(user):
    """APIClient authenticated as a regular user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def staff_client(staff_user):
    """APIClient authenticated as a staff user."""
    client = APIClient()
    client.force_authenticate(user=staff_user)
    return client


@pytest.fixture
def meter_profile(user, db):
    """A meter profile belonging to the default user."""
    return MeterProfileFactory(user=user)


@pytest.fixture
def transaction(user, meter_profile, db):
    """A PENDING transaction for the default user."""
    return TransactionFactory(user=user, meter=meter_profile)


@pytest.fixture
def paid_transaction(user, meter_profile, db):
    """A transaction with payment SUCCESS but token still PENDING."""
    return TransactionFactory(
        user=user,
        meter=meter_profile,
        payment_status="SUCCESS",
        token_status="PENDING",
    )
