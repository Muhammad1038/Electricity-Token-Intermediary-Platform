"""
meters — Meter validation via VTPass live electricity API.

VTPass API docs: https://www.vtpass.com/documentation/electricity-payment-api/
  Live base URL: https://vtpass.com/api

Auth for POST requests: api-key + secret-key headers (NOT Basic auth)
Auth for GET  requests: api-key + public-key headers

Verify endpoint:  POST {base_url}/merchant-verify
Purchase endpoint: POST {base_url}/pay

Response code "000" = success. WrongBillersCode=true = invalid meter.
NO sandbox stubs — every meter is validated against the real DISCO via VTPass live.
"""
import logging

import httpx
from django.conf import settings
from django.core.cache import cache
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

CACHE_TTL = getattr(settings, "METER_VALIDATION_CACHE_SECONDS", 1800)  # 30 min
REQUEST_TIMEOUT = getattr(settings, "METER_VALIDATION_TIMEOUT_SECONDS", 10)   # VTPass live ~1-3s
MAX_RETRIES = getattr(settings, "METER_VALIDATION_MAX_RETRIES", 2)             # 2 attempts — brief retry on transient network error


# ── Helpers ───────────────────────────────────────────────────────────────────

def _cache_key(meter_number: str, disco: str) -> str:
    return f"meter_validation:{disco}:{meter_number}"


def _vtpass_service_id(disco: str) -> str:
    """Resolve a DISCO code (e.g. 'AEDC') to its VTPass serviceID (e.g. 'abuja-electric')."""
    disco_apis = getattr(settings, "DISCO_APIS", {})
    return disco_apis.get(disco, {}).get("vtpass_service_id", "")


def _vtpass_post_headers() -> dict:
    """
    Build headers for VTPass POST requests (merchant-verify, pay).
    VTPass POST auth uses api-key + secret-key as separate named headers,
    NOT HTTP Basic auth.
    """
    return {
        "api-key": getattr(settings, "VTPASS_API_KEY", ""),
        "secret-key": getattr(settings, "VTPASS_SECRET_KEY", ""),
        "Content-Type": "application/json",
    }


# ── VTPass meter verify ───────────────────────────────────────────────────────

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    reraise=True,
)
def _call_vtpass_verify(meter_number: str, disco: str, meter_type: str = "prepaid") -> dict:
    """
    POST to VTPass /merchant-verify.
    Retries up to MAX_RETRIES times with exponential backoff (2s → 4s → 8s).

    Returns a normalised dict with:
        is_valid, meter_owner_name, meter_address, meter_type,
        min_purchase_amount, outstanding
    """
    api_key = getattr(settings, "VTPASS_API_KEY", "")
    secret_key = getattr(settings, "VTPASS_SECRET_KEY", "")
    service_id = _vtpass_service_id(disco)

    # Hard fail if VTPass is not configured — no sandbox fallback in production.
    if not api_key or not secret_key:
        raise RuntimeError(
            "VTPass credentials (VTPASS_API_KEY / VTPASS_SECRET_KEY) are not configured."
        )
    if not service_id:
        raise ValueError(
            f"DISCO '{disco}' is not mapped to a VTPass serviceID. Check DISCO_APIS in settings."
        )

    base_url = getattr(settings, "VTPASS_BASE_URL", "https://vtpass.com/api")
    payload = {
        "billersCode": meter_number,
        "serviceID": service_id,
        "type": meter_type.lower(),   # "prepaid" or "postpaid"
    }

    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        response = client.post(
            f"{base_url}/merchant-verify",
            json=payload,
            headers=_vtpass_post_headers(),
        )
        response.raise_for_status()
        data = response.json()

    logger.debug(
        "VTPass /merchant-verify response for %s/%s: code=%s",
        disco, meter_number, data.get("code"),
    )

    # code "000" is the only success code
    if data.get("code") != "000":
        logger.warning(
            "VTPass verify non-success code=%s for %s/%s: %s",
            data.get("code"), disco, meter_number, data,
        )
        return {"is_valid": False}

    content = data.get("content", {})

    # WrongBillersCode=true → meter number does not exist in the DISCO system
    if content.get("WrongBillersCode", False):
        logger.info("VTPass: WrongBillersCode for %s/%s", disco, meter_number)
        return {"is_valid": False}

    # VTPass field names are consistent across all DISCOs for /merchant-verify:
    # Customer_Name, Address, Meter_Type, Min_Purchase_Amount, Outstanding
    customer_name = (
        content.get("Customer_Name")
        or content.get("customer_name")
        or content.get("Name")
        or ""
    ).strip()
    address = (
        content.get("Address")
        or content.get("address")
        or ""
    ).strip()
    meter_type_raw = (
        content.get("Meter_Type")
        or content.get("meter_type")
        or "PREPAID"
    )
    meter_type = meter_type_raw.upper() if meter_type_raw else "PREPAID"

    # Reject meters that return no customer name — they are not real live registrations.
    if not customer_name:
        logger.warning(
            "VTPass returned code 000 but no Customer_Name for %s/%s — treating as invalid.",
            disco, meter_number,
        )
        return {"is_valid": False, "error": "Meter number not registered with this DISCO."}

    return {
        "is_valid": True,
        "meter_owner_name": customer_name,
        "meter_address": address,
        "meter_type": meter_type,
        "min_purchase_amount": content.get("Min_Purchase_Amount", 0),
        "outstanding": content.get("Outstanding", 0),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def validate_meter_with_disco(
    meter_number: str,
    disco: str,
    meter_type: str = "prepaid",
) -> dict:
    """
    Validate a meter number via VTPass.
    Results are cached in Redis for CACHE_TTL seconds (default 30 min).

    Args:
        meter_number: The customer's meter number.
        disco:        DISCO code matching DISCOProvider enum (e.g. "AEDC").
        meter_type:   "prepaid" or "postpaid" (default "prepaid").

    Returns:
        dict — keys: is_valid, meter_owner_name, meter_address, meter_type,
                      min_purchase_amount, outstanding, meter_number, disco
               on failure also: error (human-readable message)
    """
    key = _cache_key(meter_number, disco)

    # 1. Cache hit
    cached = cache.get(key)
    if cached:
        logger.debug("Meter validation cache HIT: %s / %s", disco, meter_number)
        return cached

    # 2. Call VTPass (tenacity handles retries)
    try:
        result = _call_vtpass_verify(meter_number, disco, meter_type)
        result["meter_number"] = meter_number
        result["disco"] = disco

        if result["is_valid"]:
            cache.set(key, result, timeout=CACHE_TTL)
            logger.info(
                "Meter validated and cached: %s / %s → %s",
                disco, meter_number, result.get("meter_owner_name"),
            )
        return result

    except httpx.TimeoutException:
        logger.error("VTPass meter verify timeout for %s / %s", disco, meter_number)
        return {"is_valid": False, "error": "Meter validation service timed out. Please try again."}

    except httpx.HTTPStatusError as exc:
        logger.error(
            "VTPass HTTP error %s for %s / %s",
            exc.response.status_code, disco, meter_number,
        )
        return {"is_valid": False, "error": "Meter validation failed. Please check the meter number."}

    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Unexpected error validating meter %s / %s: %s", disco, meter_number, exc
        )
        return {"is_valid": False, "error": "Meter validation service is temporarily unavailable."}
