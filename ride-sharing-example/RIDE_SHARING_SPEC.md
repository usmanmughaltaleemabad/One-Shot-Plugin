---
type: specification
project: ride-sharing-system
phase: one-shot-test-case
last_verified: 2026-05-25
owner: claude
---

# Ride-Sharing System (Uber-like) — Complete End-to-End Specification

**Goal:** Build a production-ready, enterprise-scale ride-sharing platform (like Uber) using the one-shot-prompting plugin in a single prompt. This validates plugin capability to handle complex domain modeling, multi-entity relationships, real-time operations, and payment integration.

**Success Criteria:** Plugin generates 95%+ working code; human intervention <5%; all core features operational in generated codebase.

---

## 1. System Architecture

### 1.1 Technology Stack
- **Backend:** Python (FastAPI or Django) with PostgreSQL
- **Real-time:** WebSocket/Socket.IO for live location tracking
- **Payment:** Stripe integration for payments and payouts
- **Geolocation:** Google Maps API (distance, routing, matching)
- **Authentication:** JWT tokens + OAuth2
- **Cache:** Redis for active rides, user sessions
- **Queue:** Celery for async jobs (notifications, matching)
- **Deployment:** Docker + Kubernetes ready

### 1.2 Core Entities (Domain Model)

**User (6 subtypes: Passenger, Driver, Admin, Support, Corporate, Payment Admin)**
- id (UUID)
- email (unique), phone (unique)
- auth_provider (google, phone_otp, email)
- profile_verified (bool), document_verified (bool)
- created_at, updated_at, deleted_at (soft delete)

**Driver (extends User)**
- license_number (unique), license_expiry
- vehicle_id (FK)
- rating (avg 1-5), total_rides, total_earnings
- availability_status (online, offline, on_ride)
- current_location (lat/long, updated every 10s)
- bank_account_id (FK, for payouts)
- documents (license_photo, vehicle_registration, insurance_proof)
- preferred_areas (geofence list)
- is_verified, verification_date

**Passenger (extends User)**
- home_address, work_address (favorites)
- payment_methods (list: card, wallet, corporate)
- rating (avg 1-5), total_rides
- emergency_contacts (name, phone)
- saved_places (list)
- promo_codes (list with balance)
- ride_preferences (music, temperature, conversation)

**Vehicle**
- license_plate (unique), vin (unique)
- make, model, year, color
- capacity (seats), vehicle_type (car, suv, xl)
- driver_id (FK)
- insurance_provider, policy_number
- last_service_date, next_service_due
- mileage, status (active, retired, maintenance)
- inspection_passed (bool), inspection_date

**Ride (Core transaction)**
- id (UUID), status (requested, matched, accepted, in_progress, completed, cancelled)
- passenger_id (FK), driver_id (FK nullable - matched after dispatch)
- pickup_location (lat/long, address)
- dropoff_location (lat/long, address)
- scheduled_time (nullable for future rides)
- created_at, matched_at, started_at, completed_at
- distance (km), duration (minutes estimated, then actual)
- route_polyline (Google Maps encoded polyline)
- estimated_fare, actual_fare, surge_multiplier
- payment_method_id (FK)
- special_requests (text)
- accessibility_needed (bool)
- cancellation_reason (if cancelled), cancellation_by (passenger/driver)
- cancellation_fee

**Rating & Review**
- id, ride_id (FK), rater_id (FK), ratee_id (FK)
- rating (1-5), comment (text)
- categories (cleanliness, driving, conversation, etc.)
- created_at

**Payment & Transaction**
- id, ride_id (FK), passenger_id (FK), driver_id (FK)
- amount, currency, status (pending, completed, failed, refunded)
- payment_method (stripe_card_id, wallet, corporate_account)
- breakdown (base_fare, surge, toll, tip, promo_discount, taxes)
- stripe_payment_intent_id, receipt_url
- created_at, completed_at

**RideRequest (Dispatch queue)**
- id, passenger_id (FK), status (pending, matched, expired)
- pickup_location, dropoff_location
- created_at, expires_at (30s expiry)
- matched_driver_id (FK, when matched)
- available_drivers_count (snapshot)

**DriverLocation (Real-time tracking)**
- driver_id (FK), lat, long, accuracy (meters)
- heading (0-360), speed (kmh)
- timestamp (server time), client_timestamp (client time)
- is_online, is_on_trip
- geohash (for spatial queries)

