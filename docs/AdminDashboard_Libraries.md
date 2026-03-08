# ETIP Django Admin Dashboard — Libraries & Status

**Date documented:** February 26, 2026  
**Project:** Electricity Token Intermediary Platform (ETIP)  
**Django Admin URL:** http://localhost:8000/django-admin/

---

## Overview

The Django Admin dashboard at `/django-admin/` shows every registered database
table in the system. Each section is powered by either a third-party library
or our own application code. This document explains what each section is,
which library drives it, and its current working status.

---

## Full Library Map

```
Django Admin sections
│
├── Groups                  ← django (built-in)
├── Celery Results          ← django-celery-results 2.5.1
├── Meters                  ← our own code (apps/meters)
├── Otp_Totp                ← django-otp 1.5.4
├── Periodic Tasks          ← django-celery-beat 2.7.0
└── Token Blacklist         ← djangorestframework-simplejwt 5.3.1
```

---

## Section-by-Section Reference

### 1. Groups

| Property | Detail |
|---|---|
| **Library** | Django built-in — `django.contrib.auth` (no installation needed) |
| **Version** | Ships with Django 5.1.4 |
| **Status** | ✅ Working — always on |
| **Purpose** | Organise users into permission groups and assign bulk permissions |
| **Used in ETIP** | Minimal — ETIP uses its own role system (SUPER_ADMIN / OPERATOR) |

---

### 2. Celery Results (Group results + Task results)

| Property | Detail |
|---|---|
| **Library** | `django-celery-results` |
| **Version** | 2.5.1 |
| **Status** | ✅ Working — `etip_celery_worker` container confirmed Up |
| **Purpose** | Stores the result of every background task in the database |

**What you see in Admin:**

| Sub-section | What it contains |
|---|---|
| Task results | One row per background job — shows status (SUCCESS/FAILURE), return value, timestamp |
| Group results | Results of tasks that were chained or grouped together |

**What is Celery?**  
A background task runner. When a customer buys a token, we do not make them
wait while we call IBEDC's API and send an SMS. We hand that job to Celery
immediately and tell the customer "processing...". Celery does the heavy
work in the background. `django-celery-results` saves each job's outcome
into the database so it is visible here in Admin.

---

### 3. Meters — Meter Profiles

| Property | Detail |
|---|---|
| **Library** | Our own code — `apps/meters` |
| **Status** | ✅ Working — migrations applied, all endpoints verified |
| **Purpose** | Every meter number a customer saves is stored here |

**What you see in Admin:**  
Every `MeterProfile` record — meter number, DISCO, owner name, address,
whether it is the user's default, and whether it is active (soft-delete).

---

### 4. Otp_Totp — TOTP Devices

| Property | Detail |
|---|---|
| **Library** | `django-otp` + `qrcode[pil]` |
| **Versions** | django-otp 1.5.4 / qrcode 8.0 |
| **Status** | ⏳ Installed and migrated — not yet wired to admin login |
| **Pending** | Will be connected when `admin_panel` login + MFA is implemented |
| **Purpose** | 2-Factor Authentication (2FA) for admin staff accounts |

**How TOTP works:**  
TOTP = Time-based One-Time Password. Every 30 seconds an authenticator app
(e.g. Google Authenticator) generates a new 6-digit code. When an admin
logs in, they enter their password AND that code. Even if someone steals the
password, they cannot log in without the physical phone.

**What you see in Admin:**  
Each admin account that has linked a 2FA device — one row per device.

---

### 5. Periodic Tasks (Clocked, Crontabs, Intervals, Periodic tasks, Solar events)

| Property | Detail |
|---|---|
| **Library** | `django-celery-beat` |
| **Version** | 2.7.0 |
| **Status** | ✅ Working — `etip_celery_beat` container confirmed Up |
| **Purpose** | Schedule background tasks to run automatically on a timer |

**Sub-sections explained:**

| Sub-section | Library class | What it means | ETIP example |
|---|---|---|---|
| **Intervals** | `IntervalSchedule` | Run every X seconds / minutes / hours | Retry failed token deliveries every 5 minutes |
| **Crontabs** | `CrontabSchedule` | Unix cron-style schedule | Clean expired OTPs every night at midnight (`0 0 * * *`) |
| **Clocked** | `ClockedSchedule` | Run once at a specific date and time | One-time maintenance job |
| **Periodic tasks** | `PeriodicTask` | The actual job linked to one of the schedules above | "retry_failed_tokens — every 5 minutes" |
| **Solar events** | `SolarSchedule` | Trigger at sunrise or sunset | Not used in ETIP |

**How to read a crontab (`0 0 * * *`):**
```
┌─ minute   (0)
│ ┌─ hour   (0 = midnight)
│ │ ┌─ day of month  (* = every day)
│ │ │ ┌─ month       (* = every month)
│ │ │ │ ┌─ day of week (* = every day)
0 0 * * *
```

