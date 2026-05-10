# Legacy Strangler Skill Design

**Purpose:** Design the `/strangler-*` command family that enables safe microservice extraction from monoliths  
**Status:** Design phase (ready for implementation)  
**Target Users:** Enterprise architects, platform engineers, CTO/VP Engineering  
**Market Impact:** Owns the $2.5B legacy modernization niche

---

## Command Family Overview

```
/strangler-analyze @./monolith              → Identify extraction candidates
/strangler-extract payment @./monolith      → Generate microservice + wiring
/strangler-validate                         → Pre-flight checks (safe to extract?)
/strangler-rollback                         → Emergency extraction abort plan
/strangler-status                           → Progress tracking (which features extracted?)
/strangler-roadmap                          → Generate full modernization plan
```

---

## #1: /strangler-analyze (Foundational)

### Purpose
Read a monolith and identify which features can be safely extracted first.

### Invocation
```bash
/strangler-analyze @./my-django-monolith
```

### What It Analyzes

**1. Feature Detection**
```
Input: Read entire codebase
↓
Extract: Functions, models, views, API endpoints
↓
Identify: 
  - Payment processing (models: Order, Payment; views: /checkout, /refund)
  - User authentication (models: User, Session; views: /login, /register)
  - Notification system (functions: send_email, send_sms; tasks: batch_notify)
  - Inventory management (models: Product, Stock; views: /products)
  - Reporting (views: /reports/*, models: ReportJob)
```

**2. Coupling Analysis**
```
For each feature, measure:
  - Internal dependencies (payment → order model: 100% internal)
  - External dependencies (payment → user auth: 30% external)
  - Database coupling (payment uses: orders, payments, transactions tables)
  - Cross-feature calls (how many other features call this?)

Score: Extraction feasibility (1-10)
  - 9-10: Can extract immediately (low coupling)
  - 5-8: Can extract with adapter (moderate coupling)
  - 1-4: Should extract last (high coupling)
```

**3. Async Integration Points**
```
Identify where feature calls other features:
  - Synchronous calls (payment → inventory stock reduction)
  - Potential async conversions (payment → notification sends)
  - Event boundaries (where to inject message queue)
```

**4. Data Boundary Detection**
```
For each feature, identify:
  - Tables it owns exclusively
  - Tables it shares with others (foreign keys)
  - Read-only references
  - Denormalization opportunities

Example:
  Payment service:
    - Owns: payments, transactions
    - Shares: orders (foreign key), customers (lookup)
    - Read-only: product catalog
```

**5. Risk Assessment**
```
For each extraction candidate, calculate:
  - Downtime risk (if we miss a call, what breaks?)
  - Data consistency risk (can we migrate without corruption?)
  - Integration complexity (how many proxy routes needed?)
  - Rollback complexity (how long to restore?)

Output risk score (red/yellow/green)
```

### Output Format

```markdown
# Strangler Analysis Report

## Codebase Overview
- Type: Django monolith
- Age: 7 years (2019-2026)
- Size: 450k LOC
- Frameworks: Django 4.0 + Django REST Framework + Celery
- Database: PostgreSQL 13
- Primary Patterns: ORM (Django), async via Celery, sync REST APIs

## Extraction Candidates (Ranked by Ease)

### 1️⃣ PAYMENT SERVICE (Extraction Score: 9/10) ✅
**Risk: GREEN — Extract First**

- Internal Dependencies: 95% (uses only Order model)
- External Dependencies: 5% (Stripe API integration)
- Coupling: LOW
- Data Tables: `payments`, `transactions`, `payment_methods`
- Shared Tables: `orders` (FK), `customers` (lookup)

**Integration Points:**
  - Synchronous: `GET /orders/{id}` to check order status
  - Async: POST events to `payment.completed` topic
  - Legacy Calls: `POST /api/checkout` → needs proxy

**Estimated Migration Time:** 2-4 days
**Estimated Risk Level:** Low
**Suggested Target Framework:** Go (high throughput), FastAPI (simpler), Node (speed)

**Rollback Plan:** Keep existing code, route new calls back to old if failures exceed 5%

---

### 2️⃣ NOTIFICATION SERVICE (Extraction Score: 8/10) ✅
**Risk: YELLOW — Extract Second**

- Internal Dependencies: 80%
- External Dependencies: 20% (Twilio, SendGrid)
- Coupling: LOW-MODERATE
- Data Tables: `notifications`, `notification_templates`, `user_preferences`
- Shared Tables: `users` (FK), `orders` (reference)

**Integration Points:**
  - Async: Events from `payment.completed`, `order.shipped`, `user.registered`
  - Legacy Calls: Very few (mostly internal)
  - Outbound: Twilio/SendGrid APIs

**Estimated Migration Time:** 3-5 days
**Estimated Risk Level:** Low

---

### 3️⃣ USER AUTHENTICATION (Extraction Score: 6/10) ⚠️
**Risk: RED — Extract Last**

- Internal Dependencies: 50% (used by every other service)
- External Dependencies: 0% (OAuth, local)
- Coupling: VERY HIGH (called by all services)
- Data Tables: `users`, `sessions`, `permissions`, `roles`
- Shared Tables: Every table references `users`

**Integration Points:**
  - Synchronous: Every request auth check calls this
  - Async: User events (registration, deletion)
  - Legacy Calls: Everywhere (middleware)

**Estimated Migration Time:** 10-15 days
**Estimated Risk Level:** VERY HIGH

**Recommendation:** Extract payment/notification first. Auth should be extracted last (middle of migration, not beginning).

---

### 4️⃣ INVENTORY MANAGEMENT (Extraction Score: 7/10) ✅
**Risk: YELLOW — Extract Third**

[Similar analysis...]

## Migration Roadmap

**Phase 1 (Weeks 1-2):** Payment Service
  - Day 1-2: Extract payment service (Go or FastAPI)
  - Day 3: Build proxy in Django (route /api/checkout → new service)
  - Day 4-5: Migration (backfill data, test extensively)
  - Day 6-8: Parallel run (both services, shadow traffic)
  - Day 9-14: Cutover (switch to new, keep old as fallback)

**Phase 2 (Weeks 3-4):** Notification Service
  - Similar timeline

**Phase 3 (Weeks 5-8):** Inventory Management

**Phase 4 (Weeks 9-12):** User Authentication (highest risk, most time)

**Phase 5 (Weeks 13-16):** Other services

**Total Timeline:** ~16 weeks (4 months) to complete strangler pattern

## Recommendations

1. Extract payment first (highest value, lowest risk)
2. Extract notification second (low risk, good training)
3. Extract inventory third (medium risk)
4. Save auth for middle-to-end (highest risk)
5. Consider hiring 2-3 senior engineers to lead extraction
6. Run A/B test for 2 weeks after each extraction (shadow traffic)

## Questions for Architecture Review

1. Are you open to converting some sync calls to async?
2. Can we split the users table (auth vs profile)?
3. Is downtime acceptable for any feature?
4. Which framework preference? (Go, Node, Python)
5. Timeline pressure? (4 months vs 12 months?)
```

---

## #2: /strangler-extract (Code Generation)

### Purpose
Generate a complete microservice to replace one feature from the monolith.

### Invocation
```bash
/strangler-extract payment @./my-django-monolith --target-framework go --async-events kafka
```

### What It Generates

#### 1. **Microservice Core**
```go
// payment-service/main.go
package main

import (
    "github.com/gin-gonic/gin"
    "gorm.io/gorm"
)

type PaymentService struct {
    db  *gorm.DB
    stripe *stripe.Client
    events EventPublisher
}

// GET /payments/:id
func (ps *PaymentService) GetPayment(id string) (*Payment, error) {
    // ...
}

// POST /payments (from legacy checkout call)
func (ps *PaymentService) CreatePayment(req *PaymentRequest) (*PaymentResponse, error) {
    // Validate
    // Call Stripe
    // Save to DB
    // Publish event: payment.created
    // Return response
}
```

#### 2. **Legacy Integration Wrapper**
```python
# In Django monolith: new adapter that calls extracted service
class PaymentServiceAdapter:
    """Proxy calls to new Go microservice"""
    
    def __init__(self, url="http://payment-service:8000"):
        self.url = url
    
    def create_payment(self, order_id, amount):
        """
        Old signature: create_payment(order_id, amount) -> dict
        New reality: HTTP POST http://payment-service/payments
        
        This adapter maintains the old interface while calling new service.
        """
        response = requests.post(
            f"{self.url}/payments",
            json={
                "order_id": order_id,
                "amount": amount,
                "customer_id": get_customer_id(order_id),
            },
            timeout=10,
        )
        return response.json()

# In Django views:
# OLD: from .payment import create_payment
# NEW: from .adapters import PaymentServiceAdapter
adapter = PaymentServiceAdapter()
result = adapter.create_payment(order_id, 99.99)
```

