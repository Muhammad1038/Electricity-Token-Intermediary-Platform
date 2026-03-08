"""
accounts — API Views (Auth endpoints)
"""
import logging

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import OTPVerification, User
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    OTPResendSerializer,
    OTPVerifySerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)
from .services import (
    confirm_password_reset,
    create_and_send_otp,
    initiate_password_reset,
    register_user,
    resend_otp,
    verify_otp,
)

logger = logging.getLogger(__name__)

# ── Shared inline response schemas ────────────────────────────────────────────

_JWT_RESPONSE = inline_serializer(
    name="JWTResponse",
    fields={
        "status": drf_serializers.CharField(default="success"),
        "message": drf_serializers.CharField(),
        "data": inline_serializer(
            name="JWTData",
            fields={
                "access": drf_serializers.CharField(help_text="JWT access token (15 min)"),
                "refresh": drf_serializers.CharField(help_text="JWT refresh token (30 days)"),
                "user": UserProfileSerializer(),
            },
        ),
    },
)

_SUCCESS_MSG = inline_serializer(
    name="SuccessMessage",
    fields={
        "status": drf_serializers.CharField(default="success"),
        "message": drf_serializers.CharField(),
    },
)


class RegisterView(APIView):
    """
    POST /api/v1/auth/register/
    Step 1: Submit email → OTP sent to email + WhatsApp (if provided).
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        summary="Step 1 — Register (send OTP)",
        description=(
            "Submit an email address (and optionally a Nigerian WhatsApp number). "
            "A 6-digit OTP is sent via email. If a WhatsApp number is provided, "
            "the same OTP is also delivered there. Call **verify-otp** next."
        ),
        request=UserRegistrationSerializer,
        responses={
            200: OpenApiResponse(
                response=_SUCCESS_MSG,
                description="OTP sent — proceed to /verify-otp/",
                examples=[OpenApiExample(
                    "Success",
                    value={"status": "success", "message": "OTP sent to john@example.com.", "data": {"email": "john@example.com"}},
                )],
            ),
            400: OpenApiResponse(description="Invalid email or already registered"),
        },
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        whatsapp_number = serializer.validated_data.get("whatsapp_number", "")

        create_and_send_otp(email, OTPVerification.Purpose.REGISTRATION, whatsapp_number)

        return Response(
            {
                "status": "success",
                "message": f"OTP sent to {email}. Enter it to complete registration.",
                "data": {"email": email},
            },
            status=status.HTTP_200_OK,
        )


class VerifyOTPAndCreateUserView(APIView):
    """
    POST /api/v1/auth/verify-otp/
    Step 2: Verify OTP → account created → JWT issued.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        summary="Step 2 — Verify OTP & create account",
        description="Verify the 6-digit OTP sent to your email. On success the account is created and JWT tokens are returned.",
        request=OTPVerifySerializer,
        responses={
            201: OpenApiResponse(response=_JWT_RESPONSE, description="Account created + JWT tokens issued"),
            400: OpenApiResponse(description="Wrong OTP, expired OTP, or weak password"),
            409: OpenApiResponse(description="Account already exists"),
        },
    )
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        email = data["email"]
        otp_code = data["otp_code"]
        password = data["password"]
        full_name = data.get("full_name", "")
        whatsapp_number = data.get("whatsapp_number", "")

        try:
            verify_otp(email, otp_code, OTPVerification.Purpose.REGISTRATION)
        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"status": "error", "message": "Account already exists. Please log in."},
                status=status.HTTP_409_CONFLICT,
            )

        user = register_user(email, password, full_name, whatsapp_number)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "status": "success",
                "message": "Account created successfully.",
                "data": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": UserProfileSerializer(user).data,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class OTPResendView(APIView):
    """
    POST /api/v1/auth/resend-otp/
    Resend OTP (60 second cooldown enforced).
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        summary="Resend OTP",
        description="Re-sends the OTP to the registered email (and WhatsApp if available). A 60-second cooldown is enforced between requests.",
        request=OTPResendSerializer,
        responses={
            200: OpenApiResponse(response=_SUCCESS_MSG, description="OTP resent"),
            429: OpenApiResponse(description="Cooldown not elapsed yet"),
        },
    )
    def post(self, request):
        serializer = OTPResendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        purpose = serializer.validated_data["purpose"]

        # Fetch whatsapp_number from existing user record if they have one
        whatsapp_number = ""
        try:
            whatsapp_number = User.objects.get(email=email).whatsapp_number or ""
        except User.DoesNotExist:
            pass

        try:
            resend_otp(email, purpose, whatsapp_number)
        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        return Response(
            {"status": "success", "message": "OTP resent successfully.", "data": {"email": email}},
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    """
    POST /api/v1/auth/login/
    Returns JWT access + refresh tokens.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        summary="Login — get JWT tokens",
        description=(
            "Authenticate with email and password.\n\n"
            "**After a successful response:**\n"
            "1. Copy the `access` value from the response.\n"
            "2. Click the **Authorize 🔒** button at the top of this page.\n"
            "3. Enter: `Bearer <paste_access_token_here>` and click Authorize."
        ),
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                response=_JWT_RESPONSE,
                description="Login successful — copy the `access` token",
                examples=[OpenApiExample(
                    "Success",
                    value={
                        "status": "success",
                        "message": "Login successful.",
                        "data": {
                            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "user": {"id": "uuid", "email": "john@example.com", "full_name": "", "is_verified": True},
                        },
                    },
                )],
            ),
            401: OpenApiResponse(description="Invalid email or password"),
            403: OpenApiResponse(description="Account suspended"),
            423: OpenApiResponse(description="Account locked — too many failed attempts"),
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"status": "error", "message": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"status": "error", "message": "This account has been suspended."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if user.is_locked:
            return Response(
                {"status": "error", "message": "Account temporarily locked. Try again in 15 minutes."},
                status=status.HTTP_423_LOCKED,
            )

        if not user.check_password(password):
            user.increment_failed_login()
            return Response(
                {"status": "error", "message": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user.reset_failed_login()

        refresh = RefreshToken.for_user(user)
        logger.info("User login", extra={"user_id": str(user.id)})

        return Response(
            {
                "status": "success",
                "message": "Login successful.",
                "data": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": UserProfileSerializer(user).data,
                },
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Blacklists the provided refresh token.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["auth"],
        summary="Logout",
        description="Blacklists the refresh token so it can no longer be used. Requires Bearer token in Authorize.",
        request=inline_serializer(
            name="LogoutRequest",
            fields={"refresh": drf_serializers.CharField(help_text="The refresh token to invalidate")},
        ),
        responses={
            200: OpenApiResponse(response=_SUCCESS_MSG, description="Logged out"),
            400: OpenApiResponse(description="Missing or already-expired refresh token"),
            401: OpenApiResponse(description="Not authenticated"),
        },
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"status": "error", "message": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"status": "error", "message": "Invalid or already expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"status": "success", "message": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(APIView):
    """
    POST /api/v1/auth/password-reset/
    Sends OTP for password reset.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        summary="Request password reset OTP",
        description="Sends an OTP to the registered email address. Always returns 200 to avoid leaking account existence.",
        request=PasswordResetRequestSerializer,
        responses={200: OpenApiResponse(response=_SUCCESS_MSG, description="OTP sent (if account exists)")},
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        initiate_password_reset(email)

        return Response(
            {
                "status": "success",
                "message": "If an account exists with this email, a reset code has been sent.",
                "data": {},
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """
    POST /api/v1/auth/password-reset/confirm/
    Verify OTP and set new password.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        summary="Confirm password reset",
        description="Verify the OTP and set a new password. Password must have 8+ chars, uppercase, number, special character.",
        request=PasswordResetConfirmSerializer,
        responses={
            200: OpenApiResponse(response=_SUCCESS_MSG, description="Password updated — login with new password"),
            400: OpenApiResponse(description="Wrong or expired OTP, or weak password"),
        },
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        try:
            confirm_password_reset(
                data["email"],
                data["otp_code"],
                data["new_password"],
            )
        except ValueError as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"status": "success", "message": "Password updated successfully. Please log in."},
            status=status.HTTP_200_OK,
        )


class UserProfileView(APIView):
    """
    GET  /api/v1/auth/profile/  — fetch profile
    PATCH /api/v1/auth/profile/ — update full_name / email / fcm_token
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["auth"],
        summary="Get my profile",
        responses={200: OpenApiResponse(response=UserProfileSerializer, description="User profile")},
    )
    def get(self, request):
        return Response(
            {
                "status": "success",
                "data": UserProfileSerializer(request.user).data,
            }
        )

    @extend_schema(
        tags=["auth"],
        summary="Update my profile",
        description="Partial update — send only the fields you want to change (`full_name`, `email`).",
        request=UserProfileSerializer,
        responses={200: OpenApiResponse(response=UserProfileSerializer, description="Updated profile")},
    )
    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"status": "success", "data": serializer.data}
        )


class ChangePasswordView(APIView):
    """
    POST /api/v1/auth/change-password/
    Authenticated password change — requires old_password + new_password.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["auth"],
        summary="Change password",
        description="Change password for the currently authenticated user. Requires old password for verification.",
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(response=_SUCCESS_MSG, description="Password changed"),
            400: OpenApiResponse(description="Wrong old password or weak new password"),
        },
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"status": "error", "message": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])

        return Response(
            {"status": "success", "message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )
