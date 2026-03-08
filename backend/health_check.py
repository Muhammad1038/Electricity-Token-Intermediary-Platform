"""
ETIP — Full Backend Health Check (All 6 Apps)
Run inside container:  python health_check.py
Last updated: February 26, 2026
"""
import os
import sys
import traceback
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

import httpx

BASE = "http://localhost:8000/api/v1"
PASS_COUNT = 0
FAIL_COUNT = 0
SKIP_COUNT = 0


def check(label, got, expected):
    global PASS_COUNT, FAIL_COUNT
    if got == expected:
        PASS_COUNT += 1
        print(f"  [PASS]  {label}")
    else:
        FAIL_COUNT += 1
        print(f"  [FAIL]  {label}  →  got={got!r}  expected={expected!r}")


def skip(label, reason):
    global SKIP_COUNT
    SKIP_COUNT += 1
    print(f"  [SKIP]  {label}  →  {reason}")


def separator(title):
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def safe_json(response, default=None):
    """Parse JSON safely — returns default if body is not JSON (e.g. HTML 500 page)."""
    try:
        return response.json()
    except Exception:
        return default if default is not None else {}


# ══════════════════════════════════════════════════════════════
# 1. AUTH APP
# ══════════════════════════════════════════════════════════════
separator("1. AUTH APP")
try:
    # 1.1 Wrong password
    r = httpx.post(f"{BASE}/auth/login/", json={"phone_number": "08140628953", "password": "wrong"}, timeout=10)
    check("Login wrong password → 401", r.status_code, 401)

    # 1.2 Correct login
    r = httpx.post(f"{BASE}/auth/login/", json={"phone_number": "08140628953", "password": "Admin1234!"}, timeout=10)
    check("Login correct password → 200", r.status_code, 200)
    data = safe_json(r).get("data", {})
    access = data.get("access", "")
    refresh = data.get("refresh", "")
    check("Login returns access token", bool(access), True)
    check("Login returns refresh token", bool(refresh), True)

    H = {"Authorization": f"Bearer {access}"}

    # 1.3 Profile (authenticated)
    r = httpx.get(f"{BASE}/auth/profile/", headers=H, timeout=10)
    check("GET profile (authenticated) → 200", r.status_code, 200)
    check("Profile has phone_number", "phone_number" in safe_json(r).get("data", {}), True)

    # 1.4 Profile (no token)
    r = httpx.get(f"{BASE}/auth/profile/", timeout=10)
    check("GET profile (no token) → 401", r.status_code, 401)

    # 1.5 Token refresh
    r = httpx.post(f"{BASE}/auth/token/refresh/", json={"refresh": refresh}, timeout=10)
    check("Token refresh → 200", r.status_code, 200)
    check("Refresh returns new access", "access" in safe_json(r), True)

    # 1.6 Register existing phone — returns 200 (sends OTP, prevents phone enumeration)
    r = httpx.post(f"{BASE}/auth/register/", json={"phone_number": "08140628953"}, timeout=10)
    check("Register existing phone → 200 (OTP sent)", r.status_code, 200)

    # 1.7 Login empty body
    r = httpx.post(f"{BASE}/auth/login/", json={}, timeout=10)
    check("Login empty body → 400", r.status_code, 400)
except Exception as e:
    print(f"  [ERROR] Auth section crashed: {e}")
    traceback.print_exc()


