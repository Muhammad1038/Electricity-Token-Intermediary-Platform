"""
transactions — Tests for Celery tasks.
"""
from unittest.mock import patch
from decimal import Decimal

import pytest

from apps.transactions.models import PaymentStatus, TokenStatus
from apps.transactions.tasks import (
    request_disco_token_task,
    _request_token_from_disco,
)


@pytest.mark.django_db
class TestTransactionTasks:

    @patch("apps.transactions.tasks._request_token_from_disco")
    @patch("apps.transactions.tasks.send_mail")
    def test_request_disco_token_task_success(self, mock_send_mail, mock_request, paid_transaction):
        mock_request.return_value = {
            "success": True,
            "token": "47133458396693522090",
            "disco_reference": "VTP-001",
            "units": "24.5",
        }
        
        request_disco_token_task(str(paid_transaction.id))
        
        paid_transaction.refresh_from_db()
        assert paid_transaction.token_status == TokenStatus.DELIVERED
        assert paid_transaction.token_value_encrypted
        assert mock_send_mail.called

    @patch("apps.transactions.tasks._request_token_from_disco")
    @patch("apps.transactions.tasks.send_mail")
    def test_request_disco_token_task_failure(self, mock_send_mail, mock_request, paid_transaction):
        from celery.exceptions import Retry
        mock_request.return_value = {
            "success": False,
            "error": "Timeout from VTPass",
        }
        
        with pytest.raises(Exception, match="Timeout from VTPass"):
            request_disco_token_task(str(paid_transaction.id))
        
        paid_transaction.refresh_from_db()
        assert paid_transaction.token_status == TokenStatus.PENDING  # Status remains pending during retries
        assert mock_send_mail.called is False  # Failure email only on max retries, handled differently

    @patch("apps.transactions.tasks.httpx.Client")
    def test_request_token_from_disco_http_success(self, mock_client, settings):
        settings.VTPASS_API_KEY = "test"
        settings.VTPASS_SECRET_KEY = "test"
        settings.DISCO_APIS = {"EEDC": {"vtpass_service_id": "enugu-electric"}}
        # Must disable test mode to hit http code
        settings.VTPASS_TEST_MODE = False
        
        mock_post = mock_client.return_value.__enter__.return_value.post
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "code": "000",
            "Token": "12345678901234567890",
            "purchased_code": "Token : 12345678901234567890",
            "PurchasedUnits": "13.3",
        }
        
        res = _request_token_from_disco("1111", "EEDC", Decimal("5000.00"), "ETIP-1")
        assert res["success"] is True
        assert res["token"] == "12345678901234567890"

    @patch("apps.transactions.tasks.httpx.Client")
    def test_request_token_from_disco_http_failure(self, mock_client, settings):
        settings.VTPASS_API_KEY = "test"
        settings.VTPASS_SECRET_KEY = "test"
        settings.DISCO_APIS = {"EEDC": {"vtpass_service_id": "enugu-electric"}}
        settings.VTPASS_TEST_MODE = False
        
        mock_post = mock_client.return_value.__enter__.return_value.post
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "code": "016",
            "response_description": "Failed transaction",
        }
        
        res = _request_token_from_disco("1111", "EEDC", Decimal("5000.00"), "ETIP-2")
        assert res["success"] is False
        assert res["error"] == "Failed transaction"

    def test_request_token_from_disco_test_mode(self, settings):
        settings.VTPASS_TEST_MODE = True
        res = _request_token_from_disco("1111", "EEDC", Decimal("5000.00"), "ETIP-3")
        assert res["success"] is True
        assert "TEST-ETIP-3" in res["disco_reference"]