---

### 6. Token Blacklist (Blacklisted tokens + Outstanding tokens)

| Property | Detail |
|---|---|
| **Library** | `djangorestframework-simplejwt` — `token_blacklist` plugin |
| **Version** | 5.3.1 |
| **Status** | ✅ Working — the logout endpoint uses it right now |
| **Purpose** | Track every JWT refresh token ever issued, record which are invalidated |

**Sub-sections explained:**

| Sub-section | What it contains |
|---|---|
| **Outstanding tokens** | Every refresh token ever created — one row per login |
| **Blacklisted tokens** | Tokens invalidated by logout — can never be used again |

**Why blacklisting matters:**  
JWT tokens are self-contained — the server does not store them by default.
If a user logs out, the token would still technically be valid until it
expires in 30 days. Blacklisting solves this: on logout, the token is added
to the blacklist and any future request using it is rejected immediately.

---

## Container Status (verified February 26, 2026)

| Container | Role | Status |
|---|---|---|
| `etip_api` | Django application server (port 8000) | ✅ Up |
| `etip_postgres` | PostgreSQL 16 database (port 5432) | ✅ Up (healthy) |
| `etip_redis` | Redis 7 cache + task broker (port 6379) | ✅ Up (healthy) |
| `etip_celery_worker` | Celery background task runner | ✅ Up |
| `etip_celery_beat` | Celery scheduled task trigger | ✅ Up |
| `etip_flower` | Celery monitoring dashboard (port 5555) | ✅ Up |

---

## Working Status Summary

| Admin Section | Working? | Notes |
|---|---|---|
| Groups | ✅ | Always on — Django built-in |
| Celery Results | ✅ | Worker running |
| Meters | ✅ | Built and tested |
| Otp_Totp | ⏳ | Installed, pending admin_panel MFA wiring |
| Periodic Tasks | ✅ | Beat scheduler running |
| Token Blacklist | ✅ | Logout endpoint uses it now |

---

## Auth & Meters Health Check (Feb 26, 2026)

Scope: Live verification was performed on February 26, 2026 on local Docker for two implemented microservices: Auth and Meters.

Auth Verification
Login (valid credentials)
Expected: 200 with access and refresh
Observed: Success response with JWT tokens
Status: ✅ Pass
Login (invalid password)
Expected: 401 Unauthorized
Observed: Returned unauthorized
Status: ✅ Pass
Profile (with Bearer token)
Expected: 200 with profile data
Observed: Returned authenticated user profile
Status: ✅ Pass
Profile (without token)
Expected: 401 Unauthorized
Observed: Returned auth error
Status: ✅ Pass
Token refresh
Expected: 200 with new access token
Observed: Returned refreshed access token
Status: ✅ Pass
JWT enforcement
Expected: Protected routes require valid Bearer token
Observed: Enforced correctly
Status: ✅ Pass
Meters Verification
List meters (authenticated)
Expected: 200 list response
Observed: Returned active meters for logged-in user
Status: ✅ Pass
List meters (without token)
Expected: 401 Unauthorized
Observed: Returned auth error
Status: ✅ Pass
Validate meter (IBEDC, local sandbox mode)
Expected: 200, is_valid=true
Observed: Returned valid sandbox payload (SANDBOX CUSTOMER)
Status: ✅ Pass
Validate meter (invalid input)
Expected: 400 validation error
Observed: Serializer errors returned correctly
Status: ✅ Pass
Create meter profile
Expected: 201 + created record
Observed: Meter created with UUID
Status: ✅ Pass
Retrieve single meter
Expected: 200 + matching record
Observed: Retrieved successfully
Status: ✅ Pass
Set default meter
Expected: 200 success message
Observed: Default updated successfully
Status: ✅ Pass
Soft-delete meter
Expected: 204, removed from active list
Observed: Soft-delete worked and list updated
Status: ✅ Pass
Findings
auth service is healthy.
meters service is healthy after local DISCO env correction.
Earlier single failed check was a test expectation mismatch (phone normalization), not a runtime failure.
Current Operational Status
Auth: ✅ Healthy (login, JWT, profile, refresh verified)
Meters: ✅ Healthy (validate/create/list/retrieve/default/delete verified)
Next Check
Re-run after any .env updates, token lifetime changes, or auth/meters code changes; watch JWT expiry behavior and DISCO config drift.


## Useful URLs

| URL | What you find there |
|---|---|
| http://localhost:8000/django-admin/ | Django Admin dashboard |
| http://localhost:8000/api/docs/ | Swagger UI — test all API endpoints |
| http://localhost:8000/api/redoc/ | ReDoc — read-only API reference |
| http://localhost:5555 | Flower — Celery task monitoring |