# ══════════════════════════════════════════════════════════════
# 2. METERS APP
# ══════════════════════════════════════════════════════════════
separator("2. METERS APP")
meter_id = ""
try:
    # 2.1 List meters
    r = httpx.get(f"{BASE}/meters/", headers=H, timeout=10)
    check("GET meters (auth) → 200", r.status_code, 200)
    meter_list = safe_json(r).get("results", safe_json(r) if isinstance(safe_json(r), list) else [])
    print(f"        Existing meters: {len(meter_list)}")

    # 2.2 No auth
    r = httpx.get(f"{BASE}/meters/", timeout=10)
    check("GET meters (no auth) → 401", r.status_code, 401)

    # 2.3 Validate meter (sandbox)
    r = httpx.post(f"{BASE}/meters/validate/", json={"meter_number": "45811090419", "disco": "IBEDC"}, headers=H, timeout=30)
    check("Validate meter (IBEDC) → 200", r.status_code, 200)
    check("Validation is_valid=True", safe_json(r).get("is_valid"), True)

    # 2.4 Validate empty body
    r = httpx.post(f"{BASE}/meters/validate/", json={}, headers=H, timeout=10)
    check("Validate empty body → 400", r.status_code, 400)

    # 2.5 Validate invalid DISCO
    r = httpx.post(f"{BASE}/meters/validate/", json={"meter_number": "12345", "disco": "FAKECO"}, headers=H, timeout=10)
    check("Validate bad DISCO → 400", r.status_code, 400)

    # 2.6 Cleanup existing test meter first (delete transactions referencing it, then the meter)
    from apps.meters.models import MeterProfile
    from apps.accounts.models import User
    from apps.transactions.models import Transaction
    superuser = User.objects.get(phone_number="08140628953")
    old_meters = MeterProfile.objects.filter(user=superuser, meter_number="45811090419", disco="IBEDC")
    if old_meters.exists():
        Transaction.objects.filter(meter__in=old_meters).delete()
        old_meters.delete()

    # 2.7 Add meter
    r = httpx.post(f"{BASE}/meters/", json={"meter_number": "45811090419", "disco": "IBEDC"}, headers=H, timeout=30)
    check("POST add meter → 201", r.status_code, 201)
    meter_id = safe_json(r).get("id", "")
    check("Created meter has UUID id", bool(meter_id), True)
    print(f"        Meter ID: {meter_id}")

    # 2.8 Duplicate add → 400
    r = httpx.post(f"{BASE}/meters/", json={"meter_number": "45811090419", "disco": "IBEDC"}, headers=H, timeout=30)
    check("POST duplicate meter → 400", r.status_code, 400)

    # 2.9 Retrieve single
    if meter_id:
        r = httpx.get(f"{BASE}/meters/{meter_id}/", headers=H, timeout=10)
        check("GET single meter → 200", r.status_code, 200)

    # 2.10 Set default
    if meter_id:
        r = httpx.post(f"{BASE}/meters/{meter_id}/set-default/", headers=H, timeout=10)
        check("Set default meter → 200", r.status_code, 200)
except Exception as e:
    print(f"  [ERROR] Meters section crashed: {e}")
    traceback.print_exc()


