# Multi-Stage Workflow Example

## Overview

This example demonstrates how one-shot-prompting uses a **multi-stage workflow** to transform a natural language feature request into production-ready code. The awesome-ai-apps pattern powers each stage, enabling intelligent analysis and generation at scale.

## Task

Design a payment service that integrates with Stripe, handles webhooks, validates signatures, and logs all transactions with structured logging.

## Running the Example

```bash
cd your-ecommerce-project
/one-shot "payment service with Stripe webhooks and transaction logging" @./
```

---

## Stage 1: Search — Discover Existing Patterns

**What happens:** The curator agent searches your codebase for related patterns.

**Looking for:**
- Existing payment-related entities (Order, Transaction, PaymentMethod)
- Webhook handling patterns
- Structured logging setup
- Stripe integration patterns (if any)

**Example output:**
```
🔍 CODEBASE SEARCH RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Entities Found:
✅ Order (id, user_id, total, status, created_at)
   → relationships: has_many :order_items, belongs_to :user
   → patterns: status enum (pending, confirmed, completed, cancelled)

Services Found:
✅ /services/webhook_handler.py
   → Pattern: Flask endpoint validation, signature verification
   → Integration: Uses hmac.compare_digest for timing-attack safety

Logging Found:
✅ /config/logging.py
   → Pattern: structured_logger with contextvars for request tracing
   → Fields: timestamp, service, request_id, user_id, action
```

---

## Stage 2: Analyze — Extract Domain Model

**What happens:** The analyzer extracts relationships, identifies foreign keys, and determines entity dependencies.

**Analysis:**
```json
Domain Model Extracted:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Entities:
├─ Order (existing)
│  ├─ id (UUID)
│  ├─ user_id (FK → User)
│  ├─ total_cents (Integer, in cents for precision)
│  ├─ status (Enum: pending, paid, refund_requested, refunded)
│  └─ created_at (Timestamp)
│
├─ Payment (new)
│  ├─ id (UUID)
│  ├─ order_id (FK → Order, 1:1 relationship)
│  ├─ stripe_charge_id (String, Stripe's unique identifier)
│  ├─ amount_cents (Integer)
│  ├─ status (Enum: pending, succeeded, failed, refunded)
│  ├─ stripe_webhook_id (String, idempotency key)
│  └─ created_at (Timestamp)
│
└─ Transaction Log (new)
   ├─ id (UUID)
   ├─ payment_id (FK → Payment)
   ├─ event_type (Enum: charge.succeeded, charge.failed, charge.refunded)
   ├─ webhook_body (JSON)
   ├─ processed_at (Timestamp)
   └─ created_at (Timestamp)

Relationships:
- Order 1:1 Payment (one payment per order)
- Payment 1:many TransactionLog (multiple webhook events per payment)
- Order many:1 User (existing)

Foreign Keys:
- Payment.order_id → Order.id
- TransactionLog.payment_id → Payment.id
```

---

## Stage 3: Generate — Create Spec

**What happens:** The architect agent generates spec.json with complete schema, validations, and integration points.

