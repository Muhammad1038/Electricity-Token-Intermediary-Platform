"""
transactions — Views: list, detail, and token resend.
"""
import logging

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.pagination import StandardResultsPagination

from .models import Transaction
from .serializers import (
    TokenRecordSerializer,
    TokenResendSerializer,
    TransactionDetailSerializer,
    TransactionListSerializer,
)
from .services import get_transaction_for_user, get_user_tokens, get_user_transactions, resend_token

logger = logging.getLogger(__name__)


class TransactionListView(APIView):
    """
    GET /api/v1/transactions/
    Returns the authenticated customer's transaction history (paginated).
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["transactions"],
        summary="List my transactions",
        description="Returns all transactions for the logged-in user, newest first. Paginated.",
        responses={200: TransactionListSerializer(many=True)},
    )
    def get(self, request):
        queryset = get_user_transactions(request.user)
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = TransactionListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class TransactionDetailView(APIView):
    """
    GET /api/v1/transactions/<uuid:id>/
    Returns full details of a single transaction belonging to the customer.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["transactions"],
        summary="Transaction detail",
        description="Returns full details of a transaction including token delivery status and resend eligibility.",
        responses={
            200: TransactionDetailSerializer,
            404: OpenApiResponse(description="Transaction not found"),
        },
    )
    def get(self, request, pk):
        txn = get_transaction_for_user(request.user, pk)
        if not txn:
            return Response(
                {"status": "error", "message": "Transaction not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TransactionDetailSerializer(txn)
        return Response({"status": "success", "data": serializer.data})


class MyTokensView(APIView):
    """
    GET /api/v1/transactions/my-tokens/
    Returns all delivered electricity tokens for the authenticated user.
    Dedicated endpoint for the "Token Records" screen.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["transactions"],
        summary="My token records",
        description=(
            "Returns all successfully delivered electricity tokens for the logged-in user.\n"
            "Each record includes the decrypted token value, meter number, and delivery date."
        ),
        responses={200: TokenRecordSerializer(many=True)},
    )
    def get(self, request):
        queryset = get_user_tokens(request.user)
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = TokenRecordSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class TokenResendView(APIView):
    """
    POST /api/v1/transactions/<uuid:id>/resend-token/
    Re-request token delivery for a failed or pending transaction.
    Max 3 attempts.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["transactions"],
        summary="Resend token",
        description=(
            "Re-trigger token delivery for a transaction with failed or pending token status.\n\n"
            "**Rules:**\n"
            "- Payment must be confirmed (SUCCESS)\n"
            "- Token status must be FAILED or PENDING\n"
            "- Maximum 3 resend attempts\n"
        ),
        request=None,
        responses={
            200: OpenApiResponse(
                description="Resend initiated",
                examples=[OpenApiExample(
                    "Success",
                    value={"status": "success", "message": "Token resend initiated (attempt 1/3).", "data": {"resend_attempts": 1}},
                )],
            ),
            400: OpenApiResponse(description="Resend not allowed (see error message)"),
            404: OpenApiResponse(description="Transaction not found"),
        },
    )
    def post(self, request, pk):
        txn = get_transaction_for_user(request.user, pk)
        if not txn:
            return Response(
                {"status": "error", "message": "Transaction not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        result = resend_token(txn)

        if not result["success"]:
            return Response(
                {"status": "error", "message": result["error"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "status": "success",
                "message": result["message"],
                "data": {"resend_attempts": result["resend_attempts"]},
            },
            status=status.HTTP_200_OK,
        )
