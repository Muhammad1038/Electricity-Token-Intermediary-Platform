"""
accounts — URL patterns
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    OTPResendView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
    UserProfileView,
    VerifyOTPAndCreateUserView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("verify-otp/", VerifyOTPAndCreateUserView.as_view(), name="auth-verify-otp"),
    path("resend-otp/", OTPResendView.as_view(), name="auth-resend-otp"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="auth-password-reset-confirm"),
    path("change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("profile/", UserProfileView.as_view(), name="auth-profile"),
]
