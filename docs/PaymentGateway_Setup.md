# Payment Gateway Setup — ETIP

> Last updated: February 26, 2026

---

## Overview

ETIP supports **two payment gateways** for electricity token purchases:

| Gateway | Mode | Status | API Base URL |
|---------|------|--------|-------------|
| **Paystack** | Test (sandbox) | ✅ Real test keys loaded | `https://api.paystack.co` |
| **Flutterwave** | Test (sandbox) | ✅ Real test keys loaded | `https://api.flutterwave.com/v3` |

Both are in **test mode** — no real money is charged. Test mode uses sandbox card numbers to simulate purchases.

---

## 1. Paystack

### Account
- Dashboard: https://dashboard.paystack.com
- Account email: *(your registered email)*

### Keys (Test Mode)
- **Secret Key:** `sk_test_188b...ec17` (stored in `.env`)
- **Public Key:** `pk_test_c822...8e56` (stored in `.env`)
- Base URL: `https://api.paystack.co`

### How It Works in ETIP
1. Customer hits `POST /api/v1/payments/initiate/` with `payment_gateway: "PAYSTACK"`
2. Backend calls Paystack's `POST /transaction/initialize` → gets a checkout URL
3. Customer is redirected to the checkout URL to enter card details
4. After payment, customer is redirected to `{FRONTEND_URL}/payment/verify`
5. Frontend calls `GET /api/v1/payments/verify/?reference=ETIP-XXXX`
6. Backend calls Paystack's `GET /transaction/verify/:reference` → confirms payment
7. Paystack also sends a webhook to `POST /api/v1/webhooks/paystack/`
8. Webhook is verified using **HMAC-SHA512** with the secret key

### Test Card Numbers
| Card Number | Expiry | CVV | OTP | Result |
|---|---|---|---|---|
| `4084 0840 8408 4081` | Any future date | `408` | `123456` | Success |
| `4084 0840 8408 4081` | Any future date | `408` | `123456` (pin: `1234`) | Success with PIN |

> Full list: https://paystack.com/docs/payments/test-payments

### Webhook Setup (for deployment)
When you deploy to a live server:
1. Go to **Paystack Dashboard → Settings → API Keys & Webhooks**
2. Set **Webhook URL** to: `https://your-domain.com/api/v1/webhooks/paystack/`
3. Paystack will now send `charge.success` events to your server automatically

---

## 2. Flutterwave

### Account
- Dashboard: https://app.flutterwave.com
- Account email: *(your registered email)*

### Keys (Test Mode)
- **Secret Key:** `FLWSECK_TEST-247a...8c5-X` (stored in `.env`)
- **Public Key:** `FLWPUBK_TEST-a275...61d-X` (stored in `.env`)
- **Encryption Key (Webhook Hash):** `FLWSECK_TESTbb495e5bab4c` (stored in `.env`)
- Base URL: `https://api.flutterwave.com/v3`

### How It Works in ETIP
1. Customer hits `POST /api/v1/payments/initiate/` with `payment_gateway: "FLUTTERWAVE"`
2. Backend calls Flutterwave's `POST /payments` → gets a hosted checkout link
3. Customer is redirected to complete payment
4. After payment, customer is redirected to `{FRONTEND_URL}/payment/verify`
5. Frontend calls `GET /api/v1/payments/verify/?reference=ETIP-XXXX`
6. Backend calls Flutterwave's `GET /transactions/:id/verify` → confirms payment
7. Flutterwave also sends a webhook to `POST /api/v1/webhooks/flutterwave/`
8. Webhook is verified using the **verif-hash** header against the encryption key

### Test Card Numbers
| Card Number | Expiry | CVV | OTP | PIN | Result |
|---|---|---|---|---|---|
| `5531 8866 5214 2950` | `09/32` | `564` | `12345` | `3310` | Success |
| `5258 5859 2266 6506` | `09/32` | `883` | `12345` | `3310` | Success |

> Full list: https://developer.flutterwave.com/docs/integration-guides/testing-helpers

### Webhook Setup (for deployment)
When you deploy to a live server:
1. Go to **Flutterwave Dashboard → Settings → Webhooks**
2. Set **Webhook URL** to: `https://your-domain.com/api/v1/webhooks/flutterwave/`
3. The **Secret Hash** should match `FLUTTERWAVE_HASH` in your `.env`