**Generated spec.json snippet:**
```json
{
  "name": "Payment Service",
  "description": "Stripe payment processing with webhooks and transaction logging",
  "entities": [
    {
      "name": "Payment",
      "description": "Represents a Stripe payment for an order",
      "attributes": [
        {
          "name": "id",
          "type": "uuid",
          "primary_key": true
        },
        {
          "name": "order_id",
          "type": "uuid",
          "foreign_key": true,
          "references": "orders.id"
        },
        {
          "name": "stripe_charge_id",
          "type": "string",
          "nullable": false,
          "unique": true,
          "description": "Stripe's unique charge identifier"
        },
        {
          "name": "amount_cents",
          "type": "integer",
          "nullable": false,
          "description": "Amount in cents to avoid floating-point errors"
        },
        {
          "name": "status",
          "type": "enum",
          "enum_values": ["pending", "succeeded", "failed", "refunded"],
          "default": "pending"
        },
        {
          "name": "stripe_webhook_id",
          "type": "string",
          "nullable": true,
          "description": "Idempotency key from Stripe webhook"
        },
        {
          "name": "created_at",
          "type": "timestamp",
          "auto_set": "now"
        }
      ]
    },
    {
      "name": "TransactionLog",
      "description": "Audit log for all payment events",
      "attributes": [
        {
          "name": "id",
          "type": "uuid",
          "primary_key": true
        },
        {
          "name": "payment_id",
          "type": "uuid",
          "foreign_key": true,
          "references": "payments.id"
        },
        {
          "name": "event_type",
          "type": "enum",
          "enum_values": ["charge.succeeded", "charge.failed", "charge.refunded"],
          "description": "Stripe event type"
        },
        {
          "name": "webhook_body",
          "type": "json",
          "nullable": false,
          "description": "Full webhook payload from Stripe for audit trail"
        },
        {
          "name": "processed_at",
          "type": "timestamp",
          "nullable": true,
          "description": "When the webhook was processed"
        },
        {
          "name": "created_at",
          "type": "timestamp",
          "auto_set": "now"
        }
      ]
    }
  ],
  "services": [
    {
      "name": "StripeWebhookService",
      "description": "Handles incoming webhooks from Stripe",
      "methods": [
        {
          "name": "verify_signature",
          "description": "Validates webhook signature using Stripe's shared secret"
        },
        {
          "name": "process_webhook",
          "description": "Handles charge.succeeded, charge.failed, charge.refunded events"
        }
      ]
    }
  ],
  "validations": [
    {
      "entity": "Payment",
      "field": "stripe_charge_id",
      "rule": "must be unique",
      "reason": "Prevent duplicate processing"
    },
    {
      "entity": "Payment",
      "field": "amount_cents",
      "rule": "must be positive",
      "reason": "Amounts must be > 0"
    }
  ]
}
```

---

## Stage 4: Implement — Generate Code

**What happens:** Parallel agents generate migrations, models, and services.

**Generated files:**
```
migrations/
  └─ 2024_05_25_create_payments.py
models/
  ├─ payment.py
  └─ transaction_log.py
services/
  ├─ stripe_webhook_service.py
  └─ payment_processor.py
api/
  └─ webhooks.py
tests/
  ├─ test_stripe_webhook_service.py
  ├─ test_payment_processor.py
  └─ test_webhook_signature_validation.py
```

---

## Stage 5: Verify — Auto-Patch Common Bugs

**What happens:** The verifier runs auto-patch rules to catch common issues:

1. **Missing webhook idempotency** → Added `stripe_webhook_id` to prevent double-processing
2. **SQL injection in webhook body** → Parameterized queries, JSON validation
3. **Timing attacks on signature** → Using `hmac.compare_digest()` instead of `==`
4. **Floating-point currency** → Using `amount_cents` (integer) instead of `amount` (float)

**Patch output:**
```
🔧 AUTO-PATCH RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Rule: webhook_idempotency_key
   Status: APPLIED
   Change: Added stripe_webhook_id to Payment model
   Reason: Prevent duplicate webhook processing

✅ Rule: timing_attack_safety
   Status: APPLIED
   Change: Updated signature verification to use hmac.compare_digest()
   Reason: Constant-time comparison prevents timing attacks

✅ Rule: currency_precision
   Status: APPLIED
   Change: Use amount_cents (integer) instead of amount (float)
   Reason: Avoid floating-point precision errors with currency

✅ Rule: json_validation
   Status: APPLIED
   Change: Added validation for webhook_body schema
   Reason: Ensure only valid Stripe events are logged
```

---

## Stage 6: Review — Security & Performance Gate

**What happens:** The reviewer agent checks security, performance, and style.