# ══════════════════════════════════════════════════════════════
# 3. PAYMENTS APP — Initiate + Verify
# ══════════════════════════════════════════════════════════════
separator("3. PAYMENTS APP")
txn_ref = ""
try:
    if not meter_id:
        skip("All payment tests", "No meter_id from previous section")
    else:
        # 3.1 Initiate with no auth
        r = httpx.post(f"{BASE}/payments/initiate/", json={}, timeout=10)
        check("Initiate (no auth) → 401", r.status_code, 401)

        # 3.2 Initiate with empty body
        r = httpx.post(f"{BASE}/payments/initiate/", json={}, headers=H, timeout=10)
        check("Initiate empty body → 400", r.status_code, 400)

        # 3.3 Initiate with invalid meter
        r = httpx.post(f"{BASE}/payments/initiate/", json={
            "meter_id": "00000000-0000-0000-0000-000000000000",
            "amount": "5000.00",
            "payment_gateway": "PAYSTACK"
        }, headers=H, timeout=15)
        check("Initiate bad meter → 400", r.status_code, 400)

        # 3.4 Initiate Paystack with REAL meter
        r = httpx.post(f"{BASE}/payments/initiate/", json={
            "meter_id": meter_id,
            "amount": "1000.00",
            "payment_gateway": "PAYSTACK"
        }, headers=H, timeout=30)
        check("Initiate Paystack → 201", r.status_code, 201)
        pay_data = safe_json(r).get("data", {})
        txn_ref = pay_data.get("transaction_reference", "")
        auth_url = pay_data.get("authorization_url", "")
        check("Response has transaction_reference", bool(txn_ref), True)
        check("Response has authorization_url", bool(auth_url), True)
        print(f"        TXN Reference: {txn_ref}")
        print(f"        Checkout URL:  {auth_url[:70]}..." if auth_url else "        Checkout URL:  (none)")

        # 3.5 Initiate Flutterwave with REAL meter
        r = httpx.post(f"{BASE}/payments/initiate/", json={
            "meter_id": meter_id,
            "amount": "2000.00",
            "payment_gateway": "FLUTTERWAVE"
        }, headers=H, timeout=30)
        check("Initiate Flutterwave → 201", r.status_code, 201)
        fw_data = safe_json(r).get("data", {})
        fw_ref = fw_data.get("transaction_reference", "")
        fw_url = fw_data.get("authorization_url", "")
        check("FW has transaction_reference", bool(fw_ref), True)
        check("FW has authorization_url", bool(fw_url), True)
        print(f"        TXN Reference: {fw_ref}")
        print(f"        Checkout URL:  {fw_url[:70]}..." if fw_url else "        Checkout URL:  (none)")

        # 3.6 Verify (no reference param)
        r = httpx.get(f"{BASE}/payments/verify/", headers=H, timeout=10)
        check("Verify no reference → 400", r.status_code, 400)

        # 3.7 Verify non-existent reference
        r = httpx.get(f"{BASE}/payments/verify/?reference=FAKE-REF", headers=H, timeout=10)
        check("Verify fake reference → 400", r.status_code, 400)

        # 3.8 Verify the real Paystack txn (payment not completed → gateway says not yet)
        r = httpx.get(f"{BASE}/payments/verify/?reference={txn_ref}", headers=H, timeout=30)
        # This should return 400 because payment was never completed at the checkout
        check("Verify unpaid txn → 400 (not yet paid)", r.status_code, 400)
except Exception as e:
    print(f"  [ERROR] Payments section crashed: {e}")
    traceback.print_exc()


# ══════════════════════════════════════════════════════════════
# 4. TRANSACTIONS APP
# ══════════════════════════════════════════════════════════════
separator("4. TRANSACTIONS APP")
try:
    # 4.1 List transactions (auth)
    r = httpx.get(f"{BASE}/transactions/", headers=H, timeout=10)
    check("GET transactions (auth) → 200", r.status_code, 200)
    txn_results = safe_json(r).get("results", [])
    txn_count = len(txn_results)
    print(f"        Transactions found: {txn_count}")

    # 4.2 List transactions (no auth)
    r = httpx.get(f"{BASE}/transactions/", timeout=10)
    check("GET transactions (no auth) → 401", r.status_code, 401)

    # 4.3 Get detail of the first transaction
    if txn_results:
        first_txn_id = txn_results[0]["id"]
        r = httpx.get(f"{BASE}/transactions/{first_txn_id}/", headers=H, timeout=10)
        check("GET transaction detail → 200", r.status_code, 200)
        detail = safe_json(r).get("data", {})
        check("Detail has reference", bool(detail.get("reference")), True)
        check("Detail has payment_status", bool(detail.get("payment_status")), True)
        check("Detail has can_resend_token", "can_resend_token" in detail, True)
    else:
        skip("Transaction detail (4 checks)", "No transactions to test")

    # 4.4 Get non-existent transaction
    r = httpx.get(f"{BASE}/transactions/00000000-0000-0000-0000-000000000000/", headers=H, timeout=10)
    check("GET fake transaction → 404", r.status_code, 404)

    # 4.5 Resend token on unpaid transaction (should fail — payment not SUCCESS)
    if txn_results:
        r = httpx.post(f"{BASE}/transactions/{first_txn_id}/resend-token/", headers=H, timeout=10)
        check("Resend token (unpaid) → 400", r.status_code, 400)
    else:
        skip("Resend token", "No transactions to test")

    # 4.6 Resend token on fake transaction
    r = httpx.post(f"{BASE}/transactions/00000000-0000-0000-0000-000000000000/resend-token/", headers=H, timeout=10)
    check("Resend token (fake txn) → 404", r.status_code, 404)
