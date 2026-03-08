# Electricity Token Intermediary Platform (ETIP)
# Product Requirements Document (PRD)

> **Document Type:** Product Requirements Document (PRD)  
> **Version:** 1.0  
> **Date:** February 22, 2026  
> **Status:** Draft — Pending Review  
> **Product Name:** Electricity Token Intermediary Platform (ETIP)  
> **Product Manager:** [Name]  
> **Engineering Lead:** [Name]  
> **Last Reviewed By:** [Name]  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Business Context & Opportunity](#2-business-context--opportunity)
3. [Product Vision & Strategy](#3-product-vision--strategy)
4. [Stakeholders & Users](#4-stakeholders--users)
5. [Product Goals & KPIs](#5-product-goals--kpis)
6. [Feature Requirements](#6-feature-requirements)
7. [Functional Requirements (Detailed)](#7-functional-requirements-detailed)
8. [Non-Functional Requirements (NFRs)](#8-non-functional-requirements-nfrs)
9. [System Architecture](#9-system-architecture)
10. [API Specifications (Overview)](#10-api-specifications-overview)
11. [Data Requirements](#11-data-requirements)
12. [Security Requirements](#12-security-requirements)
13. [UX & Accessibility Requirements](#13-ux--accessibility-requirements)
14. [Integration Requirements](#14-integration-requirements)
15. [Compliance & Regulatory Requirements](#15-compliance--regulatory-requirements)
16. [Analytics & Observability Requirements](#16-analytics--observability-requirements)
17. [Release Strategy](#17-release-strategy)
18. [Product Roadmap](#18-product-roadmap)
19. [Dependencies](#19-dependencies)
20. [Risks & Mitigations](#20-risks--mitigations)
21. [Open Questions & Decisions Log](#21-open-questions--decisions-log)
22. [Glossary](#22-glossary)
23. [Revision History](#23-revision-history)

---

## 1. Executive Summary

**ETIP** (Electricity Token Intermediary Platform) is a digital-first platform that enables consumers to purchase prepaid electricity tokens seamlessly via mobile and web, through an authorized intermediary connected to Nigeria's electricity distribution companies (DISCOs).

The platform addresses a critical gap: while prepaid electricity meters are widely deployed, the token purchase experience remains predominantly manual, slow, and friction-heavy. ETIP bridges this gap by providing a reliable, scalable, and compliant digital distribution layer between consumers and utility providers.

### Key Value Propositions

| For Consumers | For Operators / Admins | For DISCOs |
|---------------|----------------------|------------|
| 24/7 token purchases from any device | Full transaction visibility and control | A scalable digital distribution channel |
| Token delivery in under 10 seconds | Real-time monitoring and anomaly detection | Reduced physical vending overhead |
| Secure payments via trusted gateways | Automated reconciliation and reporting | API-based integration with authorized partner |
| Full transaction history and receipts | Manual resolution tools for edge cases | Regulatory-compliant data handling |

### Platform Scope Summary

| Scope Item | MVP (Phase 1) | Phase 2 | Phase 3 |
|-----------|--------------|---------|---------|
| Token purchase via mobile/web | ✅ | ✅ | ✅ |
| Paystack / Flutterwave payments | ✅ | ✅ | ✅ |
| Admin dashboard | ✅ | ✅ | ✅ |
| AI-based customer support | ❌ | ✅ | ✅ |
| Reseller/agent portal | ❌ | ✅ | ✅ |
| Smart meter remote injection | ❌ | ❌ | ✅ |

---

## 2. Business Context & Opportunity

### 2.1 Market Context

Nigeria operates one of the largest prepaid electricity metering systems in Africa, with millions of prepaid meters deployed across residential and commercial customers served by 11 licensed DISCOs. Despite this scale, the vast majority of token purchases still occur through:

- Physical vending kiosks and agents
- Bank teller-assisted transactions
- USSD short codes (limited and error-prone)

This creates significant friction for customers, especially during emergencies, nights, or when physical access to vending points is limited.

### 2.2 Business Opportunity

A digital intermediary platform capturing even a small percentage of daily token transactions at scale represents significant revenue potential:

- Estimated daily national prepaid token transactions: **1M+**
- Average transaction value: **₦2,000 – ₦10,000**
- Intermediary service fee potential: **0.5% – 1.5% per transaction**

### 2.3 Competitive Landscape

| Competitor Type | Examples | ETIP Differentiator |
|----------------|----------|---------------------|
| Bank apps | GTBank, Zenith | ETIP is purpose-built for electricity; faster, simpler UX |
| Utility portals | DISCO self-service sites | ETIP aggregates multiple DISCOs in one platform |
| Fintech apps | OPay, PalmPay | ETIP provides deeper electricity-specific features (history, meter profiles, resend) |
| USSD services | *Short code services* | ETIP offers richer UX, history, and notifications |

---

## 3. Product Vision & Strategy

### 3.1 Vision Statement

> *"To become the most trusted and fastest electricity token distribution platform in Nigeria, empowering every household to stay powered — anytime, anywhere."*

### 3.2 Product Strategy

| Strategic Pillar | Description |
|-----------------|-------------|
| **Speed** | Sub-10-second token delivery as a non-negotiable standard |
| **Reliability** | 99%+ token delivery success rate; graceful handling of all failure modes |
| **Trust** | Transparent transactions, instant receipts, and secure payments |
| **Scalability** | Architecture designed to handle millions of transactions with horizontal scaling |
| **Extensibility** | API-first design enabling future integrations (smart meters, AI, USSD) |

### 3.3 Product Phases

```
Phase 1 (MVP) ──────────► Phase 2 ──────────────► Phase 3
[Now → Q2 2026]            [Q3–Q4 2026]             [2027+]

Core token purchase        AI & automation          Smart meter
Consumer app               Agent/reseller portal    Remote injection
Admin dashboard            USSD channel             Deep DISCO integration
2 payment gateways         Wallet top-up            Regulatory expansion
Multi-DISCO support        WhatsApp bot             Multi-country
```

---

## 4. Stakeholders & Users

### 4.1 Stakeholder Map

| Stakeholder | Role | Interest Level | Influence |
|-------------|------|---------------|-----------|
| CEO / Founder | Executive sponsor | High | High |
| Product Manager | Requirements owner | High | High |
| Engineering Lead | Technical delivery | High | High |
| Operations Team | Admin dashboard users | High | Medium |
| Finance / Compliance | Regulatory & financial oversight | Medium | High |
| DISCO Partners | External API providers | High | High |
| Paystack / Flutterwave | Payment gateway providers | Medium | Medium |
| End Consumers | Primary product users | High | Low |
| Regulatory Bodies (CBN, NERC) | Compliance enforcers | Low (daily) | Very High |

### 4.2 User Personas

#### Persona 1: Adaeze — The Busy Professional
- **Age:** 32 | **Location:** Lagos, Nigeria
- **Meter Type:** Prepaid residential (EKEDC)
- **Behavior:** Purchases tokens once or twice a month via her phone
- **Pain Point:** Has to use her bank app, which is slow and not optimized for electricity tokens
- **Goal:** "I want to buy electricity in 30 seconds without leaving my current app"
- **Tech Comfort:** High — uses multiple apps daily

#### Persona 2: Musa — The Small Business Owner
- **Age:** 45 | **Location:** Kano, Nigeria
- **Meter Type:** Prepaid commercial (AEDC)
- **Behavior:** Purchases tokens weekly in larger amounts
- **Pain Point:** Receipts are informal; hard to track for accounting
- **Goal:** "I need formal receipts and transaction history for my business"
- **Tech Comfort:** Medium — uses phone for payments but prefers simple UX

#### Persona 3: Kemi — The Operations Analyst
- **Age:** 28 | **Location:** Abuja, Nigeria
- **Role:** Platform Admin / Operator
- **Behavior:** Monitors transactions, handles escalations, generates reports
- **Pain Point:** Current manual reconciliation is error-prone and time-consuming
- **Goal:** "I need a dashboard where I can see everything in real time and resolve issues fast"
- **Tech Comfort:** High — comfortable with complex dashboards and data

---

## 5. Product Goals & KPIs

### 5.1 Business Goals

| Goal | Metric | MVP Target | 12-Month Target |
|------|--------|-----------|----------------|
| Drive transaction volume | Total monthly transactions | 1,000 | 100,000 |
| Achieve reliability | Token delivery success rate | ≥ 99% | ≥ 99.5% |
| Deliver speed | Avg. token delivery time | ≤ 10s | ≤ 5s |
| Minimize payment errors | Payment failure rate | ≤ 1% | ≤ 0.5% |
| Grow user base | Monthly Active Users (MAU) | 200 | 20,000 |
| Generate revenue | Monthly gross transaction value | ₦1M | ₦200M |

### 5.2 Product KPIs (Operational)

| KPI | Definition | Target |
|-----|-----------|--------|
| Token Delivery Success Rate | Tokens delivered / Confirmed payments | ≥ 99% |
| Payment Success Rate | Successful payments / Total payment attempts | ≥ 99% |
| Time to Token (p50) | Median time from payment confirm to token display | ≤ 8s |
| Time to Token (p95) | 95th percentile token delivery time | ≤ 15s |
| System Uptime | % time backend is available | ≥ 99.5% |
| API Latency (p95) | 95th percentile API response time | ≤ 2s |
| Admin Resolution Time | Avg. time to resolve a flagged transaction | ≤ 4 hours |
| App Crash Rate | App crashes / Sessions | < 0.5% |
| D30 User Retention | Users active at 30 days / Users registered | ≥ 30% |

---

## 6. Feature Requirements

### 6.1 Feature Priority Matrix

| Feature | Priority | Phase | Complexity | Value |
|---------|----------|-------|-----------|-------|
| User Registration & Auth | P0 | MVP | Medium | Critical |
| Meter Number Validation | P0 | MVP | Medium | Critical |
| DISCO Provider Selection | P0 | MVP | Low | Critical |
| Token Purchase Flow | P0 | MVP | High | Critical |
| Payment Processing (Paystack/Flutterwave) | P0 | MVP | High | Critical |
| Token Display & In-App Notification | P0 | MVP | Medium | Critical |
| SMS Token Fallback | P0 | MVP | Low | High |
| Transaction History & Receipts | P0 | MVP | Medium | High |
| Admin: Transaction Monitoring | P0 | MVP | Medium | Critical |
| Admin: User Management | P0 | MVP | Low | High |
| Admin: Reporting & Reconciliation | P0 | MVP | Medium | High |
| Admin: Manual Token Resend | P0 | MVP | Medium | High |
| Wallet / Balance Top-Up | P2 | Phase 2 | High | Medium |
| AI Customer Support Bot | P2 | Phase 2 | Very High | Medium |
| Reseller / Agent Portal | P2 | Phase 2 | High | Medium |
| USSD Channel | P2 | Phase 2 | High | Medium |
| WhatsApp Integration | P2 | Phase 2 | Medium | Low |
| Smart Meter Remote Injection | P3 | Phase 3 | Very High | High |

> **Priority Legend:** P0 = Must Have (MVP Blocker) | P1 = Should Have | P2 = Nice to Have | P3 = Future

---

## 7. Functional Requirements (Detailed)

### 7.1 Authentication & User Management

#### FR-AUTH-001: User Registration
- **Description:** New users shall be able to create an account using a phone number or email address
- **Precondition:** User is not already registered
- **Flow:**
  1. User enters phone number or email
  2. System validates format and checks for duplicates
  3. OTP is sent to phone (SMS) or email
  4. User enters OTP to verify identity
  5. User sets a password (min 8 chars, 1 uppercase, 1 number, 1 special char)
  6. Account is created; JWT tokens issued
- **Business Rules:**
  - OTP is 6 digits, valid for 5 minutes, one resend per 60 seconds
  - Maximum 5 failed OTP attempts before 15-minute lockout
  - Phone number must be a valid Nigerian number (+234 format)

#### FR-AUTH-002: User Login
- **Description:** Registered users shall be able to log in securely
- **Flow:**
  1. User enters phone/email + password
  2. System validates credentials
  3. On success: JWT access token (15 min) + refresh token (30 days) issued
  4. On failure: Error shown; 5 consecutive failures triggers 15-minute account lockout
- **Business Rules:**
  - Refresh token rotation on each use
  - Forced re-authentication after 30 days of inactivity

#### FR-AUTH-003: Password Reset
- **Description:** Users shall be able to reset their password via OTP verification
- **Flow:** Enter phone/email → OTP sent → OTP verified → new password set
- **Business Rules:** Password reset link/OTP valid for 10 minutes; previous sessions invalidated on reset

#### FR-AUTH-004: Admin Authentication
- **Description:** Admin users shall authenticate via email and password
- **Business Rules:**
  - Admin accounts created manually by Super Admin only (no self-registration)
  - Mandatory MFA (TOTP) for all Admin accounts
  - All admin login events logged in AuditLog

---

### 7.2 Meter Management

#### FR-METER-001: Meter Number Validation
- **Description:** The system shall validate a meter number against the selected DISCO's API before any payment is processed
- **Flow:**
  1. User selects DISCO provider
  2. User enters meter number
  3. System calls DISCO validation API
  4. On success: Meter owner name and address returned and displayed to user for confirmation
  5. On failure: User-friendly error displayed; payment option hidden
- **Business Rules:**
  - Validation is **mandatory** and cannot be skipped
  - Validation result cached for 30 minutes to reduce API calls
  - Timeout after 5 seconds → show retry option; do not allow payment
  - Maximum 3 validation retries before showing "Service temporarily unavailable"

#### FR-METER-002: Meter Profile Management
- **Description:** Users shall be able to save frequently used meter numbers as named profiles
- **Business Rules:**
  - Maximum 5 saved meter profiles per user account
  - Each profile has a user-defined nickname (e.g., "Home", "Office")
  - Default meter profile pre-selected on token purchase screen
  - Saved profiles are validated against DISCO API once at save time

---

### 7.3 Token Purchase Flow

#### FR-TOKEN-001: Purchase Amount Selection
- **Description:** Users shall select or input a purchase amount within DISCO-defined limits
- **Business Rules:**
  - Minimum amount: ₦500 (or DISCO-defined minimum)
  - Maximum amount: ₦100,000 per transaction
  - System displays estimated kWh equivalent (if DISCO API provides tariff data)
  - Convenience amounts offered as quick-select options (₦1,000 / ₦2,000 / ₦5,000)

#### FR-TOKEN-002: Pre-Payment Confirmation
- **Description:** A confirmation screen shall be shown before initiating payment
- **Required Display Elements:**
  - Meter number (masked: show first 3 and last 3 digits)
  - Meter owner name
  - DISCO provider name
  - Purchase amount
  - Service fee (if applicable)
  - Total amount to be charged
  - Payment method selected

#### FR-TOKEN-003: Token Generation
- **Description:** Upon confirmed payment, the system shall request a token from the DISCO API
- **Flow:**
  1. Payment webhook received (server-side) → transaction marked Payment Success
  2. DISCO Token Request API called with payment reference and meter details
  3. Token returned synchronously OR polled asynchronously
  4. On token receipt: stored (encrypted), displayed to user, notification sent
  5. On DISCO failure: transaction flagged, admin alerted, async retry job queued
- **Business Rules:**
  - Token generation must be initiated within **3 seconds** of payment confirmation
  - DISCO API timeout: 8 seconds; retry up to 3 times with exponential backoff
  - If all retries fail: transaction status = "Token Failed"; admin resolution required
  - Token is stored encrypted in the database; never logged in plain text

#### FR-TOKEN-004: Token Display
- **Description:** The generated token shall be displayed clearly to the user
- **Business Rules:**
  - Token displayed as a formatted string (e.g., `1234-5678-9012-3456-7890`)
  - "Copy to Clipboard" button provided
  - User reminded to enter token into physical meter immediately
  - Token remains accessible in transaction history indefinitely

---

### 7.4 Payment Processing

#### FR-PAY-001: Payment Gateway Integration
- **Description:** The system shall support payments via Paystack and Flutterwave
- **Business Rules:**
  - Payment is initiated client-side via gateway SDK, but **confirmed server-side via webhook only**
  - Client-side payment success callbacks are treated as informational only, never as authoritative
  - Idempotency keys generated per transaction to prevent double charges
  - A transaction cannot proceed to token generation without verified server-side payment confirmation

#### FR-PAY-002: Payment Status Management
- **Description:** The system shall track and communicate payment status accurately
- **States:** `PENDING → SUCCESS | FAILED | EXPIRED`
- **Business Rules:**
  - Payment session expires after 10 minutes of inactivity
  - User notified immediately of payment success or failure
  - On payment failure: user may retry payment without re-entering meter details
  - Failed payments are never charged; system verifies via gateway API if webhook is delayed

#### FR-PAY-003: Refund Policy (MVP — Admin-Controlled)
- **Description:** In cases where payment succeeds but token delivery permanently fails, refunds are processed manually by admins in MVP
- **Business Rules:**
  - No automated refunds in MVP
  - Admin logs refund decision against transaction with reason code
  - Refund notification sent to user (push + email)
  - Phase 2 will introduce automated refund workflows

---

### 7.5 Transaction Management

#### FR-TXN-001: Transaction Logging
- **Description:** Every transaction event shall be logged with full audit trail
- **Required Log Fields:** Transaction ID, user ID, meter number (encrypted), DISCO, amount, payment gateway, payment reference, DISCO reference, payment status, token status, all timestamps, IP address, device info

#### FR-TXN-002: Transaction History (Consumer)
- **Description:** Users shall be able to view their complete transaction history
- **Business Rules:**
  - Paginated: 20 transactions per page, reverse chronological
  - Filterable by: date range, DISCO, status
  - Each transaction shows: date, amount, meter, DISCO, token (if delivered), status
  - Receipt downloadable as PDF

#### FR-TXN-003: Transaction Monitoring (Admin)
- **Description:** Admins shall view all platform transactions in real time
- **Business Rules:**
  - Dashboard refreshes every 30 seconds (or WebSocket for live updates)
  - Filters: date range, status, DISCO, user ID, meter number, gateway
  - Color-coded status indicators
  - Exportable to CSV/Excel with all fields (sensitive fields masked unless Super Admin)

---

### 7.6 Admin Features

#### FR-ADMIN-001: User Management
- **Description:** Admins shall be able to view, search, and manage user accounts
- **Capabilities:**
  - Search users by name, phone, email
  - View user profile, registered meters, and full transaction history
  - Suspend or reactivate user accounts with reason logging
  - View failed login attempts and security events

#### FR-ADMIN-002: Manual Token Resend
- **Description:** Operators shall be able to manually trigger token delivery for failed token transactions
- **Business Rules:**
  - Only available for transactions in `Payment Success / Token Failed` state
  - Resend calls DISCO API with original payment reference
  - Result logged with operator ID, timestamp, and outcome
  - Maximum 3 manual resend attempts per transaction before escalation required

#### FR-ADMIN-003: Reporting
- **Description:** Admins shall generate summary and detailed reports
- **Report Types:**
  - Transaction Volume Report (count, value, by DISCO, by status)
  - Financial Reconciliation Report (gateway charges vs. tokens issued)
  - User Activity Report (new signups, active users, transaction frequency)
  - Failure Analysis Report (failed transactions, root cause categorization)
- **Export Formats:** CSV, Excel (XLSX), PDF

#### FR-ADMIN-004: Audit Log
- **Description:** All admin actions shall be logged in a non-editable audit trail
- **Logged Events:** Login/logout, user suspension, token resend, report export, data export, configuration changes
- **Business Rules:**
  - Audit log is read-only; no admin (including Super Admin) can delete entries
  - Log retained for minimum 2 years

---

## 8. Non-Functional Requirements (NFRs)

### 8.1 Performance

| Requirement | Specification |
|-------------|--------------|
| API Response Time (p50) | ≤ 500ms under normal load |
| API Response Time (p95) | ≤ 2 seconds under normal load |
| API Response Time (p99) | ≤ 5 seconds under peak load |
| Token Delivery Time (p50) | ≤ 8 seconds end-to-end |
| Token Delivery Time (p95) | ≤ 15 seconds end-to-end |
| Concurrent Transaction Support | ≥ 500 simultaneous transactions without degradation |
| Peak Load (throughput) | ≥ 1,000 transactions per minute sustained |
| Database Query Time (p95) | ≤ 100ms for indexed queries |

### 8.2 Availability & Reliability

| Requirement | Specification |
|-------------|--------------|
| System Uptime SLA | ≥ 99.5% monthly (≤ 3.65 hours downtime/month) |
| Admin Dashboard Uptime | ≥ 99.9% monthly |
| Planned Maintenance Window | Off-peak hours only (02:00–04:00 WAT); max 30 min/month |
| Recovery Time Objective (RTO) | ≤ 30 minutes for critical system components |
| Recovery Point Objective (RPO) | ≤ 5 minutes (database backup frequency) |
| DISCO API Retry Policy | Up to 3 retries with exponential backoff (2s, 4s, 8s) |
| Payment Webhook Retry | Up to 5 retries if webhook not acknowledged within 10 seconds |

### 8.3 Scalability

| Requirement | Specification |
|-------------|--------------|
| Horizontal Scaling | Backend services shall scale horizontally via container orchestration |
| Database Scaling | Read replicas for reporting queries; primary DB for writes |
| Caching | Redis caching for meter validation results, DISCO rate limits, session data |
| Stateless API | All API endpoints stateless; no server-side session state |
| CDN | Static assets (mobile app bundles, admin app) served via CDN |
| Queue-Based Processing | Token generation and notifications processed asynchronously via task queue |

### 8.4 Security

| Requirement | Specification |
|-------------|--------------|
| Authentication | JWT-based with access/refresh token rotation |
| Authorization | Role-based access control (RBAC) for all protected resources |
| Transport Security | TLS 1.2+ on all API and webhook endpoints (HTTPS only) |
| Data Encryption at Rest | AES-256 for sensitive fields (tokens, meter numbers, personal data) |
| Password Storage | Bcrypt hashing with per-user salt (cost factor ≥ 12) |
| PCI Compliance | Card data never stored on platform; all card handling by certified gateway |
| Input Validation | All user inputs validated server-side; parameterized queries only (no raw SQL) |
| Rate Limiting | Per-IP and per-user rate limits on all public endpoints |
| Brute Force Protection | Account lockout after 5 consecutive failed login attempts |
| API Security | API keys rotated regularly; DISCO API credentials stored in secret manager |
| Audit Logging | All authentication events and admin actions logged immutably |
| Dependency Scanning | Automated CVE scanning of all dependencies in CI/CD pipeline |

### 8.5 Maintainability

| Requirement | Specification |
|-------------|--------------|
| Code Coverage | Minimum 80% unit test coverage on backend business logic |
| Documentation | All public API endpoints documented in OpenAPI 3.0 spec |
| Linting & Formatting | Enforced via pre-commit hooks (Black, Flake8 for Python; ESLint for JS) |
| CI/CD | Automated build, test, and deployment pipeline for all environments |
| Environment Parity | Staging environment mirrors production configuration |
| Logging | Structured JSON logs with correlation IDs across all services |

### 8.6 Compatibility

| Requirement | Specification |
|-------------|--------------|
| Mobile OS: Android | Android 8.0 (API 26) and above |
| Mobile OS: iOS | iOS 13 and above |
| Web Admin: Browsers | Chrome 90+, Firefox 88+, Edge 90+, Safari 14+ |
| Screen Sizes (Mobile) | 360dp – 428dp width supported |
| Network Conditions | Functional on 3G network (minimum); optimized for 4G |

---

## 9. System Architecture

### 9.1 Logical Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                            │
│  ┌──────────────────────────┐      ┌───────────────────────────────────┐│
│  │   Mobile App              │      │   Web Admin Dashboard              ││
│  │   React Native            │      │   React.js + TailwindCSS          ││
│  │   iOS + Android           │      │   Role-Based UI                   ││
│  └──────────────┬───────────┘      └─────────────────┬─────────────────┘│
└─────────────────┼───────────────────────────────────┼───────────────────┘
                  │ REST API (HTTPS)                   │ REST API (HTTPS)
┌─────────────────┼───────────────────────────────────┼───────────────────┐
│                 │         APPLICATION LAYER           │                   │
│  ┌──────────────▼─────────────────────────────────────▼──────────────┐  │
│  │                    API Gateway / Load Balancer                      │  │
│  └──────────────────────────────┬───────────────────────────────────┘  │
│                                  │                                       │
│  ┌───────────────────────────────▼────────────────────────────────────┐ │
│  │              Django REST Framework (Core API)                        │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │ │
│  │  │  Auth    │ │  Meter   │ │ Payment  │ │  Token   │ │  Admin  │ │ │
│  │  │  Service │ │  Service │ │  Service │ │  Service │ │  Service│ │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └─────────┘ │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                  │                                       │
│  ┌───────────────────────────────▼────────────────────────────────────┐ │
│  │                   Celery Task Queue (Redis Broker)                   │ │
│  │       Workers: Token Retry | Notification Dispatch | Reports         │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
         │               │              │              │
┌────────▼──────┐ ┌──────▼──────┐ ┌───▼─────────┐ ┌─▼───────────────────┐
│  PostgreSQL   │ │   Redis     │ │ DISCO APIs  │ │ Payment Gateways    │
│  Primary DB   │ │   Cache +   │ │ (Per DISCO) │ │ Paystack            │
│  Read Replica │ │   Queue     │ │             │ │ Flutterwave         │
└───────────────┘ └─────────────┘ └─────────────┘ └─────────────────────┘
                                                    ┌──────────────────────┐
                                                    │ Notification Services│
                                                    │ FCM (Push)           │
                                                    │ SMS Gateway          │
                                                    └──────────────────────┘
```

### 9.2 Deployment Architecture

| Component | Hosting | Scaling Strategy |
|-----------|---------|-----------------|
| API Backend | Cloud (AWS ECS / GCP Cloud Run) | Auto-scaling containers |
| Admin Frontend | Cloud Storage + CDN | Static hosting |
| Mobile App | App Store / Google Play | N/A |
| Database | Managed PostgreSQL (RDS / Cloud SQL) | Read replicas |
| Cache / Queue | Managed Redis (ElastiCache / Memorystore) | Clustered |
| Task Workers | Cloud container instances | Scale with queue depth |
| File Storage | Cloud Object Storage (S3 / GCS) | Unlimited |
| Monitoring | Datadog / Sentry | SaaS |

---

## 10. API Specifications (Overview)

### 10.1 API Design Principles

- **Style:** RESTful JSON API
- **Versioning:** URL path versioning (`/api/v1/`)
- **Authentication:** Bearer token (JWT) on all protected endpoints
- **Response Format:** Consistent envelope: `{ "status": "success|error", "data": {}, "message": "" }`
- **HTTP Status Codes:** Semantically correct (200, 201, 400, 401, 403, 404, 422, 429, 500)
- **Documentation:** OpenAPI 3.0 spec auto-generated and hosted at `/api/docs/`

### 10.2 Core API Endpoint Groups

#### Authentication Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/register/` | Register new user | Public |
| POST | `/api/v1/auth/verify-otp/` | Verify OTP | Public |
| POST | `/api/v1/auth/login/` | User login | Public |
| POST | `/api/v1/auth/token/refresh/` | Refresh access token | Public (Refresh Token) |
| POST | `/api/v1/auth/logout/` | Invalidate refresh token | Auth |
| POST | `/api/v1/auth/password-reset/` | Initiate password reset | Public |
| POST | `/api/v1/auth/password-reset/confirm/` | Confirm password reset | Public |

#### Meter Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/meters/validate/` | Validate meter number against DISCO | Auth |
| GET | `/api/v1/meters/profiles/` | List saved meter profiles | Auth |
| POST | `/api/v1/meters/profiles/` | Save a new meter profile | Auth |
| PUT | `/api/v1/meters/profiles/{id}/` | Update a meter profile | Auth |
| DELETE | `/api/v1/meters/profiles/{id}/` | Delete a meter profile | Auth |

#### Transaction / Purchase Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/transactions/initiate/` | Initiate a token purchase transaction | Auth |
| POST | `/api/v1/transactions/payment/initialize/` | Initialize payment with gateway | Auth |
| POST | `/api/v1/webhooks/paystack/` | Paystack payment webhook | HMAC |
| POST | `/api/v1/webhooks/flutterwave/` | Flutterwave payment webhook | Signature |
| GET | `/api/v1/transactions/` | List user transactions (paginated) | Auth |
| GET | `/api/v1/transactions/{id}/` | Get transaction detail | Auth |
| GET | `/api/v1/transactions/{id}/receipt/` | Download transaction receipt (PDF) | Auth |

#### Admin Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/admin/transactions/` | List all transactions (filtered) | Admin |
| GET | `/api/v1/admin/transactions/{id}/` | Transaction detail (full) | Admin |
| POST | `/api/v1/admin/transactions/{id}/resend-token/` | Manually resend token | Admin |
| POST | `/api/v1/admin/transactions/{id}/resolve/` | Mark transaction resolved | Admin |
| GET | `/api/v1/admin/users/` | List all users | Admin |
| GET | `/api/v1/admin/users/{id}/` | User detail + transactions | Admin |
| PATCH | `/api/v1/admin/users/{id}/status/` | Suspend or activate user | Admin |
| GET | `/api/v1/admin/reports/summary/` | Transaction summary report | Admin |
| GET | `/api/v1/admin/reports/reconciliation/` | Reconciliation report | Admin |
| GET | `/api/v1/admin/audit-log/` | View audit log | Super Admin |

### 10.3 DISCO API Integration Contract (Expected)

| Operation | Method | Description |
|-----------|--------|-------------|
| Meter Validation | GET | `?meter_number=X&disco=Y` → returns owner info |
| Token Request | POST | `{ meter_number, amount, payment_ref }` → returns token |
| Token Status Poll | GET | `?request_id=X` → returns token or pending/error status |

> **Note:** Exact DISCO API contracts will be documented separately per DISCO partner in a DISCO Integration Specification document.

---

## 11. Data Requirements

### 11.1 Data Classification

| Data Type | Classification | Storage Requirement |
|-----------|---------------|-------------------|
| User PII (name, phone, email) | Confidential | Encrypted at rest |
| Meter numbers | Confidential | Encrypted at rest |
| Token values | Highly Confidential | AES-256 encrypted; access-controlled |
| Payment references | Confidential | Encrypted at rest |
| Transaction amounts | Internal | Stored in plain; access-controlled |
| Audit logs | Internal | Read-only; 2-year retention |
| Card data | PCI Restricted | Never stored on platform |

### 11.2 Data Retention Policy

| Data Type | Retention Period | Deletion Policy |
|-----------|----------------|----------------|
| User account data | Duration of account + 7 years | Anonymized on account deletion |
| Transaction records | 7 years | Archived after 2 years; deleted after 7 |
| Audit logs | 2 years minimum | Archived; not deleted |
| Session tokens | Access: 15 min / Refresh: 30 days | Auto-expired |
| DISCO API logs | 90 days | Auto-purged |
| Payment gateway logs | 7 years | Archived |

### 11.3 Data Privacy Requirements

- The platform shall comply with Nigeria Data Protection Act (NDPA) 2023
- Users shall be provided a Privacy Policy at registration
- Users may request data export (all their data) at any time
- Users may request account deletion; data is anonymized (not deleted) for legal compliance
- No user data is sold or shared with third parties except as required for service delivery (DISCOs, payment gateways)

---

## 12. Security Requirements

### 12.1 Authentication & Authorization

| Requirement | Detail |
|-------------|--------|
| Token Standard | JWT (RS256 signed); access token 15-min TTL; refresh token 30-day TTL |
| RBAC Roles | `consumer`, `operator`, `super_admin` |
| Endpoint Authorization | Every endpoint specifies required role; enforced at middleware level |
| Admin MFA | TOTP (Google Authenticator / Authy) mandatory for all admin accounts |
| Session Invalidation | All refresh tokens invalidated on password change or explicit logout |

### 12.2 Payment Security

| Requirement | Detail |
|-------------|--------|
| Webhook Verification | All payment webhooks verified using HMAC-SHA256 signature |
| Idempotency | All payment initiation requests use unique idempotency keys |
| No Card Data Storage | Platform is out of PCI scope; all card data handled by certified gateways |
| Amount Validation | Server-side validation of payment amount matches transaction amount (prevent tampering) |
| Double-Charge Prevention | Idempotency keys + database unique constraints prevent duplicate charges |

### 12.3 Infrastructure Security

| Requirement | Detail |
|-------------|--------|
| Network | Private VPC; database not exposed to public internet |
| Secrets Management | API keys, DB credentials, and secrets stored in cloud secret manager (not in code) |
| TLS | TLS 1.2 minimum on all external endpoints; HSTS headers enabled |
| DDoS Protection | Cloud provider DDoS protection + WAF at load balancer |
| Penetration Testing | Annual penetration test; critical/high findings resolved before each major release |
| Dependency Scanning | Automated in CI/CD pipeline; critical CVEs block deployment |
| Logging & Alerting | All security events (failed logins, admin actions) alert security channel within 5 minutes |

---

## 13. UX & Accessibility Requirements

### 13.1 Consumer App UX Requirements

| Requirement | Standard |
|-------------|---------|
| Onboarding Flow | ≤ 3 screens to complete registration |
| Time-to-First-Transaction | New user can complete first purchase in ≤ 5 minutes |
| Error Messages | All errors provide: what went wrong + what to do next |
| Loading States | All async operations show loading indicators; no blank screens |
| Offline Handling | Graceful messaging when network is unavailable; no data corruption |
| Token Copy UX | One-tap copy with visual confirmation; token displayed prominently |
| Form Validation | Inline validation (not only on submit); immediate feedback |

### 13.2 Admin Dashboard UX Requirements

| Requirement | Standard |
|-------------|---------|
| Table Loading | Large transaction tables paginated; loading skeleton shown |
| Search Response | Search results return within 2 seconds |
| Export Feedback | Export progress shown; user notified when download ready |
| Action Confirmation | Destructive actions (suspend user, resend token) require confirmation dialog |
| Data Freshness | Dashboard shows "Last updated X seconds ago" indicator |

### 13.3 Accessibility Requirements

| Requirement | Standard |
|-------------|---------|
| Color Contrast | WCAG 2.1 Level AA minimum (4.5:1 contrast ratio) |
| Touch Targets | Minimum 44×44dp for all interactive elements |
| Screen Reader | All interactive elements have accessible labels |
| Font Scaling | UI supports system font size scaling up to 200% |
| Error Identification | Errors not conveyed by color alone; text and icons used |

---

## 14. Integration Requirements

### 14.1 Payment Gateways

#### Paystack
- **Integration Type:** Server-side API + Client-side Inline JS/SDK
- **Authentication:** Secret key (server-side), Public key (client-side)
- **Key Events:** `charge.success`, `charge.failed`, `transfer.success`
- **Webhook URL:** `POST /api/v1/webhooks/paystack/`
- **Signature Verification:** `x-paystack-signature` header (HMAC-SHA512)
- **Sandbox:** Required for development and staging environments

#### Flutterwave
- **Integration Type:** Server-side API + Client-side Inline SDK
- **Authentication:** Secret key (server-side), Public key (client-side)
- **Key Events:** `charge.completed`, `charge.failed`
- **Webhook URL:** `POST /api/v1/webhooks/flutterwave/`
- **Signature Verification:** `verif-hash` header (static secret or HMAC)
- **Sandbox:** Required for development and staging environments

### 14.2 DISCO APIs

#### General Requirements (Per DISCO)
- **Authentication:** API key or OAuth2 (per DISCO specification)
- **Environment:** Separate sandbox and production credentials
- **TLS:** All DISCO API calls over HTTPS only
- **Timeout:** 8-second timeout per request
- **Retry Policy:** Up to 3 retries with 2s/4s/8s exponential backoff
- **Error Handling:** Map DISCO error codes to platform-specific error types

#### DISCO Onboarding Checklist
- [ ] Signed API access agreement
- [ ] Sandbox credentials obtained
- [ ] Meter validation endpoint documented and tested
- [ ] Token request endpoint documented and tested
- [ ] Rate limits confirmed and respected
- [ ] Error code catalogue received

### 14.3 Notification Services

#### Firebase Cloud Messaging (FCM)
- **Use Case:** Primary push notification delivery
- **Trigger:** Token delivered, payment confirmation, account alerts
- **Fallback:** SMS via SMS Gateway if FCM token missing or delivery fails

#### SMS Gateway
- **Use Case:** Token delivery fallback; OTP delivery
- **Requirements:** Delivery confirmation tracking; sender ID approved (e.g., "ETIP")

---

## 15. Compliance & Regulatory Requirements

### 15.1 Financial Regulations (CBN)

| Requirement | Details |
|-------------|---------|
| Agent Authorization | Platform must operate under valid CBN framework for payment intermediaries |
| Transaction Reporting | Large transactions above regulatory threshold must be reported |
| AML/KYC | Basic KYC (phone OTP) for MVP; enhanced KYC for high-value transactions in Phase 2 |
| Consumer Protection | Clear receipts, dispute mechanism, and refund process required |

### 15.2 Utility Regulations (NERC)

| Requirement | Details |
|-------------|---------|
| DISCO Authorization | Platform must have written authorization from each DISCO for token vending |
| Token Standard | Tokens must comply with Standard Transfer Specification (STS) |
| Data Sharing | Customer meter data usage governed by DISCO data sharing agreement |

### 15.3 Data Protection (NDPA 2023)

| Requirement | Details |
|-------------|---------|
| Lawful Basis | Processing based on contract performance and legitimate interest |
| Data Subject Rights | Right to access, rectify, and request erasure (anonymization) |
| Privacy Notice | Clear privacy policy displayed at registration |
| Data Breach Notification | NDPC notified within 72 hours of a confirmed data breach |
| Data Localization | Consider whether NDPA requires Nigerian data residency |

---

## 16. Analytics & Observability Requirements

### 16.1 Application Monitoring

| Requirement | Tool | Alert Condition |
|-------------|------|----------------|
| API Error Rate | Sentry / Datadog | > 1% error rate → P1 alert |
| API Response Time | Datadog APM | p95 > 3s → Warning; > 5s → P1 alert |
| Token Delivery Success | Custom metric | < 99% hourly → P0 alert |
| System Uptime | UptimeRobot / Datadog | Any downtime > 1 min → Immediate alert |
| Queue Depth | Redis metrics | Queue depth > 100 jobs → Warning |
| Database Connections | PgBouncer metrics | Pool near exhaustion → Alert |

### 16.2 Business Analytics

| Metric | Frequency | Dashboard |
|--------|-----------|-----------|
| Daily Active Users | Real-time | Operations Dashboard |
| Transactions per hour | Real-time | Operations Dashboard |
| Transaction success rate | Real-time | Operations Dashboard |
| Revenue by DISCO | Daily | Finance Dashboard |
| Failed transaction rate | Real-time | Operations Dashboard |
| New user registrations | Daily | Growth Dashboard |
| Retention cohorts | Weekly | Product Dashboard |

### 16.3 Structured Logging

- All logs in JSON format with consistent fields: `timestamp`, `level`, `service`, `request_id`, `user_id` (where applicable), `message`, `metadata`
- Correlation IDs propagated across all service calls and async tasks
- Log levels: DEBUG (dev only), INFO, WARNING, ERROR, CRITICAL
- Logs shipped to centralized log management (e.g., Datadog Logs, CloudWatch)
- PII never logged in plain text (masked/excluded)

---

## 17. Release Strategy

### 17.1 Environment Strategy

| Environment | Purpose | Data | Auto-Deploy |
|-------------|---------|------|------------|
| Development | Feature development | Synthetic only | On push to feature branch |
| Staging | QA, UAT, integration testing | Anonymized production-like | On merge to `main` |
| Production | Live platform | Real | Manual approval gate |

### 17.2 Deployment Process

```
Feature Branch → PR Review → Merge to main →
CI: Tests + Linting + Security Scan → Auto-deploy to Staging →
QA Sign-off → Change Request Approval → Manual Deploy to Production →
Smoke Test → Monitor for 30 minutes → Release complete
```

### 17.3 Rollback Strategy

- All production deployments use **blue-green deployment** or **rolling updates**
- Rollback can be initiated within 5 minutes if critical error rate spikes post-deployment
- Database migrations must be **backward-compatible** (no breaking schema changes)
- Feature flags used for gradual feature rollout (avoid big-bang releases)

### 17.4 MVP Launch Plan

| Stage | Audience | Duration | Success Criteria |
|-------|----------|---------|-----------------|
| Internal Alpha | Team members only | 1 week | All critical flows work; no P0 bugs |
| Closed Beta | 50–100 invited users | 2 weeks | Token delivery ≥ 99%; NPS ≥ 40 |
| Soft Launch | Open registration, limited marketing | 4 weeks | MAU 200+; system stable |
| Full Launch | Full marketing campaign | Ongoing | MAU growth ≥ 20% month-over-month |

---

## 18. Product Roadmap

### Phase 1 — MVP (Q1–Q2 2026)

| Feature | Status |
|---------|--------|
| User authentication (registration, login, password reset) | Planned |
| Meter number validation | Planned |
| DISCO provider selection | Planned |
| Token purchase flow | Planned |
| Paystack + Flutterwave payment integration | Planned |
| Token display + push + SMS notification | Planned |
| Transaction history and receipts | Planned |
| Admin: transaction monitoring dashboard | Planned |
| Admin: user management | Planned |
| Admin: manual token resend | Planned |
| Admin: reporting and reconciliation | Planned |
| Core monitoring, alerting, and observability | Planned |

### Phase 2 — Intelligent Operations (Q3–Q4 2026)

| Feature | Description |
|---------|-------------|
| AI Customer Support Bot | NLP-based chat for common queries (token lookup, FAQ) |
| Automated Issue Triage | ML-based classification and routing of failed transactions |
| Wallet / Balance Top-Up | Pre-funded wallet for faster purchases |
| Reseller / Agent Portal | Sub-agent onboarding and commission management |
| USSD Channel | `*XXX#` USSD for feature-phone users |
| WhatsApp Bot | Token purchase via WhatsApp Business API |
| Enhanced KYC | BVN-linked identity verification for high-value users |
| Automated Refunds | Rule-based automated refund trigger for unresolvable failures |

### Phase 3 — Smart Meter Integration (2027+)

| Feature | Description |
|---------|-------------|
| Remote Unit Injection | Secure transmission of purchased units directly to smart meter |
| Smart Meter Dashboard | Real-time meter balance, usage analytics for consumers |
| Multi-Country Expansion | Support for DISCOs in other African markets |
| Hardware API Integration | Integration with smart meter hardware APIs (DISCO-dependent) |

---

## 19. Dependencies

### External Dependencies

| Dependency | Type | Risk | Contingency |
|-----------|------|------|-------------|
| DISCO API Access | Critical | High | Staged launch per DISCO; mock API in dev/staging |
| Paystack Approval | Critical | Low | Flutterwave as fallback; both targeted for MVP |
| Flutterwave Approval | High | Low | Paystack as fallback |
| SMS Gateway | High | Low | Multiple providers evaluated; redundant provider |
| FCM (Firebase) | High | Very Low | SMS as fallback for notifications |
| Cloud Infrastructure | Critical | Very Low | Managed services with SLA ≥ 99.9% |

### Internal Dependencies

| Dependency | Owner | Risk |
|-----------|-------|------|
| DISCO API contracts finalized | Business/Legal | High |
| CBN regulatory clearance | Legal | High |
| Payment gateway merchant accounts | Finance | Medium |
| UI/UX design completion | Design | Medium |
| Backend API ready for mobile integration | Engineering | Low |

---

## 20. Risks & Mitigations

| Risk | Category | Likelihood | Impact | Mitigation Strategy | Owner |
|------|----------|-----------|--------|---------------------|-------|
| DISCO API unavailable or unstable | Technical | Medium | Critical | Retry logic; fallback queue; admin alerts; SLA in contract | Engineering |
| Payment gateway outage | Technical | Low | Critical | Dual gateway (Paystack + Flutterwave); auto-failover | Engineering |
| Token double-generation (user charged twice) | Technical | Low | Critical | Idempotency keys; transaction state machine; DB constraints | Engineering |
| DISCO delays token issuance > 30s | Technical | Medium | High | Async polling with user "processing" state; admin visibility | Engineering |
| Regulatory change (CBN/NERC) | Regulatory | Low | Critical | Legal monitoring; modular architecture for compliance updates | Legal/Product |
| Data breach (user or payment data) | Security | Low | Critical | Encryption, pen testing, access control, breach response plan | Engineering/Security |
| Fraudulent transactions | Fraud | Medium | High | OTP verification, rate limiting, anomaly detection alerts | Engineering/Operations |
| DISCO rejects API partnership | Business | Medium | Critical | Engage multiple DISCOs simultaneously; prioritize largest by user base | Business |
| Low user adoption post-launch | Market | Medium | High | Closed beta feedback loop; user interviews; quick iteration | Product |
| Scalability bottleneck at peak | Technical | Low | High | Load testing pre-launch; horizontal scaling; Redis caching | Engineering |

---

## 21. Open Questions & Decisions Log

| # | Question | Status | Decision | Date Decided |
|---|----------|--------|---------|-------------|
| 1 | Which DISCO APIs are available at MVP launch? | Open | — | — |
| 2 | Are we targeting Paystack or Flutterwave first, or both simultaneously? | Open | — | — |
| 3 | What is the platform's service fee per transaction? | Open | — | — |
| 4 | Should meter validation results be cached, and for how long? | Proposed | Cache for 30 min | Pending approval |
| 5 | Is SMS token delivery a hard requirement for MVP or nice-to-have? | Open | — | — |
| 6 | Do we need biometric authentication (FaceID/Fingerprint) for MVP? | Open | — | — |
| 7 | What is the refund processing time SLA for users? | Open | — | — |
| 8 | Will the platform support iOS at MVP launch or Android-only? | Open | — | — |
| 9 | Is data localization (Nigeria-only servers) required by NDPA? | Open | Legal review needed | — |
| 10 | Should admin dashboard require VPN access for additional security? | Open | — | — |

---

## 22. Glossary

| Term | Definition |
|------|-----------|
| **DISCO** | Distribution Company — licensed electricity distributor (e.g., EKEDC, AEDC, IBEDC) |
| **ETIP** | Electricity Token Intermediary Platform — the product being built |
| **STS** | Standard Transfer Specification — industry standard for prepaid electricity tokens |
| **Token** | A unique numeric code entered into a prepaid electricity meter to credit units |
| **MAU** | Monthly Active Users — users who complete at least one transaction per month |
| **KPI** | Key Performance Indicator — measurable value tracking product performance |
| **RTO** | Recovery Time Objective — maximum acceptable system downtime duration |
| **RPO** | Recovery Point Objective — maximum acceptable data loss window |
| **JWT** | JSON Web Token — standard for stateless API authentication |
| **RBAC** | Role-Based Access Control — permissions assigned based on user role |
| **HMAC** | Hash-based Message Authentication Code — used to verify webhook authenticity |
| **PCI** | Payment Card Industry — standards for secure card payment handling |
| **NDPA** | Nigeria Data Protection Act 2023 — Nigeria's primary data privacy legislation |
| **NERC** | Nigerian Electricity Regulatory Commission — electricity industry regulator |
| **CBN** | Central Bank of Nigeria — financial services regulator |
| **OTP** | One-Time Password — time-limited code for identity verification |
| **Idempotency Key** | A unique key ensuring a payment request is processed only once, even if retried |
| **p95 / p99** | 95th/99th percentile — statistical measure of worst-case performance |
| **Celery** | Python distributed task queue for async job processing |
| **FCM** | Firebase Cloud Messaging — Google's push notification service |
| **WAF** | Web Application Firewall — filters malicious HTTP traffic |
| **CDN** | Content Delivery Network — distributed server network for fast static asset delivery |

---

## 23. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | February 22, 2026 | Product Team | Initial draft — based on ETIP SRS v1.0 |
| | | | |
| | | | |

---

**Document Approvals**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Manager | | | |
| Engineering Lead | | | |
| QA Lead | | | |
| Legal / Compliance | | | |
| Business Stakeholder | | | |

---

*This PRD is a living document. Features, priorities, and requirements will evolve based on stakeholder feedback, technical discoveries, and market conditions. All changes must be tracked in the Revision History table.*
