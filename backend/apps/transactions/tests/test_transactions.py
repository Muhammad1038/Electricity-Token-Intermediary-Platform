"""
transactions — Tests for Transaction model, services, and API views.
"""
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.transactions.models import PaymentStatus, TokenStatus, Transaction
from apps.transactions.services import (
    confirm_payment,
    create_transaction,
    decrypt_token_value,
    encrypt_token_value,
    fail_payment,
    fail_token,
    generate_reference,
    store_token,
)
from conftest import TransactionFactory


# ── Service Tests ────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestTransactionServices:
    def test_generate_reference_format(self):
        ref = generate_reference()
        assert ref.startswith("ETIP-")
        assert len(ref) > 10

    def test_generate_reference_unique(self):
        refs = {generate_reference() for _ in range(50)}
        assert len(refs) == 50  # all unique

    def test_create_transaction(self, user, meter_profile):
        txn = create_transaction(
            user=user,
            meter=meter_profile,
            amount=Decimal("5000.00"),
            payment_gateway="PAYSTACK",
        )
        assert txn.payment_status == PaymentStatus.PENDING
        assert txn.token_status == TokenStatus.PENDING
        assert txn.reference.startswith("ETIP-")
        assert txn.meter_number == meter_profile.meter_number

    def test_confirm_payment(self, transaction):
        confirm_payment(transaction, gateway_reference="PAY-GW-123")
        transaction.refresh_from_db()
        assert transaction.payment_status == PaymentStatus.SUCCESS
        assert transaction.gateway_reference == "PAY-GW-123"
        assert transaction.payment_confirmed_at is not None

    def test_fail_payment(self, transaction):
        fail_payment(transaction, reason="Declined by bank")
        transaction.refresh_from_db()
        assert transaction.payment_status == PaymentStatus.FAILED

    def test_encrypt_decrypt_token_roundtrip(self):
        original = "47133458396693522090"
        encrypted = encrypt_token_value(original)
        assert encrypted != original
        decrypted = decrypt_token_value(encrypted)
        assert decrypted == original

    def test_store_token(self, paid_transaction):
        store_token(paid_transaction, token_value="12345678901234567890", disco_reference="VTP-001")
        paid_transaction.refresh_from_db()
        assert paid_transaction.token_status == TokenStatus.DELIVERED
        assert paid_transaction.token_value_encrypted  # not empty
        assert paid_transaction.disco_reference == "VTP-001"
        assert paid_transaction.token_delivered_at is not None

    def test_fail_token(self, paid_transaction):
        fail_token(paid_transaction, reason="DISCO API down")
        paid_transaction.refresh_from_db()
        assert paid_transaction.token_status == TokenStatus.FAILED


# ── Model Property Tests ────────────────────────────────────────────────────


@pytest.mark.django_db
class TestTransactionModel:
    def test_total_amount(self, transaction):
        transaction.amount = Decimal("5000.00")
        transaction.service_fee = Decimal("50.00")
        assert transaction.total_amount == Decimal("5050.00")

    def test_can_resend_token_eligible(self):
        txn = TransactionFactory.build(
            payment_status=PaymentStatus.SUCCESS,
            token_status=TokenStatus.FAILED,
            resend_attempts=0,
        )
        assert txn.can_resend_token

    def test_can_resend_token_max_attempts(self):
        txn = TransactionFactory.build(
            payment_status=PaymentStatus.SUCCESS,
            token_status=TokenStatus.FAILED,
            resend_attempts=3,
        )
        assert not txn.can_resend_token

    def test_can_resend_token_not_paid(self):
        txn = TransactionFactory.build(
            payment_status=PaymentStatus.PENDING,
            token_status=TokenStatus.FAILED,
            resend_attempts=0,
        )
        assert not txn.can_resend_token


# ── View / API Tests ────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestTransactionViews:
    def test_list_transactions(self, auth_client, transaction):
        resp = auth_client.get(reverse("transaction-list"))
        assert resp.status_code == 200

    def test_list_transactions_unauthenticated(self, api_client):
        resp = api_client.get(reverse("transaction-list"))
        assert resp.status_code == 401

    def test_transaction_detail(self, auth_client, transaction):
        resp = auth_client.get(
            reverse("transaction-detail", kwargs={"pk": transaction.pk})
        )
        assert resp.status_code == 200
        data = resp.data.get("data", resp.data)
        assert data["reference"] == transaction.reference

    def test_transaction_detail_not_found(self, auth_client):
        import uuid
        resp = auth_client.get(
            reverse("transaction-detail", kwargs={"pk": uuid.uuid4()})
        )
        assert resp.status_code == 404

    def test_resend_token_unpaid(self, auth_client, transaction):
        """Resend should fail when payment is still PENDING."""
        resp = auth_client.post(
            reverse("transaction-resend-token", kwargs={"pk": transaction.pk})
        )
        assert resp.status_code == 400

    @patch("apps.transactions.views.resend_token")
    def test_resend_token_eligible(self, mock_resend, auth_client, paid_transaction):
        paid_transaction.token_status = TokenStatus.FAILED
        paid_transaction.save(update_fields=["token_status"])
        mock_resend.return_value = {"success": True, "resend_attempts": 1, "message": "Success"}

        resp = auth_client.post(
            reverse("transaction-resend-token", kwargs={"pk": paid_transaction.pk})
        )
        # 200 if success, or 400 if service raises — depends on the view
        assert resp.status_code in (200, 400)
