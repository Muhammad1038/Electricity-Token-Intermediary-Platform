"""
ETIP Backend — Base Settings
Shared across all environments.
"""

import os
from datetime import timedelta
from pathlib import Path

import environ

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # /backend

# ── Environment ───────────────────────────────────────────────────────────────
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# ── Core ──────────────────────────────────────────────────────────────────────
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost"])

# ── Applications ──────────────────────────────────────────────────────────────
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "django_celery_beat",
    "django_celery_results",
    "django_otp",
    "django_otp.plugins.otp_totp",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.meters",
    "apps.transactions",
    "apps.payments",
    "apps.notifications",
    "apps.admin_panel",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ── Middleware ─────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.admin_panel.middleware.AuditLogMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ── Database ──────────────────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="etip_db"),
        "USER": env("DB_USER", default="etip_user"),
        "PASSWORD": env("DB_PASSWORD", default="etip_password"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
        "OPTIONS": {
            "connect_timeout": 10,
        },
        "CONN_MAX_AGE": 60,
    }
}

# ── Custom User Model ──────────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.User"

# ── Password Validation ────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Internationalization ───────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

# ── Static & Media ─────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Django REST Framework ──────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "config.pagination.StandardResultsPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "config.exceptions.custom_exception_handler",
}

# ── JWT Settings ───────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env.int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=15)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=30)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "TOKEN_OBTAIN_SERIALIZER": "apps.accounts.serializers.CustomTokenObtainPairSerializer",
}

# ── Redis & Caching ────────────────────────────────────────────────────────────
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "TIMEOUT": 300,  # 5 minutes default
    }
}

# ── Celery ─────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/2")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Africa/Lagos"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes max per task
CELERY_TASK_SOFT_TIME_LIMIT = 240

# ── API Documentation (drf-spectacular) ───────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "ETIP API",
    "DESCRIPTION": """
## Electricity Token Intermediary Platform — REST API

### How to get a Bearer token and test protected endpoints

1. Find **POST /api/v1/auth/login/** below — it is already expanded and ready.
2. Click **Try it out** (button on the right of the endpoint row).
3. Fill in the **Request body** that appears:
   ```json
   {\n     \"phone_number\": \"08140628953\",\n     \"password\": \"Admin1234!\"\n   }
   ```
4. Click **Execute**. Copy the `access` value from the response JSON.
5. Click the **Authorize 🔒** button at the top of this page.
6. In the **BearerAuth** row, paste exactly: `Bearer <paste_access_token_here>`
7. Click **Authorize** → **Close**. All padlocks turn solid — you are authenticated.

> Tokens expire in **15 minutes**. Repeat steps 2–7 with a fresh token when needed.
    """,
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True,
        "defaultModelsExpandDepth": 2,
        "defaultModelExpandDepth": 2,
    },
    "TAGS": [
        {"name": "auth", "description": "Register, verify OTP, login, logout, password reset, profile"},
        {"name": "meters", "description": "Saved meter profiles (CRUD) + real-time DISCO validation"},
    ],
    "SECURITY": [{"BearerAuth": []}],
    "SCHEMA_PATH_PREFIX": "/api/v1",
}

# ── CORS ───────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:3000", "http://localhost:3001"],
)
CORS_ALLOW_CREDENTIALS = True

# ── Security Headers ───────────────────────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True