**Support Ticket**
- id, creator_id (FK, passenger/driver), ride_id (FK nullable)
- category (payment_issue, safety, lost_item, quality, fraud)
- status (open, in_progress, resolved, escalated)
- priority (low, medium, high, critical)
- description, attachments (photo)
- assigned_agent_id (FK), resolution_notes
- created_at, resolved_at

---

## 2. Core Features (MVP)

### 2.1 Passenger Flow
1. **Sign Up & Verification**
   - Email/phone registration, OAuth (Google), OTP verification
   - Profile picture, emergency contact, payment method setup

2. **Request a Ride**
   - Enter pickup/dropoff (maps search with autocomplete)
   - Select ride type (economy, comfort, xl, premium)
   - Add special requests, schedule future rides
   - Set payment method, apply promo code

3. **Ride Tracking**
   - See available drivers (count, ETA)
   - Real-time driver location on map (live)
   - Driver info (name, rating, vehicle, photo)
   - Chat with driver (text only for MVP)
   - Estimated fare, surge multiplier, ETA to dropoff

4. **Ride Completion**
   - Confirm arrival at destination
   - Add tip (optional)
   - Rate & review driver (1-5, optional comment)
   - View receipt (breakdown of charges)

5. **Payment & History**
   - Add payment methods (credit card via Stripe)
   - Manage wallet (top-up, check balance)
   - View ride history, receipts
   - Download invoices (CSV, PDF)

6. **Support & Complaints**
   - Report safety issue during ride (alert button)
   - Post-ride complaint (payment issue, quality, lost item)
   - Chat with support agent
   - Rate support interaction

### 2.2 Driver Flow
1. **Sign Up & Verification**
   - Phone + email registration
   - License upload, vehicle registration, insurance
   - Background check request (third-party integration stub)
   - Bank account setup for payouts

2. **Go Online**
   - Toggle availability (online/offline)
   - Set preferred areas (geofence)
   - Automatic location updates every 10s when online

3. **Accept Rides**
   - Dispatch notification (passenger location, destination)
   - Accept/Decline (10s to respond)
   - View passenger info (name, rating, photo)
   - Navigate to pickup (integrated maps)

4. **Complete Ride**
   - Confirm passenger pickup
   - Navigate to dropoff
   - Confirm arrival, complete ride
   - Collect payment (Stripe payment already processed)
   - Rate & review passenger

5. **Earnings & Payouts**
   - View daily/weekly earnings
   - See breakdown (fares, tips, incentives, deductions)
   - Request payout (weekly automatic transfer to bank)
   - Tax document generation (1099, income summary)

6. **Support**
   - Report safety issue, passenger misconduct
   - Chat with support
   - View support ticket history

### 2.3 Admin & Operations
1. **Dashboard**
   - Total active users (passengers, drivers)
   - Rides in progress, completed today, cancelled
   - Revenue today, week, month
   - Driver utilization rate, average rating
   - Payment success rate

2. **User Management**
   - Search users, view profiles
   - Verify/reject documents
   - Suspend/ban users (fraud, safety)
   - View user support tickets

3. **Driver Management**
   - Approve/reject driver signups
   - View driver stats (acceptance rate, rating, earnings)
   - Manage driver documents expiration
   - Send bulk notifications (surge pricing, incentives)

4. **Finance & Payments**
   - View all transactions, refunds
   - Manage promo codes (create, distribute, track redemption)
   - Payout tracking (to drivers)
   - Revenue reports (by ride type, time, region)
   - Chargeback management

5. **Support Operations**
   - Queue of open tickets
   - Assign to agents, resolve
   - View chat transcripts
   - Analytics (avg resolution time, customer satisfaction)

6. **Safety & Compliance**
   - Safety reports and escalation
   - Fraud detection (unusual patterns, duplicate accounts)
   - Compliance audit log (data access, actions)

---

## 3. Technical Requirements

### 3.1 API Endpoints (45+ endpoints)

**Authentication**
- POST /auth/register, /auth/login, /auth/logout
- POST /auth/refresh_token, /auth/verify_email, /auth/resend_otp
- POST /auth/oauth/google (OAuth callback)

**Users (Passenger, Driver)**
- GET /users/{id}, PUT /users/{id}
- GET /users/{id}/rides, POST /users/{id}/ratings
- POST /users/{id}/documents/upload
- GET /users/{id}/documents (verification status)

**Rides**
- POST /rides (request ride), GET /rides/{id}
- PUT /rides/{id}/status (accept, cancel, complete)
- GET /rides (history), GET /rides/active (in-progress)
- POST /rides/{id}/cancel
- GET /rides/{id}/location (real-time driver location)

**Drivers**
- GET /drivers/available (nearby drivers)
- PUT /drivers/{id}/status (online/offline)
- PUT /drivers/{id}/location (GPS update)
- GET /drivers/{id}/earnings, /drivers/{id}/stats
- POST /drivers/{id}/payout-request

**Payments**
- POST /payments/add-payment-method
- GET /payments/methods, DELETE /payments/methods/{id}
- GET /payments/history, GET /payments/{id}/receipt
- POST /payments/{id}/refund

**Support**
- POST /support/tickets (create), GET /support/tickets/{id}
- POST /support/tickets/{id}/messages (chat)
- PUT /support/tickets/{id}/status

**Admin**
- GET /admin/dashboard, /admin/users, /admin/drivers, /admin/rides
- POST /admin/users/{id}/suspend, /admin/users/{id}/ban
- POST /admin/promo-codes, GET /admin/promo-codes
- GET /admin/analytics/revenue, /admin/analytics/drivers

**Real-time (WebSocket)**
- /ws/ride/{ride_id}/updates (driver location, status updates)
- /ws/user/{user_id}/notifications (ride dispatch, payment updates)
- /ws/support/ticket/{ticket_id}/chat (support chat)

### 3.2 Database Schema
- 11 core tables (User, Driver, Passenger, Vehicle, Ride, RideRequest, etc.)
- 20+ indexes (driver location geospatial, ride status, user email, etc.)
- Soft deletes (deleted_at column) on User, Ride, Payment
- Partitioning on Ride table (by date for scale)
- Archive tables for completed rides >1 year old

### 3.3 Authentication & Security
- JWT tokens (15-min access, 7-day refresh)
- OAuth2 (Google login for passengers/drivers)
- Phone OTP (SMS via Twilio for signup)
- Password hashing (bcrypt), salting
- Rate limiting (10 requests/min per user)
- CORS configuration (mobile app origins)
- HTTPS enforced, TLS 1.2+
- SQL injection prevention (parameterized queries)
- CSRF tokens for web forms
- Secrets management (Stripe API key, Google API key, Twilio auth)

### 3.4 External Integrations
- **Stripe** (payment processing, payouts)
- **Google Maps** (distance, routing, geocoding, geofencing)
- **Twilio** (SMS OTP)
- **SendGrid** (email notifications, receipts)

### 3.5 Async Jobs (Celery)
- Send ride notifications (dispatch to drivers, updates to passenger)
- Calculate surge pricing (periodic, every 5 min)
- Driver location indexing (geospatial, every 30s)
- Process payouts (weekly)
- Generate tax documents (monthly/annually)
- Send rating reminders (post-ride, 1 hour)
- Fraud detection (suspicious patterns, real-time)

### 3.6 Caching (Redis)
- Active drivers by location (geohash, updated every 10s)
- User sessions (JWT blacklist on logout)
- Ride details (15-min TTL)
- Promo code validation (1-hr TTL)
- Surge pricing data (5-min TTL)

### 3.7 Real-time Requirements
- Driver location updates <5s latency to passenger
- Ride dispatch <2s to nearest drivers
- Chat messages <1s delivery
- Notifications <3s
- Dashboard metrics <10s stale

### 3.8 Performance & Scale
- Handle 100K concurrent rides
- 500K monthly active users
- 50K drivers online peak
- 99.9% uptime SLA
- <2s API response (95th percentile)
- <500ms geospatial query (nearby drivers)

---

## 4. Quality Requirements

### 4.1 Code Quality
- 80%+ test coverage (unit + integration)
- 0 unhandled exceptions in production paths
- PEP 8 compliance (Python)
- Type hints on all functions
- Docstrings on public APIs

### 4.2 Security
- No SQL injection, XSS, CSRF vulnerabilities
- Secrets never in code (environment vars)
- Rate limiting on all public endpoints
- Input validation on all user inputs
- OWASP Top 10 compliance

### 4.3 Documentation
- API documentation (OpenAPI/Swagger)
- Database schema diagram
- Deployment guide
- Troubleshooting guide
- Architecture decision records (ADRs)

### 4.4 Deployment
- Docker containerization
- Kubernetes manifests (dev, staging, prod)
- CI/CD pipeline (GitHub Actions)
- Health checks on all services
- Graceful shutdown handling

---

## 5. Data Model: Complete ER Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         RIDE_SHARING_SYSTEM                      │
├─────────────────────────────────────────────────────────────────┤
│
│  USER (PK: id)
│  ├─ id (UUID)
│  ├─ email (unique)
│  ├─ phone (unique)
│  ├─ type (passenger, driver, admin, support, corporate)
│  ├─ profile_verified, document_verified
│  └─ auth fields (password_hash, oauth_id, last_login)
│
│  ├─→ DRIVER (FK: user_id)
│  │   ├─ license_number, license_expiry
│  │   ├─ vehicle_id (FK)
│  │   ├─ current_location (lat/long)
│  │   ├─ availability_status
│  │   ├─ rating, total_rides, total_earnings
│  │   └─ bank_account_id (FK)
│  │
│  ├─→ PASSENGER (FK: user_id)
│  │   ├─ home_address, work_address
│  │   ├─ rating, total_rides
│  │   ├─ emergency_contacts
│  │   └─ payment_methods (1:N)
│  │
│  └─→ SUPPORT_AGENT (FK: user_id)
│      ├─ assigned_tickets
│      └─ support_stats
│
│  VEHICLE (PK: id)
│  ├─ license_plate, vin
│  ├─ driver_id (FK)
│  ├─ vehicle_type, capacity
│  └─ documents (insurance_proof, registration)
│
│  RIDE (PK: id)
│  ├─ passenger_id (FK)
│  ├─ driver_id (FK, matched after dispatch)
│  ├─ pickup_location, dropoff_location
│  ├─ status (requested → matched → in_progress → completed)
│  ├─ distance, duration_estimate, duration_actual
│  ├─ estimated_fare, actual_fare, surge_multiplier
│  ├─ route_polyline (Google Maps)
│  ├─ payment_method_id (FK)
│  ├─ special_requests, accessibility_needed
│  └─ cancellation info (reason, by, fee)
│
│  ├─→ RIDE_REQUEST (PK: id) [Dispatch queue]
│  │   ├─ passenger_id (FK)
│  │   ├─ status (pending, matched, expired)
│  │   ├─ available_drivers (snapshot)
│  │   └─ expires_at (30s TTL)
│  │
│  ├─→ DRIVER_LOCATION (PK: id) [Real-time]
│  │   ├─ driver_id (FK)
│  │   ├─ lat, long, geohash
│  │   ├─ heading, speed
│  │   └─ timestamp (10s updates)
│  │
│  └─→ RATING (PK: id)
│      ├─ ride_id (FK)
│      ├─ rater_id (FK)
│      ├─ ratee_id (FK)
│      ├─ rating (1-5)
│      └─ categories (cleanliness, driving, etc.)
│
│  PAYMENT (PK: id)
│  ├─ ride_id (FK)
│  ├─ passenger_id (FK)
│  ├─ amount, currency
│  ├─ payment_method_id (FK)
│  ├─ breakdown (base, surge, toll, tip, discount)
│  ├─ stripe_payment_intent_id
│  ├─ status (pending, completed, refunded)
│  └─ created_at, completed_at
│
│  PROMO_CODE (PK: id)
│  ├─ code (unique)
│  ├─ discount_amount / percentage
│  ├─ max_uses, uses_count
│  ├─ valid_from, valid_until
│  └─ user_id (FK, if user-specific)
│
│  SUPPORT_TICKET (PK: id)
│  ├─ creator_id (FK, passenger/driver)
│  ├─ ride_id (FK, nullable)
│  ├─ category, status, priority
│  ├─ assigned_agent_id (FK)
│  ├─ messages (1:N)
│  └─ resolution_notes
│
│  SUPPORT_MESSAGE (PK: id)
│  ├─ ticket_id (FK)
│  ├─ sender_id (FK)
│  ├─ message_text, attachments
│  └─ created_at
│
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Implementation Phases (Single Prompt → Multi-Phase Build)

### Phase 1: Core Infrastructure (Immediate)
- User authentication (registration, login, JWT)
- Driver and passenger entities
- Database schema, migrations
- Basic API (GET/POST users, drivers)
- Tests for user management

### Phase 2: Ride Management (Hour 1-2)
- Ride request, matching (simple geospatial)
- Real-time location tracking
- WebSocket setup for live updates
- Ride completion workflow
- Tests for ride flow

### Phase 3: Payments & Transactions (Hour 2-3)
- Stripe integration (payment processing)
- Payment method management
- Fare calculation (base + surge)
- Payout management for drivers
- Tests for payment flow

### Phase 4: Advanced Features (Hour 3-4)
- Rating and reviews
- Support tickets and chat
- Admin dashboard
- Promo codes
- Tests for advanced features

### Phase 5: Observability & Ops (Hour 4-5)
- OTel instrumentation
- Logging, metrics (Prometheus)
- Health checks
- Deployment manifests (Docker, K8s)
- Production readiness checklist

---

## 7. Success Metrics (One-Shot Plugin Validation)

| Metric | Target | Success |
|--------|--------|---------|
| Code generation success | >95% | All core entities generated correctly |
| Test coverage | >80% | Critical paths tested |
| Manual intervention | <5% | Minimal human fixes needed |
| Time to functional system | <5 hours | From prompt to deployable code |
| API endpoint count | 45+ | All CRUD + advanced endpoints |
| Database schema | 11 tables | All relationships correct |
| Bugs in generated code | <10 | Critical bugs caught by tests |
| Documentation | Complete | API docs, schema diagram, guides |

---

## 8. Ride-Sharing System One-Shot Prompt

**THE SINGLE PROMPT TO GENERATE ENTIRE SYSTEM:**

```
Build a complete, production-ready ride-sharing system (like Uber) with all of the following:

CORE ENTITIES:
- User (with 6 subtypes: Passenger, Driver, Admin, Support, Corporate, PaymentAdmin)
- Driver (extends User: license, vehicle, rating, earnings, location tracking)
- Passenger (extends User: payment methods, saved places, promo codes)
- Vehicle (license plate, driver, insurance, mileage, inspection status)
- Ride (passenger, driver, pickup/dropoff, fare calculation, surge pricing, status flow)
- Payment & Transaction (Stripe integration, breakdown, refunds, tax docs)
- Rating & Review (1-5 stars, categories, by driver/passenger)
- Support Ticket (chat, issue tracking, resolution)
- RideRequest (dispatch queue with 30s expiry)
- DriverLocation (real-time tracking, geohash for spatial queries)

FEATURES:
Passenger Flow: Sign up, request ride, track driver real-time, complete ride, pay, rate driver
Driver Flow: Sign up, go online, receive dispatch, accept/decline, complete ride, earn, request payout
Admin Dashboard: Users, drivers, rides, revenue, support tickets, fraud detection
Payments: Stripe integration, card management, wallet, promo codes, driver payouts
Real-time: WebSocket for driver location, ride status, notifications, support chat
Support: Ticket system, chat with support agent, complaint resolution

TECHNICAL:
- Backend: Python FastAPI with PostgreSQL
- Auth: JWT tokens + OAuth2 (Google)
- Payment: Stripe API for payments and payouts
- Geolocation: Google Maps for distance, routing, matching
- Real-time: WebSocket/Socket.IO
- Cache: Redis for active riders, sessions
- Queue: Celery for async jobs (notifications, payouts)
- Tests: 80%+ coverage, all critical paths
- Deployment: Docker, Kubernetes manifests, CI/CD ready
- API: 45+ endpoints (CRUD + advanced operations)
- Database: 11 tables with proper relationships, soft deletes, indexing
- Security: No SQL injection, XSS, CSRF; rate limiting; OWASP compliance
- Performance: <2s response, <5s location update, 100K concurrent rides capacity
- Observability: OTel tracing, structured logs, metrics

REQUIREMENTS:
- All code must be production-ready with minimal human intervention
- All tests must pass (critical paths covered)
- Database migrations must be included
- API documentation (Swagger/OpenAPI)
- Deployment guide (Docker, K8s)
- All security best practices applied
- Error handling with proper HTTP status codes
- Input validation on all endpoints
```

---

**This specification is COMPLETE, DETAILED, and READY FOR PLUGIN EXECUTION in Phase 2.**
