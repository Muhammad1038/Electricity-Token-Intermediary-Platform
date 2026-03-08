"""
ETIP Backend — Development Settings
"""
from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Use real SMTP in development so OTP emails are actually delivered.
# EMAIL_BACKEND is set to smtp.EmailBackend in base.py — do NOT override it here.

# Relaxed CORS for local development
CORS_ALLOW_ALL_ORIGINS = True

# Django Debug Toolbar (optional — install separately if needed)
INTERNAL_IPS = ["127.0.0.1"]

# Logging — verbose in development
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