**Reviewer report:**
```
🔒 SECURITY REVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Webhook Signature Validation
   Status: PASS
   Notes: Using Stripe's recommended HMAC-SHA256 validation

✅ Sensitive Data Handling
   Status: PASS
   Notes: stripe_charge_id stored (public), but full card details never logged

✅ Idempotency
   Status: PASS
   Notes: stripe_webhook_id prevents duplicate charge processing

⚠️  Recommendations:
   - Consider PCI DSS compliance if storing payment details
   - Implement rate limiting on webhook endpoint
   - Set up monitoring/alerting for failed payments

🚀 PERFORMANCE REVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Database Indexes
   Status: PASS
   Notes: payment.order_id, transaction_log.payment_id indexed

✅ Query Efficiency
   Status: PASS
   Notes: No N+1 queries detected in webhook handler

Recommendations:
   - Consider caching Stripe API responses (30-60 min TTL)
   - Batch webhook processing if high volume (>1000/sec)
```

---

## Stage 7: Wire — Auto-Integrate

**What happens:** The wirer updates main.py to register routes and inject dependencies.

**Changes made:**
```python
# main.py changes
from services.stripe_webhook_service import StripeWebhookService
from api.webhooks import webhook_router

# In app initialization
app.include_router(webhook_router, prefix="/webhooks")
stripe_service = StripeWebhookService(stripe_api_key=settings.STRIPE_API_KEY)
```

---

## Stage 8: Test & Iterate — Critic Loop

**What happens:** The critic runs pytest and provides a pass/fail verdict.

**Output:**
```
pytest output:

collected 12 items

tests/test_payment_processor.py::test_create_payment PASSED
tests/test_payment_processor.py::test_payment_status_updates PASSED
tests/test_stripe_webhook_service.py::test_verify_signature_valid PASSED
tests/test_stripe_webhook_service.py::test_verify_signature_invalid PASSED
tests/test_stripe_webhook_service.py::test_handle_charge_succeeded PASSED
tests/test_stripe_webhook_service.py::test_handle_charge_failed PASSED
tests/test_stripe_webhook_service.py::test_idempotency_prevents_duplicates PASSED
tests/test_stripe_webhook_service.py::test_webhook_body_stored_in_log PASSED
tests/test_stripe_webhook_service.py::test_missing_order_fails_gracefully PASSED
tests/test_stripe_webhook_service.py::test_rate_limit_protection PASSED
tests/test_integrations.py::test_webhook_end_to_end PASSED
tests/test_integrations.py::test_concurrent_webhooks PASSED

12 passed in 0.84s

✅ CRITIC VERDICT: SHIP IT ✓
   All tests passing, ready for deployment.
```

---

## Key Insights from This Workflow

1. **Pattern Reuse**: By searching first, the generated code matches your project's conventions
2. **Relationship Extraction**: Foreign keys and 1:many relationships are discovered automatically
3. **Spec-Driven**: The spec.json is the single source of truth, generated from domain analysis
4. **Auto-Patching**: Common security/precision bugs are caught before code review
5. **Parallel Generation**: Models, services, and tests generated in parallel, cutting time in half
6. **Closed-Loop**: Tests prove correctness; critic decides if code is ready to ship

## Integration with Awesome-AI-Apps

This multi-stage workflow is powered by the **awesome-ai-apps** pattern:

- **Stage 1-2**: Multi-tool search agents discover patterns
- **Stage 3**: Architect agent generates spec (cost: ~$0.10)
- **Stage 4**: Implementer + test-author agents generate in parallel (cost: ~$0.20)
- **Stage 5-6**: Verification + review agents catch issues early
- **Stage 7-8**: Wirer + critic agents complete the loop

Total cost: ~$0.30–$0.50 per feature. Quality far exceeds templated generators.

## Troubleshooting

**Problem**: "No Stripe patterns found in codebase"
- **Solution**: First, manually integrate Stripe in one service. Re-run. Curator will find the pattern.

**Problem**: "Migration conflicts detected"
- **Solution**: Check if Payment/Transaction entities already exist. Use `--schema-only` to preview.

**Problem**: "Webhook tests fail with invalid signatures"
- **Solution**: Ensure `STRIPE_WEBHOOK_SECRET` env var is set. Tests use Stripe's test API keys.

**Problem**: "Critic loop fails with 'module not found'"
- **Solution**: Auto-patch may have missed an import. Run `--apply` to merge changes, then manually fix imports if needed.