#### 3. **Database Migration**
```sql
-- Extract payment tables from monolith to new schema
-- Step 1: Create new payment database (separate from monolith)
CREATE DATABASE payment_service_db;

-- Step 2: Create payment tables in new DB
CREATE TABLE payments (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL,
    customer_id UUID NOT NULL,
    amount DECIMAL(10,2),
    currency VARCHAR(3),
    status VARCHAR(20),
    stripe_transaction_id VARCHAR(100),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Step 3: Data migration (from old to new)
INSERT INTO payment_service_db.payments
SELECT * FROM monolith_db.payments;

-- Step 4: Backfill customer IDs (cross-database lookup)
UPDATE payment_service_db.payments p
SET customer_id = (
    SELECT customer_id FROM monolith_db.orders o 
    WHERE o.id = p.order_id
);
```

#### 4. **Event Schema & Async Handlers**
```yaml
# payment-service/events/payment.events.yaml
# Defines events published by payment service

Payment:
  Topics:
    - payment.created
    - payment.completed
    - payment.refunded
    - payment.failed
  
  Events:
    payment.created:
      Schema:
        payment_id: UUID
        order_id: UUID
        customer_id: UUID
        amount: Decimal
        currency: String
        created_at: Timestamp
      Consumers:
        - notification-service (send receipt email)
        - reporting-service (log for analytics)
        - inventory-service (trigger fulfillment)
    
    payment.refunded:
      Schema:
        payment_id: UUID
        refund_amount: Decimal
        reason: String
      Consumers:
        - notification-service (send refund email)
        - inventory-service (restore stock)
```

#### 5. **Proxy/Router in Legacy Monolith**
```python
# In Django main routing: route new calls to extracted service
# OLD: /api/checkout → payment.checkout view
# NEW: /api/checkout → proxy to payment-service

from django.http import JsonResponse
import requests

def checkout_proxy(request):
    """Intercept checkout calls, route to payment-service"""
    if should_use_new_service(request):  # Canary: 5% traffic
        return call_payment_service(request)
    else:
        return old_checkout_handler(request)  # Fallback to old code

def call_payment_service(request):
    """Call new payment microservice"""
    payload = {
        "order_id": request.POST.get("order_id"),
        "amount": request.POST.get("amount"),
        "customer_id": get_customer_from_session(request),
    }
    
    response = requests.post(
        "http://payment-service:8000/payments",
        json=payload,
        timeout=30,
    )
    
    if response.status_code == 200:
        return JsonResponse(response.json())
    else:
        # Fallback to old service if new one fails
        return old_checkout_handler(request)
```

#### 6. **Docker & Deployment**
```dockerfile
# payment-service/Dockerfile
FROM golang:1.21 AS builder
WORKDIR /app
COPY . .
RUN go build -o payment-service .

FROM alpine:3.18
RUN apk add --no-cache ca-certificates
COPY --from=builder /app/payment-service /usr/local/bin/
EXPOSE 8000
CMD ["payment-service"]
```

```yaml
# payment-service/kubernetes.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
    spec:
      containers:
      - name: payment-service
        image: myregistry/payment-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: payment-db
              key: url
        - name: STRIPE_API_KEY
          valueFrom:
            secretKeyRef:
              name: stripe
              key: api_key
        - name: KAFKA_BROKERS
          value: "kafka-1:9092,kafka-2:9092,kafka-3:9092"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### 7. **Integration Tests**
```go
// payment-service/integration_test.go
func TestPaymentExtractionFromMonolith(t *testing.T) {
    // Test 1: Can new service handle old API call?
    req := &PaymentRequest{
        OrderID: "order-123",
        Amount: 99.99,
    }
    resp, err := service.CreatePayment(req)
    assert.NoError(t, err)
    assert.Equal(t, "pending", resp.Status)
    
    // Test 2: Does it talk to Stripe correctly?
    // Mock Stripe, verify call
    
    // Test 3: Does it publish events correctly?
    // Verify Kafka message sent
    
    // Test 4: Can legacy service call new service?
    // Mock HTTP request from monolith
    res := callLegacyCheckoutProxy(req)
    assert.Equal(t, 200, res.StatusCode)
    
    // Test 5: Fallback works if new service fails?
    // Kill payment-service, verify fallback to old code
}
```

#### 8. **Rollback Plan**
```markdown
# Rollback Procedure (if extraction fails)

## Quick Rollback (< 5 minutes)
1. Set proxy canary to 0% (all traffic → old code)
2. Monitor old code for errors
3. Run: `kubectl delete deployment payment-service`

