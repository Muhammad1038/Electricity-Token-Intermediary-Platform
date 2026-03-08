"""
payments — Views: initiate payment, verify payment, and webhook receivers.
"""
import json
import logging

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    InitiatePaymentSerializer,
    PaymentInitiatedResponseSerializer,
    VerifyPaymentSerializer,
)
from .services import (
    handle_paystack_webhook,
    initiate_payment,
    verify_payment,
    verify_paystack_webhook,
)

logger = logging.getLogger(__name__)


class InitiatePaymentView(APIView):
    """
    POST /api/v1/payments/initiate/
    Start a new token purchase — creates a transaction and returns
    the gateway checkout URL.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["payments"],
        summary="Initiate payment",
        description=(
            "Create a new electricity token purchase.\n\n"
            "1. Validates the meter belongs to the authenticated user.\n"
            "2. Creates a PENDING transaction record.\n"
            "3. Initialises payment with the chosen gateway.\n"
            "4. Returns a checkout URL — redirect the customer there.\n"
        ),
        request=InitiatePaymentSerializer,
        responses={
            201: PaymentInitiatedResponseSerializer,
            400: OpenApiResponse(description="Validation error or gateway failure"),
        },
        examples=[
            OpenApiExample(
                "Paystack example",
                value={
                    "meter_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "amount": "5000.00",
                    "payment_gateway": "PAYSTACK",
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip_address = request.META.get("REMOTE_ADDR", "")
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

        try:
            result = initiate_payment(
                user=request.user,
                meter_id=serializer.validated_data["meter_id"],
                amount=serializer.validated_data["amount"],
                payment_gateway=serializer.validated_data["payment_gateway"],
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"status": "success", "data": result},
            status=status.HTTP_201_CREATED,
        )


class VerifyPaymentView(APIView):
    """
    GET /api/v1/payments/verify/?reference=ETIP-XXXX
    Manually verify a payment status with the gateway.
    Called by the frontend after redirect from the hosted checkout page.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["payments"],
        summary="Verify payment",
        description=(
            "After the customer is redirected back from the gateway checkout,\n"
            "the frontend calls this endpoint to confirm payment and trigger\n"
            "token delivery.\n\n"
            "Pass the ETIP transaction reference as a query parameter."
        ),
        parameters=[VerifyPaymentSerializer],
        responses={
            200: OpenApiResponse(
                description="Payment verification result",
                examples=[
                    OpenApiExample(
                        "Verified",
                        value={
                            "status": "success",
                            "data": {
                                "status": "success",
                                "transaction_reference": "ETIP-ABC123DEF456",
                                "message": "Payment verified. Token delivery in progress.",
                            },
                        },
                    )
                ],
            ),
            400: OpenApiResponse(description="Missing reference or verification failed"),
        },
    )
    def get(self, request):
        reference = request.query_params.get("reference", "").strip()
        if not reference:
            return Response(
                {"status": "error", "message": "'reference' query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = verify_payment(reference)
        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error("Unexpected error verifying payment %s: %s", reference, e, exc_info=True)
            return Response(
                {"status": "error", "message": "An unexpected error occurred. Please check your token history."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        http_status = (
            status.HTTP_200_OK if result["status"] == "success"
            else status.HTTP_400_BAD_REQUEST
        )
        return Response({"status": result["status"], "data": result}, status=http_status)


# ━━ Webhooks (unauthenticated — signature-verified) ━━━━━━━━━━━━━━━━━━━━━━━━━━


class PaystackWebhookView(APIView):
    """
    POST /api/v1/webhooks/paystack/
    Receives Paystack webhook events. Verifies HMAC-SHA512 signature.
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # No JWT required

    @extend_schema(
        tags=["webhooks"],
        summary="Paystack webhook",
        description="Receives Paystack webhook events. Signature-verified via X-Paystack-Signature.",
        request=None,
        responses={200: OpenApiResponse(description="Webhook processed")},
    )
    def post(self, request):
        signature = request.META.get("HTTP_X_PAYSTACK_SIGNATURE", "")
        body = request.body

        if not verify_paystack_webhook(body, signature):
            logger.warning("Paystack webhook signature verification failed.")
            return Response(
                {"status": "error", "message": "Invalid signature."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return Response(
                {"status": "error", "message": "Invalid JSON."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = handle_paystack_webhook(payload)
        logger.info("Paystack webhook processed: %s", result)
        return Response({"status": "ok"}, status=status.HTTP_200_OK)



