"""
transactions — URL configuration.
"""
from django.urls import path

from .views import MyTokensView, TokenResendView, TransactionDetailView, TransactionListView

urlpatterns = [
    path("", TransactionListView.as_view(), name="transaction-list"),
    path("my-tokens/", MyTokensView.as_view(), name="my-tokens"),
    path("<uuid:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
    path(
        "<uuid:pk>/resend-token/",
        TokenResendView.as_view(),
        name="transaction-resend-token",
    ),
]
