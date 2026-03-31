"""
ETIP Backend — Root URL Configuration
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Health check for Render
    path("health", lambda r: JsonResponse({"status": "ok"})),

    # Django admin (internal)
    path("django-admin/", admin.site.urls),

    # API v1
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/meters/", include("apps.meters.urls")),
    path("api/v1/transactions/", include("apps.transactions.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/webhooks/", include("apps.payments.webhook_urls")),
    path("api/v1/admin/", include("apps.admin_panel.urls")),
    path("api/v1/chat/", include("apps.chat.urls")),

    # API documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