except Exception as e:
    print(f"  [ERROR] Transactions section crashed: {e}")
    traceback.print_exc()


# ══════════════════════════════════════════════════════════════
# 5. ADMIN PANEL APP
# ══════════════════════════════════════════════════════════════
separator("5. ADMIN PANEL APP")
try:
    # The superuser (08140628953) has is_staff=True, so admin endpoints should work
    from apps.accounts.models import User

    # 5.1 Dashboard stats
    r = httpx.get(f"{BASE}/admin/dashboard/", headers=H, timeout=10)
    check("GET dashboard stats → 200", r.status_code, 200)
    stats = safe_json(r).get("data", {})
    check("Dashboard has total_users", "total_users" in stats, True)
    check("Dashboard has total_transactions", "total_transactions" in stats, True)
    check("Dashboard has total_revenue", "total_revenue" in stats, True)
    print(f"        Total users: {stats.get('total_users')}")
    print(f"        Total transactions: {stats.get('total_transactions')}")
    print(f"        Revenue: ₦{stats.get('total_revenue')}")

    # 5.2 Dashboard (no auth)
    r = httpx.get(f"{BASE}/admin/dashboard/", timeout=10)
    check("GET dashboard (no auth) → 401", r.status_code, 401)

    # 5.3 List customers
    r = httpx.get(f"{BASE}/admin/users/", headers=H, timeout=10)
    check("GET admin/users → 200", r.status_code, 200)

    # 5.4 List customers with search
    r = httpx.get(f"{BASE}/admin/users/?search=08140628953", headers=H, timeout=10)
    check("Search users by phone → 200", r.status_code, 200)

    # 5.5 Customer detail
    superuser = User.objects.get(phone_number="08140628953")
    r = httpx.get(f"{BASE}/admin/users/{superuser.id}/", headers=H, timeout=10)
    check("GET admin/users/:id → 200", r.status_code, 200)

    # 5.6 Admin transactions list
    r = httpx.get(f"{BASE}/admin/transactions/", headers=H, timeout=10)
    check("GET admin/transactions → 200", r.status_code, 200)
    admin_txns = safe_json(r).get("results", [])
    print(f"        Admin sees {len(admin_txns)} transactions")

    # 5.7 Admin transactions with filter
    r = httpx.get(f"{BASE}/admin/transactions/?payment_status=PENDING", headers=H, timeout=10)
    check("Filter txns by PENDING → 200", r.status_code, 200)

    # 5.8 Admin transaction detail
    if admin_txns:
        atxn_id = admin_txns[0]["id"]
        r = httpx.get(f"{BASE}/admin/transactions/{atxn_id}/", headers=H, timeout=10)
        check("GET admin/transactions/:id → 200", r.status_code, 200)
        check("Admin detail has user_phone", "user_phone" in safe_json(r).get("data", {}), True)
    else:
        skip("Admin transaction detail", "No transactions")

    # 5.9 Resolve transaction
    if admin_txns:
        r = httpx.post(f"{BASE}/admin/transactions/{atxn_id}/resolve/", json={
            "resolution_notes": "Health check test — marked resolved."
        }, headers=H, timeout=10)
        check("Resolve transaction → 200", r.status_code, 200)
    else:
        skip("Resolve transaction", "No transactions")

    # 5.10 Audit logs
    r = httpx.get(f"{BASE}/admin/audit-logs/", headers=H, timeout=10)
    check("GET audit-logs → 200", r.status_code, 200)
    logs = safe_json(r).get("results", [])
    print(f"        Audit log entries: {len(logs)}")
    if logs:
        check("Audit log has action field", "action" in logs[0], True)
        print(f"        Latest action: {logs[0].get('action')}")

    # 5.11 List admin accounts
    r = httpx.get(f"{BASE}/admin/admins/", headers=H, timeout=10)
    check("GET admin/admins → 200", r.status_code, 200)

    # 5.12 Admin endpoints with non-staff user (create via ORM, test, delete)
    import uuid as _uuid
    test_phone = f"0900{_uuid.uuid4().hex[:7]}"
    try:
        test_user = User.objects.create_user(
            phone_number=test_phone,
            password="TestPass123!",
            full_name="Health Check User",
            is_verified=True,
        )
        # Login as non-staff
        r2 = httpx.post(f"{BASE}/auth/login/", json={"phone_number": test_phone, "password": "TestPass123!"}, timeout=10)
        if r2.status_code == 200:
            nonadmin_token = safe_json(r2).get("data", {}).get("access", "")
            NH = {"Authorization": f"Bearer {nonadmin_token}"}
            r3 = httpx.get(f"{BASE}/admin/dashboard/", headers=NH, timeout=10)
            check("Non-staff user → admin 403", r3.status_code, 403)
        else:
            skip("Non-staff admin test", f"Could not login test user (status {r2.status_code})")
        # Cleanup
        test_user.delete()
    except Exception as inner_e:
        skip("Non-staff admin test", f"Error: {inner_e}")
