"""
payments — Customer-facing payment endpoints.
"""
from django.urls import path

from .views import InitiatePaymentView, VerifyPaymentView

urlpatterns = [
    path("initiate/", InitiatePaymentView.as_view(), name="payment-initiate"),
    path("verify/", VerifyPaymentView.as_view(), name="payment-verify"),
]
