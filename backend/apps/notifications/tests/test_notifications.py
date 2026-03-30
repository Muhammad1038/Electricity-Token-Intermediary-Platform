"""
notifications — Tests for WhatsApp, push notification services, and Celery tasks.
"""
from unittest.mock import patch

import pytest

from apps.notifications.services import send_push_notification, send_whatsapp


@pytest.mark.django_db
class TestNotificationServices:
    def test_send_whatsapp_not_configured(self, settings):
        """Returns False when Twilio credentials are missing."""
        settings.TWILIO_ACCOUNT_SID = ""
        settings.TWILIO_AUTH_TOKEN = ""
        settings.TWILIO_PHONE_NUMBER = ""
        result = send_whatsapp("08140628953", "Test message")
        assert result is False

    def test_send_push_no_firebase(self, settings):
        """Returns False when Firebase credentials path is missing."""
        settings.FIREBASE_CREDENTIALS_PATH = "/nonexistent/path.json"
        result = send_push_notification("fake_token", "Title", "Body")
        assert result is False


@pytest.mark.django_db
class TestNotificationTasks:
    @patch("apps.notifications.services.send_whatsapp", return_value=False)
    def test_sms_task_skips_unconfigured(self, mock_sms):
        from apps.notifications.tasks import send_sms_task
        # With eager Celery, this runs synchronously
        send_sms_task("08140628953", "Test")
        mock_sms.assert_called_once()

    @patch("apps.notifications.services.send_push_notification", return_value=False)
    def test_push_task_skips_unconfigured(self, mock_push):
        from apps.notifications.tasks import send_push_notification_task
        send_push_notification_task("fake_token", "Title", "Body", {})
        mock_push.assert_called_once()
