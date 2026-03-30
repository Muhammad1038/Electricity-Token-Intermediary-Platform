"""
payments — Tests for payment initiation, verification, and webhook handling.
"""
import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings
from django.urls import reverse

from apps.transactions.models import PaymentStatus, Transaction
from conftest import MeterProfileFactory, TransactionFactory


@pytest.mark.django_db
class TestPaymentServices:
    @patch("apps.payments.services._paystack_initialize")
    def test_initiate_payment_success(self, mock_init, auth_client, meter_profile):
        mock_init.return_value = {
            "authorization_url": "https://checkout.paystack.com/test",
            "access_code": "ACCESS_CODE",
            "reference": "ETIP-TEST123",
        }
        resp = auth_client.post(
            reverse("payment-initiate"),
            {
                "meter_id": str(meter_profile.id),
                "amount": "5000.00",
                "payment_gateway": "PAYSTACK",
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.data.get("data", resp.data)
        assert "transaction_reference" in data
        assert "authorization_url" in data

    def test_initiate_payment_invalid_meter(self, auth_client):
        import uuid
        resp = auth_client.post(
            reverse("payment-initiate"),
            {
                "meter_id": str(uuid.uuid4()),
                "amount": "5000.00",
                "payment_gateway": "PAYSTACK",
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_initiate_payment_unauthenticated(self, api_client):
        resp = api_client.post(
            reverse("payment-initiate"),
            {},
            format="json",
        )
        assert resp.status_code == 401

    def test_initiate_payment_empty_body(self, auth_client):
        resp = auth_client.post(
            reverse("payment-initiate"),
            {},
            format="json",
        )
        assert resp.status_code == 400

    @patch("apps.payments.services._paystack_verify")
    @patch("apps.transactions.tasks.request_disco_token_task.delay")
    def test_verify_payment_success(self, mock_task, mock_verify, auth_client, user, meter_profile):
        txn = TransactionFactory(user=user, meter=meter_profile, payment_status="PENDING")
        mock_verify.return_value = {
            "status": "success",
            "reference": txn.reference,
            "gateway_response": "Approved",
        }
        resp = auth_client.get(
            reverse("payment-verify") + f"?reference={txn.reference}"
        )
        assert resp.status_code == 200
        txn.refresh_from_db()
        assert txn.payment_status == PaymentStatus.SUCCESS

    @patch("apps.payments.services._paystack_verify")
    def test_verify_payment_failed(self, mock_verify, auth_client, user, meter_profile):
        txn = TransactionFactory(user=user, meter=meter_profile, payment_status="PENDING")
        mock_verify.return_value = {
            "status": "failed",
            "reference": txn.reference,
            "gateway_response": "Declined",
        }
        resp = auth_client.get(
            reverse("payment-verify") + f"?reference={txn.reference}"
        )
        assert resp.status_code == 400
        txn.refresh_from_db()
        assert txn.payment_status == PaymentStatus.FAILED

    def test_verify_payment_no_reference(self, auth_client):
        resp = auth_client.get(reverse("payment-verify"))
        assert resp.status_code == 400


@pytest.mark.django_db
class TestPaystackWebhook:
    def _make_signature(self, body: bytes) -> str:
        return hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode(),
            body,
            hashlib.sha512,
        ).hexdigest()

    def test_webhook_invalid_signature(self, api_client):
        body = json.dumps({"event": "charge.success"}).encode()
        resp = api_client.post(
            reverse("webhook-paystack"),
            data=body,
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE="badsignature",
        )
        assert resp.status_code == 400

    @patch("apps.payments.services.verify_payment")
    def test_webhook_valid_signature(self, mock_verify, api_client, user, meter_profile):
        txn = TransactionFactory(user=user, meter=meter_profile)
        payload = {"event": "charge.success", "data": {"reference": txn.reference}}
        body = json.dumps(payload).encode()
        signature = self._make_signature(body)
        mock_verify.return_value = {
            "status": "success",
            "transaction_reference": txn.reference,
            "message": "Payment verified.",
        }
        resp = api_client.post(
            reverse("webhook-paystack"),
            data=body,
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE=signature,
        )
        assert resp.status_code == 200