---

## 3. ETIP Payment Endpoints

| Method | URL | Auth | Purpose |
|--------|-----|------|---------|
| `POST` | `/api/v1/payments/initiate/` | JWT | Start a token purchase |
| `GET` | `/api/v1/payments/verify/?reference=...` | JWT | Verify payment after redirect |
| `POST` | `/api/v1/webhooks/paystack/` | None (signature) | Paystack webhook receiver |
| `POST` | `/api/v1/webhooks/flutterwave/` | None (hash) | Flutterwave webhook receiver |

---

## 4. .env Variables Reference

```env
# Paystack
PAYSTACK_SECRET_KEY=sk_test_...          # From Paystack Dashboard → Settings → API Keys
PAYSTACK_PUBLIC_KEY=pk_test_...          # Same page
PAYSTACK_BASE_URL=https://api.paystack.co

# Flutterwave
FLUTTERWAVE_SECRET_KEY=FLWSECK_TEST-... # From Flutterwave Dashboard → Settings → API Keys
FLUTTERWAVE_PUBLIC_KEY=FLWPUBK_TEST-... # Same page
FLUTTERWAVE_BASE_URL=https://api.flutterwave.com/v3
FLUTTERWAVE_HASH=...                     # Encryption key from the same page
```

---

## 5. Switching to Live Mode (Production)

When ready for real payments:

1. **Paystack:**
   - Complete business verification on Paystack Dashboard
   - Toggle to **Live Mode**
   - Copy the live keys (`sk_live_...`, `pk_live_...`)
   - Update `.env` on the production server

2. **Flutterwave:**
   - Complete KYC verification on Flutterwave Dashboard
   - Toggle to **Live Mode**
   - Copy the live keys
   - Update `.env` on the production server

3. Update webhook URLs to your production domain
4. **NEVER commit live keys to Git**

---

## 6. ⚠️ ACTION ITEMS — Things YOU Need To Do

These are tasks that cannot be automated — they require your personal action:

### Already Done ✅
- [x] Created Paystack account and got test keys
- [x] Created Flutterwave account and got test keys
- [x] Keys loaded into `.env` and container rebuilt

### Still Pending ❌

#### HIGH PRIORITY (Before Presentation)
- [ ] **SMS Gateway account** — Currently placeholder in `.env`. You need a real SMS provider (e.g., Termii, Africa's Talking, or Twilio) for OTP delivery. Without this, OTP verification uses console output only.
  - Go to https://www.termii.com or https://africastalking.com
  - Create account → get API key
  - Update `.env`: `SMS_GATEWAY_URL` and `SMS_GATEWAY_API_KEY`

- [ ] **DISCO API credentials** — Currently blank (sandbox stubs active). For real meter validation & token generation, you need API agreements with:
  - IBEDC (Ibadan Electricity Distribution Company)
  - EKEDC (Eko Electricity Distribution Company)
  - AEDC (Abuja Electricity Distribution Company)
  - This typically requires a business registration and API partnership application
  - For SIWES demo: sandbox stubs work fine — shows the architecture

#### MEDIUM PRIORITY (Before Deployment)
- [ ] **Firebase project** — For push notifications to mobile app
  - Go to https://console.firebase.google.com
  - Create project → download `firebase_credentials.json`
  - Place it at `backend/config/firebase_credentials.json`

- [ ] **Domain name** — Needed for webhook URLs and deployment
  - Register a domain (e.g., Namecheap, Google Domains)
  - Point DNS to your server

- [ ] **Production server** — AWS, DigitalOcean, or Railway for hosting
  - Set up Docker on the server
  - Configure SSL certificate (Let's Encrypt)

#### LOW PRIORITY (Nice to Have)
- [ ] **AWS S3 bucket** — For receipt storage and exports
  - Currently placeholder keys in `.env`
  - Not needed for MVP/SIWES demo

- [ ] **Email SMTP** — For admin notifications
  - Currently placeholder in `.env`
  - Can use Gmail app password or Mailgun

- [ ] **Paystack webhook URL** — Set in Paystack dashboard when deployed
- [ ] **Flutterwave webhook URL** — Set in Flutterwave dashboard when deployed
