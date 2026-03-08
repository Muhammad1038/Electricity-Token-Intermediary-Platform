"""
admin_panel — Views: dashboard stats, user management, transaction management,
audit logs, and admin account management.

All endpoints require AdminUser authentication via a custom permission.
"""
import logging

from django.db.models import Count, Q, Sum
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.transactions.models import PaymentStatus, TokenStatus, Transaction
from apps.meters.models import MeterProfile
from config.pagination import StandardResultsPagination

from .models import AdminRole, AdminUser, AuditLog
from apps.transactions.serializers import TokenRecordSerializer

from .serializers import (
    AdminCreateSerializer,
    AdminLoginSerializer,
    AdminMeterListSerializer,
    AdminProfileSerializer,
    AdminTransactionDetailSerializer,
    AdminTransactionListSerializer,
    AuditLogSerializer,
    CustomerEditSerializer,
    CustomerListSerializer,
    CustomerSuspendSerializer,
    DashboardStatsSerializer,
    ResolveTransactionSerializer,
)

logger = logging.getLogger(__name__)


# ── Permission helper ─────────────────────────────────────────────────────────


def _is_admin(request):
    """Check the requesting user has is_staff=True (Django superuser or staff)."""
    return request.user and request.user.is_authenticated and request.user.is_staff


