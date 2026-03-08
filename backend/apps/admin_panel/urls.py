"""
admin_panel — Admin/operator dashboard API routes.
"""
from django.urls import path

from .views import (
    AdminMeterDeactivateView,
    AdminMeterListView,
    AdminTransactionDetailView,
    AdminTransactionListView,
    AdminUserCreateView,
    AdminUserListView,
    AuditLogListView,
    CustomerDetailView,
    CustomerListView,
    CustomerSuspendView,
    CustomerTokensView,
    DailyRevenueView,
    DashboardStatsView,
    ResolveTransactionView,
    RetryTokenDeliveryView,
)

urlpatterns = [
    # Dashboard
    path("dashboard/", DashboardStatsView.as_view(), name="admin-dashboard"),
    path("daily-revenue/", DailyRevenueView.as_view(), name="admin-daily-revenue"),

    # Meter management
    path("meters/", AdminMeterListView.as_view(), name="admin-meter-list"),
    path("meters/<uuid:pk>/deactivate/", AdminMeterDeactivateView.as_view(), name="admin-meter-deactivate"),

    # Customer management
    path("users/", CustomerListView.as_view(), name="admin-user-list"),
    path("users/<uuid:pk>/", CustomerDetailView.as_view(), name="admin-user-detail"),
    path("users/<uuid:pk>/suspend/", CustomerSuspendView.as_view(), name="admin-user-suspend"),
    path("users/<uuid:pk>/tokens/", CustomerTokensView.as_view(), name="admin-user-tokens"),

    # Transaction management
    path("transactions/", AdminTransactionListView.as_view(), name="admin-transaction-list"),
    path("transactions/<uuid:pk>/", AdminTransactionDetailView.as_view(), name="admin-transaction-detail"),
    path("transactions/<uuid:pk>/resolve/", ResolveTransactionView.as_view(), name="admin-transaction-resolve"),
    path("transactions/<uuid:pk>/retry-token/", RetryTokenDeliveryView.as_view(), name="admin-transaction-retry-token"),

    # Audit logs
    path("audit-logs/", AuditLogListView.as_view(), name="admin-audit-logs"),

    # Admin account management
    path("admins/", AdminUserListView.as_view(), name="admin-list"),
    path("admins/create/", AdminUserCreateView.as_view(), name="admin-create"),
]