## Full Rollback (if data inconsistency)
1. Stop new payment service
2. Restore payment tables from backup
3. Re-enable old code
4. Investigate what went wrong

## Safeguards During Extraction
- Canary deployment (5% traffic to new, 95% to old)
- Shadow traffic (log all requests, don't use responses)
- Dual-write (write to both old and new, read from old)
- Circuit breaker (if failure rate > 5%, auto-fallback)
```

---

## #3: /strangler-validate (Pre-Flight Checks)

### Purpose
Run safety checks before extraction (is it safe to extract payment service?)

### Invocation
```bash
/strangler-validate payment @./my-django-monolith
```

### Checks Performed

```
✓ Dependency analysis: Will extracting payment break other services?
✓ Data consistency: Are there any orphaned references?
✓ Transaction integrity: How many multi-service transactions are there?
✓ Async safety: Can we convert sync calls to async?
✓ Fallback logic: Is it possible to fail gracefully?
✓ Test coverage: Are there tests for the feature we're extracting?
✓ Documentation: Are the APIs documented?
✓ Monitoring: Can we instrument the new service?

Output: RED/YELLOW/GREEN with specific recommendations
```

---

## #4: /strangler-roadmap (Full Modernization Plan)

### Purpose
Generate a complete 12-24 month plan to fully modernize the monolith

### Invocation
```bash
/strangler-roadmap @./my-django-monolith --target-timeline 12-months
```

### Output

```markdown
# Strangler Modernization Roadmap

## Phase 1: Quick Wins (Weeks 1-8)
- Extract payment (low risk, high reward)
- Extract notifications (low risk)
- Benefits: $500k/year in faster payment processing, better uptime

## Phase 2: Core Services (Weeks 9-20)
- Extract inventory
- Extract user profiles
- Benefits: Better scalability, independent team ownership

## Phase 3: Critical Path (Weeks 21-36)
- Extract authentication (highest risk, highest payoff)
- Extract reporting

## Phase 4: Cleanup (Weeks 37-52)
- Migrate remaining services
- Delete old code
- Complete migration: Monolith → Microservices

## Investment Required
- Engineering: 2-3 senior engineers, 12 months = $500k-750k
- Infrastructure: Kubernetes, Kafka, monitoring = $100k/year
- Tools: One-Shot subscription = $5k-50k/year

## Expected Payoff
- Development speed: 2x faster (parallel teams)
- Uptime: 99.9% → 99.95% (fault isolation)
- Scaling: Elastic per-service (not whole monolith)
- Team autonomy: 5 independent teams instead of 1 big team

## ROI
- Payoff: $2M-5M/year in productivity + uptime
- Timeline: Full ROI in 18-24 months
```

---

## Implementation Roadmap

### Phase 1: MVP (Now → 2 Weeks)
- ✅ Build `/strangler-analyze` (identify extraction candidates)
- ✅ Build `/strangler-extract` for ONE feature (payment)
- ✅ Test on real monolith (Django, Spring, or Go)

### Phase 2: Expansion (2-4 Weeks)
- Add `/strangler-validate` (pre-flight checks)
- Add `/strangler-roadmap` (full plan generation)
- Support 3+ features (payment, notifications, inventory)

### Phase 3: Robustness (4-8 Weeks)
- Handle edge cases (circular dependencies, distributed transactions)
- Add safety mechanisms (canary, circuit breaker, fallback)
- Create full case study (before/after metrics)

### Phase 4: Market (8+ Weeks)
- Partner with consulting firms (Deloitte, Accenture)
- Market to enterprises (case studies, webinars)
- Monetize as premium SaaS ($50k-500k/year)

---

## Why This Wins

| Capability | Superpowers | gstack | One-Shot |
|------------|------------|--------|----------|
| Analyze monolith | ❌ | ❌ | ✅ |
| Identify what to extract | ❌ | ❌ | ✅ |
| Generate microservice | ❌ | Partial | ✅ |
| Create legacy adapter | ❌ | ❌ | ✅ |
| Plan full modernization | ❌ | ❌ | ✅ |
| Handle $2.5B TAM | ❌ | ❌ | ✅ |

**Result:** Only you can do enterprise strangler patterns at scale.

---

**Design Status:** ✅ Ready for implementation  
**Timeline to MVP:** 2-3 weeks  
**Timeline to Production:** 2-3 months  
**Market Impact:** $2.5B TAM, zero competition