def _admin_required(request):
    """Return error Response if not admin, else None."""
    if not _is_admin(request):
        return Response(
            {"status": "error", "message": "Admin access required."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


def _log_action(request, action, target_type="", target_id="", metadata=None):
    """Create an audit log entry."""
    AuditLog.objects.create(
        user_actor=request.user if request.user.is_authenticated else None,
        actor_label=str(request.user) if request.user.is_authenticated else "anonymous",
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        metadata=metadata or {},
        ip_address=getattr(request, "audit_ip", request.META.get("REMOTE_ADDR")),
    )


# ── Dashboard ─────────────────────────────────────────────────────────────────


class DashboardStatsView(APIView):
    """
    GET /api/v1/admin/dashboard/
    Returns summary statistics for the admin dashboard.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["admin"],
        summary="Dashboard statistics",
        description="Returns counts of users, transactions, payment/token statuses, and total revenue.",
        responses={200: DashboardStatsSerializer},
    )
    def get(self, request):
        denied = _admin_required(request)
        if denied:
            return denied

        successful_txns = Transaction.objects.filter(payment_status=PaymentStatus.SUCCESS)
        revenue = successful_txns.aggregate(total=Sum("amount"))["total"] or 0

        stats = {
            "total_users": User.objects.count(),
            "total_transactions": Transaction.objects.count(),
            "pending_payments": Transaction.objects.filter(payment_status=PaymentStatus.PENDING).count(),
            "successful_payments": successful_txns.count(),
            "failed_payments": Transaction.objects.filter(payment_status=PaymentStatus.FAILED).count(),
            "pending_tokens": Transaction.objects.filter(token_status=TokenStatus.PENDING).count(),
            "delivered_tokens": Transaction.objects.filter(token_status=TokenStatus.DELIVERED).count(),
            "failed_tokens": Transaction.objects.filter(token_status=TokenStatus.FAILED).count(),
            "total_revenue": revenue,
        }
        return Response({"status": "success", "data": stats})


class DailyRevenueView(APIView):
    """
    GET /api/v1/admin/daily-revenue/
    Returns last 30 days of daily revenue + transaction count (successful only).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        denied = _admin_required(request)
        if denied:
            return denied

        from django.db.models.functions import TruncDate
        import datetime

        since = timezone.now().date() - datetime.timedelta(days=29)
        rows = (
            Transaction.objects
            .filter(payment_status=PaymentStatus.SUCCESS, created_at__date__gte=since)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(revenue=Sum("amount"), count=Count("id"))
            .order_by("day")
        )
        # Fill in zeros for missing days
        data_map = {r["day"]: r for r in rows}
        result = []
        for i in range(30):
            day = since + datetime.timedelta(days=i)
            row = data_map.get(day)
            result.append({
                "date": day.strftime("%b %d"),
                "revenue": float(row["revenue"]) if row else 0,
                "count": row["count"] if row else 0,
            })
        return Response({"status": "success", "data": result})


# ── Customer management ──────────────────────────────────────────────────────

class AdminMeterListView(APIView):
    """
    GET /api/v1/admin/meters/
    Lists all meter profiles across all users. Admin only.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        denied = _admin_required(request)
        if denied:
            return denied

        qs = (
            MeterProfile.objects
            .select_related("user")
            .order_by("-created_at")
        )

        search = request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(meter_number__icontains=search)
                | Q(user__email__icontains=search)
                | Q(meter_owner_name__icontains=search)
                | Q(disco__icontains=search)
            )

        active_only = request.query_params.get("active", "")
        if active_only == "1":
            qs = qs.filter(is_active=True)

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(qs, request)
        data = [
            {
                "id": str(m.id),
                "meter_number": m.meter_number,
                "disco": m.disco,
                "disco_display": m.get_disco_display(),
                "nickname": m.nickname,
                "meter_owner_name": m.meter_owner_name or "",
                "meter_type": m.meter_type,
                "is_active": m.is_active,
                "is_default": m.is_default,
                "user_email": m.user.email,
                "user_name": m.user.full_name or "",
                "created_at": m.created_at.isoformat(),
            }
            for m in page
        ]
        return paginator.get_paginated_response(data)


class AdminMeterDeactivateView(APIView):
    """
    POST /api/v1/admin/meters/<uuid:pk>/deactivate/
    Soft-deactivates a meter. Admin only.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        denied = _admin_required(request)
        if denied:
            return denied

        try:
            meter = MeterProfile.objects.get(id=pk)
        except MeterProfile.DoesNotExist:
            return Response({"status": "error", "message": "Meter not found."}, status=status.HTTP_404_NOT_FOUND)

        meter.is_active = False
        meter.save(update_fields=["is_active"])
        _log_action(request, "meter.deactivate", "MeterProfile", pk, {"meter_number": meter.meter_number})
        return Response({"status": "success", "message": "Meter deactivated."})

class CustomerListView(APIView):
    """
    GET /api/v1/admin/users/
    Lists all customer accounts with transaction count.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["admin"],
        summary="List customers",
        description="Lists all consumer accounts with transaction counts. Admin only.",
        responses={200: CustomerListSerializer(many=True)},
    )
    def get(self, request):
        denied = _admin_required(request)
        if denied:
            return denied

        queryset = (
            User.objects
            .annotate(transaction_count=Count("transactions"))
            .order_by("-created_at")
        )

        # Optional search by phone or name
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | Q(full_name__icontains=search)
            )

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = CustomerListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class CustomerDetailView(APIView):
    """
    GET   /api/v1/admin/users/<uuid:pk>/  — single customer profile
    PATCH /api/v1/admin/users/<uuid:pk>/  — edit customer details
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["admin"],
        summary="Customer detail",
        responses={200: CustomerListSerializer},
    )
    def get(self, request, pk):
        denied = _admin_required(request)
        if denied:
            return denied

        try:
            user = User.objects.annotate(
                transaction_count=Count("transactions")
            ).get(id=pk)
        except User.DoesNotExist:
            return Response(
                {"status": "error", "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CustomerListSerializer(user)
        return Response({"status": "success", "data": serializer.data})

    @extend_schema(
        tags=["admin"],
        summary="Edit customer details",
        description="Partial update — send only the fields you want to change (full_name, email, is_active).",
        request=CustomerEditSerializer,
        responses={
            200: CustomerListSerializer,
            404: OpenApiResponse(description="User not found"),
        },
    )
    def patch(self, request, pk):
        denied = _admin_required(request)
        if denied:
            return denied

        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response(
                {"status": "error", "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CustomerEditSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        _log_action(
            request, "user.edit",
            target_type="User", target_id=user.id,
            metadata={"changed_fields": list(serializer.validated_data.keys())},
        )

        # Re-annotate for response
        user = User.objects.annotate(
            transaction_count=Count("transactions")
        ).get(id=pk)
        return Response({"status": "success", "data": CustomerListSerializer(user).data})


class CustomerSuspendView(APIView):
    """
    POST /api/v1/admin/users/<uuid:pk>/suspend/
    Toggle suspend/reactivate a customer account.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["admin"],
        summary="Suspend / reactivate customer",
        description="Toggles is_active on the customer account. Logs the action.",
        request=CustomerSuspendSerializer,
        responses={
            200: OpenApiResponse(description="Account status toggled"),
            404: OpenApiResponse(description="User not found"),
        },
    )
    def post(self, request, pk):
        denied = _admin_required(request)
        if denied:
            return denied

        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response(
                {"status": "error", "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CustomerSuspendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Use explicit suspend boolean instead of blind toggle
        should_suspend = serializer.validated_data["suspend"]
        user.is_active = not should_suspend
        user.save(update_fields=["is_active"])

        action = "user.suspend" if not user.is_active else "user.reactivate"
        _log_action(
            request, action,
            target_type="User", target_id=user.id,
            metadata={"reason": serializer.validated_data.get("reason", "")},
        )

        status_label = "suspended" if not user.is_active else "reactivated"
        return Response({
            "status": "success",
            "message": f"Account {status_label}.",
            "data": {"is_active": user.is_active},
        })


class CustomerTokensView(APIView):
    """
    GET /api/v1/admin/users/<uuid:pk>/tokens/
    Returns all delivered electricity tokens for a specific user.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["admin"],
        summary="User's token records",
        description="Returns all delivered tokens for a specific customer. Admin only.",
        responses={200: TokenRecordSerializer(many=True)},
    )
    def get(self, request, pk):
        denied = _admin_required(request)
        if denied:
            return denied

        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response(
                {"status": "error", "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        queryset = (
            Transaction.objects
            .filter(
                user=user,
                payment_status=PaymentStatus.SUCCESS,
                token_status__in=[TokenStatus.DELIVERED, TokenStatus.RESENT],
            )
            .exclude(token_value_encrypted="")
            .order_by("-token_delivered_at")
        )

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = TokenRecordSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# ── Transaction management ───────────────────────────────────────────────────


class AdminTransactionListView(APIView):
    """
    GET /api/v1/admin/transactions/
    Lists all transactions across all users.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["admin"],
        summary="List all transactions",
        description=(
            "Lists all transactions with filters for payment_status, "
            "token_status, disco, and search by reference/meter."
        ),
        responses={200: AdminTransactionListSerializer(many=True)},
    )
    def get(self, request):
        denied = _admin_required(request)
        if denied:
            return denied

        queryset = Transaction.objects.select_related("user").order_by("-created_at")

        # Filter by user
        user_id = request.query_params.get("user_id")
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filters
        payment_status = request.query_params.get("payment_status")
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)

        token_status = request.query_params.get("token_status")
        if token_status:
            queryset = queryset.filter(token_status=token_status)

        disco = request.query_params.get("disco")
        if disco:
            queryset = queryset.filter(disco=disco)

        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(reference__icontains=search)
                | Q(meter_number__icontains=search)
                | Q(meter_owner_name__icontains=search)
            )

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AdminTransactionListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminTransactionDetailView(APIView):
    """
    GET /api/v1/admin/transactions/<uuid:pk>/
    Full transaction detail for admin review.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["admin"],
        summary="Transaction detail (admin)",
        responses={
            200: AdminTransactionDetailSerializer,
            404: OpenApiResponse(description="Transaction not found"),
        },
    )
    def get(self, request, pk):
        denied = _admin_required(request)
        if denied:
            return denied

        try:
            txn = Transaction.objects.select_related("user", "resolved_by").get(id=pk)
        except Transaction.DoesNotExist:
            return Response(
                {"status": "error", "message": "Transaction not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AdminTransactionDetailSerializer(txn)
        return Response({"status": "success", "data": serializer.data})


class ResolveTransactionView(APIView):
    """
    POST /api/v1/admin/transactions/<uuid:pk>/resolve/
    Mark a transaction issue as resolved.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["admin"],
        summary="Resolve transaction",
        description="Mark a problematic transaction as resolved with notes.",
        request=ResolveTransactionSerializer,
        responses={
            200: OpenApiResponse(description="Transaction resolved"),
            404: OpenApiResponse(description="Transaction not found"),
        },
    )
    def post(self, request, pk):
        denied = _admin_required(request)
        if denied:
            return denied

        try:
            txn = Transaction.objects.get(id=pk)
        except Transaction.DoesNotExist:
            return Response(
                {"status": "error", "message": "Transaction not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ResolveTransactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        txn.is_resolved = True
        txn.resolution_notes = serializer.validated_data["resolution_notes"]
        txn.resolved_by = request.user
        txn.resolved_at = timezone.now()
        txn.save(update_fields=[
            "is_resolved", "resolution_notes", "resolved_by", "resolved_at", "updated_at",
        ])

        _log_action(
            request, "transaction.resolve",
            target_type="Transaction", target_id=txn.id,
            metadata={"reference": txn.reference, "notes": txn.resolution_notes},
        )

        return Response({
            "status": "success",
            "message": f"Transaction {txn.reference} marked as resolved.",
        })


class RetryTokenDeliveryView(APIView):
    """
    POST /api/v1/admin/transactions/<uuid:pk>/retry-token/
    Re-dispatch token delivery for a paid transaction with failed token.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["admin"],
        summary="Retry token delivery",
        description=(
            "Re-dispatches the DISCO token delivery task for a transaction "
            "where payment succeeded but token delivery failed."
        ),
        responses={
            200: OpenApiResponse(description="Token delivery retried"),
            400: OpenApiResponse(description="Transaction not eligible for retry"),
            404: OpenApiResponse(description="Transaction not found"),
        },
    )
    def post(self, request, pk):
        denied = _admin_required(request)
        if denied:
            return denied

        try:
            txn = Transaction.objects.get(id=pk)
        except Transaction.DoesNotExist:
            return Response(
                {"status": "error", "message": "Transaction not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if txn.payment_status != PaymentStatus.SUCCESS:
            return Response(
                {"status": "error", "message": "Only paid transactions can have token delivery retried."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if txn.token_status not in (TokenStatus.FAILED, TokenStatus.PENDING):
            return Response(
                {"status": "error", "message": f"Token status is {txn.token_status} — not eligible for retry."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.transactions.tasks import request_disco_token_task
        request_disco_token_task.delay(str(txn.id))

        _log_action(
            request, "transaction.retry_token",
            target_type="Transaction", target_id=txn.id,
            metadata={"reference": txn.reference, "previous_token_status": txn.token_status},
        )

        return Response({
            "status": "success",
            "message": f"Token delivery retried for {txn.reference}.",
        })


# ── Audit logs ────────────────────────────────────────────────────────────────


class AuditLogListView(APIView):
    """
    GET /api/v1/admin/audit-logs/
    Paginated, filterable audit trail.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["admin"],
        summary="Audit logs",
        description="View the immutable audit trail. Filter by action or search by actor.",
        responses={200: AuditLogSerializer(many=True)},
    )
    def get(self, request):
        denied = _admin_required(request)
        if denied:
            return denied

        queryset = AuditLog.objects.order_by("-timestamp")

        action = request.query_params.get("action")
        if action:
            queryset = queryset.filter(action=action)

        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(actor_label__icontains=search)
                | Q(target_type__icontains=search)
                | Q(target_id__icontains=search)
            )

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AuditLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# ── Admin account management (SUPER_ADMIN only in practice) ───────────────────


class AdminUserListView(APIView):
    """
    GET /api/v1/admin/admins/
    List admin/operator accounts.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["admin"],
        summary="List admin accounts",
        responses={200: AdminProfileSerializer(many=True)},
    )
    def get(self, request):
        denied = _admin_required(request)
        if denied:
            return denied

        admins = AdminUser.objects.order_by("-created_at")
        serializer = AdminProfileSerializer(admins, many=True)
        return Response({"status": "success", "data": serializer.data})


class AdminUserCreateView(APIView):
    """
    POST /api/v1/admin/admins/
    Create a new operator account (staff only).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["admin"],
        summary="Create admin account",
        request=AdminCreateSerializer,
        responses={
            201: AdminProfileSerializer,
            403: OpenApiResponse(description="Not authorized"),
        },
    )
    def post(self, request):
        denied = _admin_required(request)
        if denied:
            return denied

        serializer = AdminCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin = serializer.save()

        _log_action(
            request, "admin.create",
            target_type="AdminUser", target_id=admin.id,
            metadata={"email": admin.email, "role": admin.role},
        )

        return Response(
            {"status": "success", "data": AdminProfileSerializer(admin).data},
            status=status.HTTP_201_CREATED,
        )