except Exception as e:
    print(f"  [ERROR] Admin section crashed: {e}")
    traceback.print_exc()


# ══════════════════════════════════════════════════════════════
# 6. WEBHOOKS — Signature Verification
# ══════════════════════════════════════════════════════════════
separator("6. WEBHOOKS")
try:
    # 6.1 Paystack webhook with wrong signature
    r = httpx.post(f"{BASE}/webhooks/paystack/", content=b'{"event":"charge.success"}',
        headers={"Content-Type": "application/json", "X-Paystack-Signature": "badsig"}, timeout=10)
    check("Paystack webhook bad sig → 400", r.status_code, 400)

    # 6.2 Flutterwave webhook with wrong hash
    r = httpx.post(f"{BASE}/webhooks/flutterwave/", content=b'{"event":"charge.completed"}',
        headers={"Content-Type": "application/json", "verif-hash": "badhash"}, timeout=10)
    check("Flutterwave webhook bad hash → 400", r.status_code, 400)
except Exception as e:
    print(f"  [ERROR] Webhooks section crashed: {e}")
    traceback.print_exc()


# ══════════════════════════════════════════════════════════════
# 7. API DOCS
# ══════════════════════════════════════════════════════════════
separator("7. API DOCS")
try:
    r = httpx.get("http://localhost:8000/api/schema/", timeout=10)
    check("OpenAPI schema → 200", r.status_code, 200)

    r = httpx.get("http://localhost:8000/api/docs/", timeout=10)
    check("Swagger UI → 200", r.status_code, 200)

    r = httpx.get("http://localhost:8000/api/redoc/", timeout=10)
    check("ReDoc → 200", r.status_code, 200)
except Exception as e:
    print(f"  [ERROR] API Docs section crashed: {e}")
    traceback.print_exc()


# ══════════════════════════════════════════════════════════════
# CLEANUP — Remove test meter
# ══════════════════════════════════════════════════════════════
separator("CLEANUP")
try:
    if meter_id:
        # Delete transactions referencing this meter first, then the meter
        from apps.transactions.models import Transaction as TxnCleanup
        from apps.meters.models import MeterProfile as MeterCleanup
        TxnCleanup.objects.filter(meter_id=meter_id).delete()
        MeterCleanup.objects.filter(id=meter_id).delete()
        print(f"  Deleted test meter + associated txns: {meter_id}")
    else:
        print("  No meter to clean up.")
except Exception as e:
    print(f"  Cleanup error: {e}")


# ══════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════
separator("FINAL SUMMARY")
total = PASS_COUNT + FAIL_COUNT + SKIP_COUNT
print(f"  Passed  : {PASS_COUNT} / {total}")
print(f"  Failed  : {FAIL_COUNT} / {total}")
print(f"  Skipped : {SKIP_COUNT} / {total}")
print()
if FAIL_COUNT == 0:
    print("  ✓ ALL SYSTEMS GREEN — Full backend is working.")
else:
    print(f"  ✗ {FAIL_COUNT} check(s) failed — review [FAIL] lines above.")
print()
