"""
ETIP Backend — Custom Exception Handler
Wraps DRF exceptions in a consistent response envelope.
"""
import logging

from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        error_data = response.data

        # Flatten validation errors into a readable list
        if isinstance(error_data, dict):
            errors = {}
            for field, messages in error_data.items():
                if isinstance(messages, list):
                    errors[field] = [str(m) for m in messages]
                else:
                    errors[field] = str(messages)
            detail = errors
        elif isinstance(error_data, list):
            detail = [str(e) for e in error_data]
        else:
            detail = str(error_data)

        response.data = {
            "status": "error",
            "message": _get_error_message(exc, detail),
            "errors": detail,
        }

    else:
        # Unhandled exception — log it
        logger.exception("Unhandled exception in API view", exc_info=exc)

    return response


def _get_error_message(exc, detail):
    """Return a human-readable top-level message."""
    if hasattr(exc, "default_detail"):
        return str(exc.default_detail)
    if isinstance(detail, dict) and "detail" in detail:
        return str(detail["detail"])
    return "An error occurred. Please try again."