# ── Email (SMTP) — OTP delivery ───────────────────────────────────────────────
# OTP codes are emailed directly via Django SMTP.
# Gmail: enable 2FA → Google Account → Security → App Passwords → create one.
# The 16-char App Password goes in EMAIL_HOST_PASSWORD (NOT your Gmail password).
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST          = env("EMAIL_HOST",          default="smtp.gmail.com")
EMAIL_PORT          = env.int("EMAIL_PORT",      default=587)
EMAIL_USE_TLS       = env.bool("EMAIL_USE_TLS",  default=True)
EMAIL_HOST_USER     = env("EMAIL_HOST_USER",     default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL  = env("DEFAULT_FROM_EMAIL",  default="ETIP <noreply@etip.ng>")

# ── Application-Specific Settings ─────────────────────────────────────────────
# OTP
OTP_EXPIRY_SECONDS = 300          # 5 minutes
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_LENGTH = 6

# Meter
METER_VALIDATION_CACHE_SECONDS = 1800   # 30 minutes
METER_VALIDATION_TIMEOUT_SECONDS = 5
METER_VALIDATION_MAX_RETRIES = 3
MAX_METER_PROFILES_PER_USER = 5

# Token purchase
MIN_PURCHASE_AMOUNT = 500          # Naira
MAX_PURCHASE_AMOUNT = 100_000      # Naira

# DISCO token delivery
# VTPass live API responds in 1-3s; 15s is ample headroom
DISCO_REQUEST_TIMEOUT_SECONDS = 15
DISCO_RETRY_DELAYS = [3, 6]        # 2 retries — token purchase is critical, brief retry is fine
DISCO_MAX_RETRIES = 2

# Meter validation
METER_VALIDATION_TIMEOUT_SECONDS = 10   # VTPass live ~1-3s; 10s is generous
METER_VALIDATION_MAX_RETRIES = 2        # 2 attempts — fast live API, retry once on transient error

# Payment
PAYMENT_SESSION_EXPIRY_MINUTES = 10

# Encryption key (Fernet) for token values
TOKEN_ENCRYPTION_KEY = env("TOKEN_ENCRYPTION_KEY", default="")

# Payment gateways
PAYSTACK_SECRET_KEY = env("PAYSTACK_SECRET_KEY", default="")
PAYSTACK_PUBLIC_KEY = env("PAYSTACK_PUBLIC_KEY", default="")
PAYSTACK_BASE_URL = env("PAYSTACK_BASE_URL", default="https://api.paystack.co")

FLUTTERWAVE_SECRET_KEY = env("FLUTTERWAVE_SECRET_KEY", default="")
FLUTTERWAVE_PUBLIC_KEY = env("FLUTTERWAVE_PUBLIC_KEY", default="")
FLUTTERWAVE_BASE_URL = env("FLUTTERWAVE_BASE_URL", default="https://api.flutterwave.com/v3")
FLUTTERWAVE_HASH = env("FLUTTERWAVE_HASH", default="")

# ── VTPass (unified DISCO gateway) ───────────────────────────────────────────
# GET  requests use: api-key + public-key headers
# POST requests use: api-key + secret-key headers
# Register at: https://www.vtpass.com/register
# Sandbox:     https://sandbox.vtpass.com/register
# Keys:        /account → API Keys tab
VTPASS_API_KEY    = env("VTPASS_API_KEY",    default="")
VTPASS_PUBLIC_KEY = env("VTPASS_PUBLIC_KEY", default="")
VTPASS_SECRET_KEY = env("VTPASS_SECRET_KEY", default="")
VTPASS_BASE_URL   = env("VTPASS_BASE_URL",   default="https://sandbox.vtpass.com/api")

# DISCO registry — keyed by DISCOProvider code.
# 'vtpass_service_id' maps to the serviceID field in every VTPass electricity request.
# 'states' is documentation-only (human reference, not used in code).
DISCO_APIS = {
    # ── South-West ────────────────────────────────────────────────────────────
    "IBEDC": {
        "vtpass_service_id": "ibadan-electric",
        "name": "Ibadan Electricity Distribution Company",
        "states": ["Oyo", "Ogun", "Ondo", "Osun", "Kwara"],
    },
    "EKEDC": {
        "vtpass_service_id": "eko-electric",
        "name": "Eko Electricity Distribution Company",
        "states": ["Lagos Island", "Badagry", "Epe"],
    },
    "IKEDC": {
        "vtpass_service_id": "ikeja-electric",
        "name": "Ikeja Electric",
        "states": ["Lagos Mainland", "Ikeja", "Ikorodu"],
    },
    # ── South-South ───────────────────────────────────────────────────────────
    "PHED": {
        "vtpass_service_id": "phed",
        "name": "Port Harcourt Electricity Distribution Company",
        "states": ["Rivers", "Bayelsa", "Akwa Ibom", "Cross River"],
    },
    "BEDC": {
        "vtpass_service_id": "benin-electric",
        "name": "Benin Electricity Distribution Company",
        "states": ["Edo", "Delta", "Ekiti", "Ondo"],
    },
    # ── South-East ────────────────────────────────────────────────────────────
    "EEDC": {
        "vtpass_service_id": "enugu-electric",
        "name": "Enugu Electricity Distribution Company",
        "states": ["Enugu", "Anambra", "Imo", "Abia", "Ebonyi"],
    },
    "ABA": {
        "vtpass_service_id": "aba-electric",
        "name": "Aba Electricity Distribution Company",
        "states": ["Abia (Aba zone)"],
    },
    # ── North-Central ─────────────────────────────────────────────────────────
    "AEDC": {
        "vtpass_service_id": "abuja-electric",
        "name": "Abuja Electricity Distribution Company",
        "states": ["FCT", "Kogi", "Niger", "Nassarawa"],
    },
    "JED": {
        "vtpass_service_id": "jos-electric",
        "name": "Jos Electricity Distribution Company",
        "states": ["Plateau", "Benue", "Gombe", "Bauchi"],
    },
    # ── North-West ────────────────────────────────────────────────────────────
    "KAEDCO": {
        "vtpass_service_id": "kaduna-electric",
        "name": "Kaduna Electric",
        "states": ["Kaduna", "Kebbi", "Sokoto", "Zamfara"],
    },
    "KEDCO": {
        "vtpass_service_id": "kano-electric",
        "name": "Kano Electricity Distribution Company",
        "states": ["Kano", "Jigawa", "Katsina"],
    },
    # ── North-East ────────────────────────────────────────────────────────────
    "YEDC": {
        "vtpass_service_id": "yola-electric",
        "name": "Yola Electricity Distribution Company",
        "states": ["Adamawa", "Taraba"],
    },
}

# ── Twilio ─────────────────────────────────────────────────────────────────────
# Register at: https://www.twilio.com/try-twilio
# ── Twilio ───────────────────────────────────────────────────────────────────
# Register at: https://www.twilio.com/try-twilio
# Console:     https://www.twilio.com/console
# Verify docs: https://www.twilio.com/docs/verify/api
#
# IMPORTANT — when creating the Verify Service in Twilio Console:
#   • Set channel to SMS (not email, not WhatsApp, not voice)
#   • Code length: 6
#   • All code sends from backend use channel="sms" hardcoded
#
# IMPORTANT — phone number format:
#   • Numbers are stored in DB as Nigerian local format: 08140628953
#   • _to_e164_nigeria() in accounts/services.py auto-converts to +2348140628953
#     before every Twilio API call — you do NOT need to store E.164 in the DB.
#
# TWILIO_ACCOUNT_SID   — from twilio.com/console (starts with AC)
# TWILIO_AUTH_TOKEN    — from twilio.com/console
# TWILIO_VERIFY_SERVICE_SID — from console.twilio.com/verify/services (starts with VA)
# TWILIO_PHONE_NUMBER  — your Twilio SMS sender number in E.164, e.g. +14155552671
#                        (buy one at console.twilio.com/phone-numbers)
TWILIO_ACCOUNT_SID        = env("TWILIO_ACCOUNT_SID",        default="")
TWILIO_AUTH_TOKEN         = env("TWILIO_AUTH_TOKEN",         default="")
TWILIO_VERIFY_SERVICE_SID = env("TWILIO_VERIFY_SERVICE_SID", default="")
TWILIO_PHONE_NUMBER       = env("TWILIO_PHONE_NUMBER",       default="")

# Firebase
FIREBASE_CREDENTIALS_PATH = env(
    "FIREBASE_CREDENTIALS_PATH", default="config/firebase_credentials.json"
)

# Frontend
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")
ADMIN_FRONTEND_URL = env("ADMIN_FRONTEND_URL", default="http://localhost:3001")
