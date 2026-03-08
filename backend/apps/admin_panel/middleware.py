"""
admin_panel — Audit log middleware.
Attaches request metadata so AuditLog entries can include IP + user agent.
"""
import logging

logger = logging.getLogger(__name__)


class AuditLogMiddleware:
    """
    Stores request IP and user agent on the request object
    so views and services can attach them to AuditLog entries.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.audit_ip = self._get_client_ip(request)
        request.audit_ua = request.META.get("HTTP_USER_AGENT", "")
        response = self.get_response(request)
        return response

    @staticmethod
    def _get_client_ip(request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
