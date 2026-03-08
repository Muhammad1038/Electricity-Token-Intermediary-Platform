# Electricity Token Intermediary Platform (ETIP)
# Minimum Viable Product (MVP) Document

> **Version:** 1.0  
> **Date:** February 22, 2026  
> **Status:** Draft  
> **Owner:** Product Team  

---

## Table of Contents

1. [MVP Overview](#1-mvp-overview)
2. [Problem Statement](#2-problem-statement)
3. [MVP Goals & Objectives](#3-mvp-goals--objectives)
4. [Target Users (MVP)](#4-target-users-mvp)
5. [Core MVP Features](#5-core-mvp-features)
6. [User Stories & Acceptance Criteria](#6-user-stories--acceptance-criteria)
7. [Out-of-Scope for MVP](#7-out-of-scope-for-mvp)
8. [MVP Success Metrics](#8-mvp-success-metrics)
9. [Technical Architecture (MVP)](#9-technical-architecture-mvp)
10. [MVP Data Model Overview](#10-mvp-data-model-overview)
11. [Integration Points](#11-integration-points)
12. [MVP Risks & Mitigations](#12-mvp-risks--mitigations)
13. [MVP Release Criteria](#13-mvp-release-criteria)
14. [Milestones & Timeline](#14-milestones--timeline)
15. [Assumptions & Constraints](#15-assumptions--constraints)

---

## 1. MVP Overview

The **Electricity Token Intermediary Platform (ETIP)** MVP is the first shippable version of a digital platform that allows customers to purchase prepaid electricity tokens from authorized electricity distribution companies (DISCOs) through a fast, secure, and reliable intermediary system.

The MVP focuses exclusively on end-to-end token delivery — from meter validation to payment processing to token display — as the critical path that delivers immediate customer value and validates the core business model.

> **MVP Hypothesis:** If customers can purchase prepaid electricity tokens digitally in under 10 seconds with a success rate above 99%, they will prefer this platform over manual/physical alternatives, and the platform will achieve sustainable transaction volume growth month-over-month.

---

## 2. Problem Statement

### Current Pain Points

| # | Problem | Impact |
|---|---------|--------|
| 1 | Customers must physically visit vending points to purchase electricity tokens | Time-consuming, especially during off-hours or emergencies |
| 2 | Manual processing introduces errors (wrong meter numbers, incorrect amounts) | Failed purchases and customer frustration |
| 3 | No centralized digital history of past purchases | Customers cannot self-service or resolve disputes |
| 4 | Utility companies lack a scalable digital distribution channel | Revenue leakage and high operational costs |
| 5 | No real-time payment reconciliation exists for intermediaries | Manual reconciliation; high audit overhead |

### Opportunity

A mobile-first digital intermediary platform can eliminate physical friction, enable 24/7 token purchases, and provide transparent transaction tracking — serving as a scalable bridge between customers and DISCOs.

---

## 3. MVP Goals & Objectives

### Primary Goal
Deliver a fully functional, end-to-end electricity token purchase flow on both mobile (React Native) and web (Admin Dashboard) that is reliable, secure, and scalable from day one.

### MVP Objectives

| Objective | Measurement |
|-----------|-------------|
| Validate core token purchase flow | Complete E2E flow from meter input → payment → token delivery |
| Achieve reliable token delivery | Token delivery success rate ≥ 99% |
| Enable fast transactions | Average end-to-end token delivery ≤ 10 seconds |
| Minimize payment failures | Payment failure rate ≤ 1% |
| Provide admin visibility | Admin can view, filter, and export all transactions |

---

## 4. Target Users (MVP)

### 4.1 Primary User — Consumer

- **Who:** Individual with a prepaid electricity meter
- **Motivation:** Purchase electricity tokens quickly without visiting a physical vending point
- **Tech Comfort:** Basic smartphone or internet user
- **Key Need:** Fast, reliable token delivery with confirmation

### 4.2 Secondary User — Platform Admin / Operator

- **Who:** Internal operations staff managing the platform
- **Motivation:** Monitor transaction health, resolve disputes, and generate reports
- **Key Need:** Real-time dashboard, transaction search, and issue resolution tools

### 4.3 External System — DISCO (Utility Partner)

- **Who:** Electricity Distribution Company (e.g., IBEDC, EKEDC, AEDC)
- **Role:** Token issuing authority via API
- **Key Requirement:** Secure, authorized API communication for meter validation and token generation

---

## 5. Core MVP Features

### 5.1 Consumer Mobile & Web App Features

#### F-01: User Authentication
- Email/phone-based registration with OTP verification
- Secure login with JWT-based session management
- Password reset flow

#### F-02: Meter Number Validation
- Input field for meter number entry
- Real-time validation call to DISCO API before payment proceeds
- Clear error messaging for invalid or unrecognized meters

#### F-03: Electricity Provider Selection
- Dropdown/list of available DISCO providers
- Provider-to-meter auto-detection where DISCO API supports it

#### F-04: Token Purchase (Amount-Based)
- Customer selects or inputs purchase amount (within defined min/max limits)
- Estimated unit preview (kWh) displayed before payment
- Confirmation screen before payment initiation

#### F-05: Online Payment Processing
- Integration with **Paystack** and **Flutterwave**
- Secure payment flow (redirect or inline SDK)
- Payment status polling with real-time feedback
- Automatic retry for transient payment failures

#### F-06: Token Display & Delivery
- Token displayed in-app immediately upon successful payment and DISCO confirmation
- Push notification and/or SMS delivery of token
- Token displayed in a copy-to-clipboard format

#### F-07: Transaction History & Receipts
- Chronological list of all past transactions
- Detailed receipt view: date, meter, amount, token, status
- Downloadable/shareable receipt (PDF or plain text)

---

### 5.2 Admin Dashboard Features

#### F-08: Admin Authentication
- Role-based access control (Super Admin, Operator)
- Secure login with audit log of admin sessions

#### F-09: Transaction Monitoring
- Real-time transaction feed with status indicators (Pending, Success, Failed)
- Search and filter by: date range, meter number, DISCO, status, user
- Export transactions to CSV/Excel

#### F-10: User Management
- View and search registered users
- Ability to suspend/reactivate user accounts
- View a user's complete transaction history

#### F-11: Reporting & Reconciliation
- Daily/weekly/monthly summary reports (volume, revenue, success rate)
- Reconciliation view for payment gateway vs. DISCO token logs
- Flagging of unresolved/discrepant transactions

#### F-12: Manual Issue Resolution
- Ability to manually trigger token resend for a completed transaction
- Log resolution notes per transaction
- Mark transactions as resolved or escalated

---

## 6. User Stories & Acceptance Criteria

### Consumer Stories

---

#### US-01: Account Registration

> **As a** new user,  
> **I want to** create an account using my phone number or email,  
> **So that** I can securely access the platform and track my purchases.

**Acceptance Criteria:**
- [ ] User can register with phone number (+ OTP verification) or email + password
- [ ] OTP expires after 5 minutes and can be resent once per 60 seconds
- [ ] Duplicate phone/email registration is rejected with a clear message
- [ ] Upon successful registration, user is redirected to the home/dashboard screen
- [ ] Registration data is stored encrypted in the database

---

#### US-02: Meter Validation

> **As a** consumer,  
> **I want to** validate my meter number before making a payment,  
> **So that** I don't pay for a token that can't be delivered to my meter.

**Acceptance Criteria:**
- [ ] Meter number field accepts numeric input only (length validated per DISCO standard)
- [ ] System calls DISCO meter validation API when user submits the meter number
- [ ] If valid: meter owner's name and address are displayed for confirmation
- [ ] If invalid: a clear error message is shown and payment cannot proceed
- [ ] Validation response must return within 5 seconds; timeout shows a user-friendly error

---

#### US-03: Provider Selection

> **As a** consumer,  
> **I want to** select my electricity distribution company,  
> **So that** the correct DISCO API is called for my region.

**Acceptance Criteria:**
- [ ] A list of all integrated DISCO providers is displayed
- [ ] User can search or scroll to select their provider
- [ ] Selected provider is persisted for future transactions (can be changed)
- [ ] Auto-selection is attempted if DISCO can be inferred from meter number prefix

---

#### US-04: Token Purchase

> **As a** consumer,  
> **I want to** purchase an electricity token by entering an amount,  
> **So that** I can top up my prepaid meter without visiting a vendor.

**Acceptance Criteria:**
- [ ] User can input a purchase amount within the allowed range (e.g., ₦500 – ₦100,000)
- [ ] Estimated kWh equivalent is shown before payment
- [ ] A summary confirmation screen is shown before final payment initiation
- [ ] On payment success, DISCO API is called to generate the token
- [ ] Token is displayed within 10 seconds of payment confirmation
- [ ] If DISCO token generation fails after payment, transaction is logged and flagged for admin resolution

---

#### US-05: Payment Processing

> **As a** consumer,  
> **I want to** pay securely using my card or bank transfer,  
> **So that** my transaction is processed safely.

**Acceptance Criteria:**
- [ ] Paystack and/or Flutterwave payment modal is launched within the app
- [ ] Payment status is verified via server-side webhook (not client-side only)
- [ ] On payment failure, the user is notified with a specific reason (e.g., insufficient funds, card declined)
- [ ] User is never charged without a corresponding token generation attempt
- [ ] Payment amount is deducted only once, even in retry scenarios

---

#### US-06: Token Display & Notification

> **As a** consumer,  
> **I want to** see my purchased electricity token immediately and receive a notification,  
> **So that** I can enter the token into my meter without delay.

**Acceptance Criteria:**
- [ ] Token is displayed in a large, readable format with a "Copy" button
- [ ] Token is sent via push notification (if app is in background)
- [ ] Token is sent via SMS as a fallback if push notification fails
- [ ] Token remains accessible in transaction history indefinitely

---

#### US-07: Transaction History

> **As a** consumer,  
> **I want to** view all my past transactions,  
> **So that** I can track my spending and retrieve past tokens if needed.

**Acceptance Criteria:**
- [ ] Transaction history loads in reverse chronological order
- [ ] Each entry shows: date, meter number, amount, token (masked or full), status
- [ ] Tapping an entry shows the full receipt
- [ ] Receipt can be shared or downloaded as PDF
- [ ] History is paginated (20 records per page)

---

### Admin Stories

---

#### US-08: Admin Transaction Monitoring

> **As an** operator,  
> **I want to** view and filter all platform transactions in real time,  
> **So that** I can quickly identify and respond to failed or suspicious transactions.

**Acceptance Criteria:**
- [ ] Dashboard shows live transaction feed with auto-refresh (every 30 seconds or WebSocket)
- [ ] Filters available: date range, DISCO, status, meter number, user ID
- [ ] Status badges clearly indicate: Pending, Success, Failed, Resolved
- [ ] Export to CSV is available for filtered results

---

#### US-09: Manual Token Resend

> **As an** operator,  
> **I want to** manually resend a token for a successful payment where delivery failed,  
> **So that** the customer receives their purchased token without a refund process.

**Acceptance Criteria:**
- [ ] Operator can search by transaction ID or meter number
- [ ] Resend option is only available for transactions in "Payment Success / Token Failed" state
- [ ] Resend triggers a new DISCO API call using the original transaction reference
- [ ] Result (success or failure) is logged with operator ID and timestamp

---

#### US-10: Reporting

> **As an** admin,  
> **I want to** generate summary reports for any time period,  
> **So that** I can monitor platform performance and prepare financial reconciliations.

**Acceptance Criteria:**
- [ ] Reports can be generated for: daily, weekly, monthly, or custom date ranges
- [ ] Report includes: total transactions, total value, success rate, failure rate, DISCO breakdown
- [ ] Reports can be exported as CSV or PDF
- [ ] Reconciliation report shows payment gateway records vs. DISCO token records side-by-side

---

## 7. Out-of-Scope for MVP

The following items are explicitly **excluded** from the MVP to maintain focus and delivery speed:

| Feature | Reason Excluded | Planned Phase |
|---------|----------------|---------------|
| Remote meter unit injection (smart meters) | Requires DISCO smart infrastructure | Phase 3 |
| AI-based customer support chatbot | Complex, not core to initial transaction flow | Phase 2 |
| Hardware/firmware meter control | Regulatory and infrastructure dependency | Phase 3 |
| Multi-language support (localization) | Deferred; single-language launch | Post-MVP |
| Loyalty/rewards program | Not core to value proposition at MVP | Post-MVP |
| Wallet/balance top-up system | Adds payment complexity | Post-MVP |
| Third-party agent/reseller portal | Separate product surface | Phase 2 |
| WhatsApp/USSD channel | Channel diversification deferred | Phase 2 |
| Automated AI issue triage | Requires ML model training and data | Phase 2 |
| Dark mode / advanced UI theming | UX enhancement | Post-MVP |

---

## 8. MVP Success Metrics

### Primary KPIs

| KPI | Target | Measurement Method |
|-----|--------|-------------------|
| Token Delivery Success Rate | ≥ 99% | (Successful tokens / Total confirmed payments) × 100 |
| Average Token Delivery Time | ≤ 10 seconds | Timestamp: payment confirmation → token displayed |
| Payment Failure Rate | ≤ 1% | (Failed payments / Total payment attempts) × 100 |
| System Uptime | ≥ 99.5% | Uptime monitoring tool (e.g., UptimeRobot / Datadog) |
| API Response Time (p95) | ≤ 2 seconds | Backend API monitoring |

### Growth KPIs (Tracked from Week 1)

| KPI | Target at 30 Days | Target at 90 Days |
|-----|------------------|------------------|
| Registered Users | 500 | 5,000 |
| Monthly Active Users (MAU) | 200 | 2,000 |
| Total Transactions | 1,000 | 15,000 |
| Transaction Volume (₦) | ₦1,000,000 | ₦20,000,000 |
| Retention Rate (D30) | 30% | 40% |

### Quality KPIs

| KPI | Target |
|-----|--------|
| App Crash Rate | < 0.5% of sessions |
| Admin Dashboard Uptime | 99.9% |
| Customer Support Tickets (token delivery) | < 2% of transactions |

---

## 9. Technical Architecture (MVP)

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│   ┌─────────────────────┐     ┌──────────────────────────────┐  │
│   │  Mobile App          │     │  Web Admin Dashboard          │  │
│   │  (React Native)      │     │  (React.js)                   │  │
│   └──────────┬──────────┘     └───────────────┬──────────────┘  │
└──────────────┼────────────────────────────────┼─────────────────┘
               │ HTTPS / REST API               │ HTTPS / REST API
┌──────────────┼────────────────────────────────┼─────────────────┐
│              │       BACKEND LAYER             │                  │
│   ┌──────────▼────────────────────────────────▼──────────────┐  │
│   │         Django + Django REST Framework (DRF)               │  │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐ │  │
│   │  │  Auth    │ │  Token   │ │  Payment │ │   Admin     │ │  │
│   │  │  Module  │ │  Module  │ │  Module  │ │   Module    │ │  │
│   │  └──────────┘ └──────────┘ └──────────┘ └─────────────┘ │  │
│   └────────────────────────────┬─────────────────────────────┘  │
│                                │                                  │
│   ┌────────────────────────────▼─────────────────────────────┐  │
│   │              Task Queue (Celery + Redis)                   │  │
│   │         Async: Token polling, Notifications, Reports       │  │
│   └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
               │                        │
┌──────────────┼────────────┐  ┌────────┼──────────────────────────┐
│  EXTERNAL APIs            │  │  DATABASE & CACHE                 │
│  ┌───────────▼──────────┐ │  │  ┌─────▼──────────────────────┐  │
│  │  DISCO Token APIs     │ │  │  │  PostgreSQL (Primary DB)    │  │
│  │  (per provider)       │ │  │  └────────────────────────────┘  │
│  └──────────────────────┘ │  │  ┌────────────────────────────┐  │
│  ┌──────────────────────┐ │  │  │  Redis (Cache + Task Queue) │  │
│  │  Paystack API         │ │  │  └────────────────────────────┘  │
│  └──────────────────────┘ │  └───────────────────────────────────┘
│  ┌──────────────────────┐ │
│  │  Flutterwave API      │ │  ┌───────────────────────────────────┐
│  └──────────────────────┘ │  │  NOTIFICATIONS                    │
│  ┌──────────────────────┐ │  │  Firebase Cloud Messaging (Push)  │
│  │  SMS Gateway          │ │  │  SMS Gateway (Fallback)           │
│  └──────────────────────┘ │  └───────────────────────────────────┘
└───────────────────────────┘
```

### Tech Stack Summary

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Mobile Frontend | React Native | Cross-platform iOS + Android from single codebase |
| Web Admin | React.js | Consistent JS ecosystem; rapid admin UI development |
| Backend API | Django + DRF | Mature, secure Python framework; rapid API development |
| Database | PostgreSQL | ACID compliant; ideal for financial transaction data |
| Cache / Queue | Redis + Celery | Fast async processing; retry logic for token delivery |
| Payment | Paystack + Flutterwave | Leading Nigerian payment gateways with good uptime |
| Notifications | FCM + SMS Gateway | Push primary, SMS fallback for token delivery |
| Hosting | Cloud (AWS / GCP) | Auto-scaling, managed services, high availability |
| Auth | JWT (SimpleJWT) | Stateless, scalable authentication |

---

## 10. MVP Data Model Overview

### Core Entities

```
User
├── id (UUID)
├── phone_number (unique)
├── email (unique, optional)
├── full_name
├── is_verified (bool)
├── created_at
└── updated_at

MeterProfile
├── id (UUID)
├── user_id → User
├── meter_number
├── disco → DISCO
├── meter_owner_name
├── address
└── is_default (bool)

Transaction
├── id (UUID)
├── reference (unique string)
├── user_id → User
├── meter_id → MeterProfile
├── disco
├── amount (decimal)
├── payment_status [PENDING | SUCCESS | FAILED]
├── token_status  [PENDING | DELIVERED | FAILED | RESENT]
├── token_value (encrypted string)
├── payment_gateway [PAYSTACK | FLUTTERWAVE]
├── gateway_reference
├── disco_reference
├── created_at
├── updated_at
└── resolved_at

AdminUser
├── id (UUID)
├── email (unique)
├── role [SUPER_ADMIN | OPERATOR]
├── is_active
└── last_login

AuditLog
├── id (UUID)
├── actor_id (AdminUser or User)
├── action (string)
├── target_type (string)
├── target_id (UUID)
├── metadata (JSON)
└── timestamp
```

---

## 11. Integration Points

### 11.1 DISCO API Integration

| Integration | Endpoint Type | Purpose |
|-------------|--------------|---------|
| Meter Validation | REST GET | Validate meter number, return owner info |
| Token Request | REST POST | Submit payment ref, receive token string |
| Token Status Poll | REST GET | Check token generation status (async) |

**Failure Handling:**
- Retry up to **3 times** with **exponential backoff** (2s, 4s, 8s)
- On all retries exhausted: flag transaction as "Token Failed," notify admin, do **not** refund automatically
- Async retry job scheduled via Celery for unresolved token failures

### 11.2 Payment Gateway Integration

| Gateway | Integration Method | Webhook Used |
|---------|------------------|--------------|
| Paystack | Inline JS SDK + Server-side webhook | `charge.success`, `charge.failed` |
| Flutterwave | Inline SDK + Server-side webhook | `charge.completed` |

**Critical Rule:** Token generation is only triggered by **server-side webhook confirmation**, never by client-side callback alone.

### 11.3 Notification Integration

| Channel | Provider | Trigger |
|---------|----------|---------|
| Push Notification | Firebase Cloud Messaging | Token delivered |
| SMS | Chosen SMS Gateway | Push failure fallback |
| In-App | WebSocket / Poll | Real-time status update |

---

## 12. MVP Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| DISCO API downtime or rate limiting | Medium | High | Implement retries with backoff; queue failed jobs; admin alert |
| Payment gateway outage | Low | High | Support both Paystack & Flutterwave; auto-failover |
| Double-charging on payment retry | Low | Very High | Idempotency keys on all payment requests; server-side deduplication |
| Token delivered but user doesn't receive it | Medium | Medium | In-app history + SMS fallback; "resend token" in history |
| Invalid meter number accepted | Low | High | Pre-payment DISCO validation mandatory; cannot bypass |
| Fraudulent account creation | Medium | Medium | OTP verification; rate limiting; device fingerprinting |
| Regulatory non-compliance | Low | Very High | Legal review before launch; adhere to CBN and utility guidelines |
| Database overload at peak | Low | High | Connection pooling (PgBouncer); Redis caching; horizontal scaling |
| Slow token delivery > 10s | Medium | Medium | Async processing; Celery workers; monitoring alerts at 8s threshold |

---

## 13. MVP Release Criteria

The MVP is considered **ready for production release** when ALL of the following criteria are met:

### Functional Completeness
- [ ] All F-01 through F-12 features are implemented and tested
- [ ] All US-01 through US-10 user stories pass acceptance testing
- [ ] End-to-end flow (register → validate → pay → receive token) works for all integrated DISCOs

### Quality Gates
- [ ] Unit test coverage ≥ 80% on backend modules
- [ ] All critical user flows covered by integration tests
- [ ] Zero P0 (critical) bugs open
- [ ] Zero P1 (high) bugs open related to payment or token delivery
- [ ] Load test: system handles 100 concurrent transactions without degradation

### Performance Gates
- [ ] API p95 response time ≤ 2 seconds under normal load
- [ ] Token delivery end-to-end ≤ 10 seconds (measured in staging)
- [ ] Payment webhook processing ≤ 3 seconds

### Security Gates
- [ ] Penetration testing completed; critical/high findings resolved
- [ ] All API endpoints require authentication (no unprotected routes)
- [ ] Payment data never stored server-side (PCI compliance)
- [ ] All sensitive data encrypted at rest and in transit

### Operational Gates
- [ ] Monitoring and alerting configured (Datadog / Sentry / equivalent)
- [ ] Admin dashboard accessible and functional for operations team
- [ ] Runbook documented for common operational issues
- [ ] Backup and recovery procedures tested

---

## 14. Milestones & Timeline

| Milestone | Deliverable | Target Duration |
|-----------|------------|----------------|
| **M1: Foundation** | Project setup, auth, DB schema, CI/CD pipeline | Week 1–2 |
| **M2: Core API** | Meter validation, DISCO integration, transaction model | Week 3–4 |
| **M3: Payments** | Paystack + Flutterwave integration, webhook handling | Week 5–6 |
| **M4: Token Delivery** | Token request, async retry, notification delivery | Week 7–8 |
| **M5: Mobile App** | React Native app (all consumer screens) | Week 5–9 |
| **M6: Admin Dashboard** | React admin: monitoring, reporting, issue resolution | Week 8–10 |
| **M7: QA & Testing** | Unit tests, integration tests, load testing, UAT | Week 10–12 |
| **M8: Security & Compliance** | Pen test, security review, legal sign-off | Week 11–12 |
| **M9: Production Launch** | Soft launch with limited users | Week 13 |

> **Estimated Total Duration:** 13 weeks (~3 months) from kickoff to soft launch.

---

## 15. Assumptions & Constraints

### Assumptions
- DISCOs will provide authorized, documented API access and sandbox environments before development begins
- Paystack and/or Flutterwave merchant accounts are approved and active
- All users have valid prepaid electricity meters registered with a DISCO
- SMS gateway service is procured before notification feature testing
- Cloud infrastructure is provisioned in advance of M1 milestone
- Legal and regulatory review is conducted in parallel with development

### Constraints
- MVP must launch within 13 weeks of kickoff
- MVP platform supports only **Nigerian DISCOs** (IBEDC, EKEDC, AEDC, etc.) initially
- Minimum purchase amount is determined by DISCO APIs (typically ₦500+)
- Token format and structure are dictated by DISCO standards (non-negotiable)
- The platform acts as an **intermediary only** — it does not store payment card data

---

*This MVP document is a living document. It should be updated after each sprint review and validated against actual user feedback post-launch.*

---

**Document Approvals**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Manager | | | |
| Tech Lead | | | |
| QA Lead | | | |
| Business Stakeholder | | | |
