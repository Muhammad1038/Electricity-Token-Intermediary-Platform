"""
ETIP Backend — Test Settings
Uses SQLite for speed; disables caching and async tasks.
"""
from .base import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Use synchronous task execution during tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable caching in tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Fast password hashing for tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Suppress logging noise in tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"]},
}

# Dummy keys for tests
PAYSTACK_SECRET_KEY = "sk_test_dummy"
FLUTTERWAVE_SECRET_KEY = "FLWSECK_TEST-dummy"
TOKEN_ENCRYPTION_KEY = "3VXCEJhMhMMlYg_NHsqAuMX3_qI8fGUfQwNJOK0GVNk="
