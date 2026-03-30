"""
meters — Tests for MeterProfile model, validation, and API views.
"""
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.meters.models import MeterProfile
from conftest import MeterProfileFactory, UserFactory


@pytest.mark.django_db
class TestMeterProfileModel:
    def test_meter_creation(self, user):
        meter = MeterProfileFactory(user=user, is_default=True)
        assert meter.meter_number
        assert meter.disco == "EEDC"
        assert meter.is_default

    def test_default_meter_auto_unset(self, user):
        m1 = MeterProfileFactory(user=user, is_default=True, meter_number="11111111111")
        m2 = MeterProfileFactory(user=user, is_default=False, meter_number="22222222222")

        # Setting m2 as default should unset m1
        m2.is_default = True
        m2.save()
        MeterProfile.objects.filter(
            user=user, is_default=True
        ).exclude(pk=m2.pk).update(is_default=False)

        m1.refresh_from_db()
        assert not m1.is_default


@pytest.mark.django_db
class TestMeterViews:
    def test_list_meters_authenticated(self, auth_client, meter_profile):
        resp = auth_client.get(reverse("meter-profile-list"))
        assert resp.status_code == 200

    def test_list_meters_unauthenticated(self, api_client):
        resp = api_client.get(reverse("meter-profile-list"))
        assert resp.status_code == 401

    @patch("apps.meters.services.validate_meter_with_disco")
    def test_add_meter(self, mock_validate, auth_client, user):
        mock_validate.return_value = {
            "is_valid": True,
            "customer_name": "John Doe",
            "customer_address": "123 Test St",
            "meter_number": "99999999999",
            "disco": "EEDC",
        }
        resp = auth_client.post(
            reverse("meter-profile-list"),
            {"meter_number": "99999999999", "disco": "EEDC"},
            format="json",
        )
        assert resp.status_code == 201
        assert MeterProfile.objects.filter(user=user, meter_number="99999999999").exists()

    @patch("apps.meters.services.validate_meter_with_disco")
    def test_add_duplicate_meter(self, mock_validate, auth_client, meter_profile):
        mock_validate.return_value = {
            "is_valid": True,
            "customer_name": "John Doe",
            "customer_address": "123 Test St",
            "meter_number": meter_profile.meter_number,
            "disco": meter_profile.disco,
        }
        resp = auth_client.post(
            reverse("meter-profile-list"),
            {"meter_number": meter_profile.meter_number, "disco": meter_profile.disco},
            format="json",
        )
        assert resp.status_code == 400

    def test_retrieve_meter(self, auth_client, meter_profile):
        resp = auth_client.get(
            reverse("meter-profile-detail", kwargs={"pk": meter_profile.pk})
        )
        assert resp.status_code == 200

    def test_soft_delete_meter(self, auth_client, meter_profile):
        resp = auth_client.delete(
            reverse("meter-profile-detail", kwargs={"pk": meter_profile.pk})
        )
        assert resp.status_code in (200, 204)
        meter_profile.refresh_from_db()
        assert not meter_profile.is_active

    @patch("apps.meters.views.validate_meter_with_disco")
    def test_validate_endpoint(self, mock_validate, auth_client):
        mock_validate.return_value = {
            "is_valid": True,
            "customer_name": "Test Customer",
            "customer_address": "Test Address",
            "meter_number": "12345678901",
            "disco": "EEDC",
        }
        resp = auth_client.post(
            reverse("meter-validate"),
            {"meter_number": "12345678901", "disco": "EEDC"},
            format="json",
        )
        assert resp.status_code == 200

    def test_validate_endpoint_empty_body(self, auth_client):
        resp = auth_client.post(
            reverse("meter-validate"),
            {},
            format="json",
        )
        assert resp.status_code == 400
