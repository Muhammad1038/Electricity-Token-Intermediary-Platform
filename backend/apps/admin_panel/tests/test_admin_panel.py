"""
admin_panel — Tests for dashboard, customer management, audit logs, and middleware.
"""
from decimal import Decimal

import pytest
from django.test import RequestFactory
from django.urls import reverse

from apps.admin_panel.middleware import AuditLogMiddleware
from apps.admin_panel.models import AdminUser, AuditLog
from apps.transactions.models import PaymentStatus, TokenStatus
from conftest import TransactionFactory, UserFactory


@pytest.mark.django_db
class TestDashboardViews:
    def test_dashboard_stats(self, staff_client, user, meter_profile):
        # Create some transactions for stats
        TransactionFactory(user=user, meter=meter_profile, payment_status="SUCCESS")
        TransactionFactory(user=user, meter=meter_profile, payment_status="PENDING")

        resp = staff_client.get(reverse("admin-dashboard"))
        assert resp.status_code == 200
        data = resp.data.get("data", resp.data)
        assert "total_users" in data
        assert "total_transactions" in data
        assert "total_revenue" in data

    def test_dashboard_requires_staff(self, auth_client):
        resp = auth_client.get(reverse("admin-dashboard"))
        assert resp.status_code == 403


@pytest.mark.django_db
class TestCustomerManagement:
    def test_customer_list(self, staff_client, user):
        resp = staff_client.get(reverse("admin-user-list"))
        assert resp.status_code == 200

    def test_customer_list_with_search(self, staff_client, user):
        resp = staff_client.get(
            reverse("admin-user-list") + f"?search={user.email}"
        )
        assert resp.status_code == 200

    def test_customer_detail(self, staff_client, user):
        resp = staff_client.get(
            reverse("admin-user-detail", kwargs={"pk": user.pk})
        )
        assert resp.status_code == 200

    def test_suspend_customer(self, staff_client, user):
        resp = staff_client.post(
            reverse("admin-user-suspend", kwargs={"pk": user.pk}),
            {"suspend": True, "reason": "Test suspension"},
            format="json",
        )
        assert resp.status_code == 200
        user.refresh_from_db()
        assert not user.is_active

        # Verify audit log was created
        assert AuditLog.objects.filter(action="user.suspend").exists()

    def test_reactivate_customer(self, staff_client, user):
        user.is_active = False
        user.save(update_fields=["is_active"])

        resp = staff_client.post(
            reverse("admin-user-suspend", kwargs={"pk": user.pk}),
            {"suspend": False},
            format="json",
        )
        assert resp.status_code == 200
        user.refresh_from_db()
        assert user.is_active


@pytest.mark.django_db
class TestTransactionManagement:
    def test_admin_transaction_list(self, staff_client, transaction):
        resp = staff_client.get(reverse("admin-transaction-list"))
        assert resp.status_code == 200

    def test_resolve_transaction(self, staff_client, transaction):
        resp = staff_client.post(
            reverse("admin-transaction-resolve", kwargs={"pk": transaction.pk}),
            {"resolution_notes": "Resolved by admin during testing."},
            format="json",
        )
        assert resp.status_code == 200
        transaction.refresh_from_db()
        assert transaction.is_resolved
        assert transaction.resolution_notes == "Resolved by admin during testing."
        assert AuditLog.objects.filter(action="transaction.resolve").exists()


@pytest.mark.django_db
class TestAuditLog:
    def test_audit_log_no_delete_permission(self):
        # AuditLog default_permissions = ("add", "view") — no "delete"
        perms = AuditLog._meta.default_permissions
        assert "delete" not in perms
        assert "change" not in perms

    def test_audit_log_list(self, staff_client):
        AuditLog.objects.create(
            actor_label="test@etip.test",
            action="test.action",
            target_type="Test",
            target_id="123",
        )
        resp = staff_client.get(reverse("admin-audit-logs"))
        assert resp.status_code == 200


class TestAuditLogMiddleware:
    def test_middleware_attaches_ip(self):
        factory = RequestFactory()
        request = factory.get("/test/")
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        def get_response(req):
            return None

        middleware = AuditLogMiddleware(get_response)
        middleware(request)
        assert request.audit_ip == "192.168.1.100"

    def test_middleware_x_forwarded_for(self):
        factory = RequestFactory()
        request = factory.get("/test/")
        request.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.1, 192.168.1.1"

        def get_response(req):
            return None

        middleware = AuditLogMiddleware(get_response)
        middleware(request)
        assert request.audit_ip == "10.0.0.1"
