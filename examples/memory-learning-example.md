# Memory Learning Propagation Example

## Overview

This example demonstrates how one-shot-prompting **learns from successful generations and applies those learnings to future tasks**. The awesome-ai-apps memory-propagator agent extracts patterns, records them, and surfaces them when similar tasks are requested.

## How Memory Learning Works

```
Task 1 → Success → Extract Learnings → Store in Memory
                                             ↓
Task 2 (similar) → Detect Similarity → Suggest Previous Learnings → Success with Less Effort
```

---

## Scenario: Payment Processing Across Projects

### First Project: E-Commerce

You run:
```bash
cd ~/projects/ecommerce
/one-shot "add Stripe payment processing with webhook validation" @./
```

**Generation succeeds.** Code passes all tests. Critic says: ✅ SHIP IT

---

## Stage 1: Extraction — Memory-Propagator Analyzes Success

**What happens**: At the end of successful generation, the memory-propagator agent:

1. **Extracts the spec.json** generated during architect phase
2. **Reads the generated code** to understand what was created
3. **Reviews critic feedback** to see what worked well
4. **Identifies key patterns** that made this successful

**Extracted learnings:**
```json
{
  "id": "learning_20240525_001",
  "timestamp": "2024-05-25T14:35:23Z",
  "task": "add Stripe payment processing with webhook validation",
  "project": "ecommerce",
  "status": "success",
  
  "pattern": "payment_webhook_validation",
  "category": "stripe_integration",
  "confidence": 0.98,
  
  "description": "Best practices for validating Stripe webhooks securely",
  
  "key_insights": [
    {
      "name": "signature_verification_timing_attack_safe",
      "rule": "Always use hmac.compare_digest() instead of == operator",
      "why": "Prevents timing attacks that could reveal webhook secret",
      "code_reference": "services/stripe_webhook_service.py:45-47",
      "difficulty": "easy",
      "impact": "critical_security"
    },
    {
      "name": "idempotency_key_for_retries",
      "rule": "Store stripe_webhook_id to prevent duplicate processing",
      "why": "Stripe may retry webhooks; without idempotency, same event processed twice",
      "code_reference": "models/payment.py:28-30",
      "difficulty": "easy",
      "impact": "prevents_data_corruption"
    },
    {
      "name": "amount_precision_use_cents",
      "rule": "Store amounts in cents (integer), never float",
      "why": "Floating-point math causes rounding errors with currency",
      "code_reference": "models/payment.py:15-16",
      "difficulty": "easy",
      "impact": "prevents_financial_errors"
    },
    {
      "name": "validate_webhook_signature_first",
      "rule": "Verify signature before ANY processing",
      "why": "Malicious requests must be rejected before hitting database",
      "code_reference": "api/webhooks.py:22-25",
      "difficulty": "easy",
      "impact": "prevents_unauthorized_access"
    },
    {
      "name": "log_full_webhook_body_for_audit",
      "rule": "Store complete webhook payload in audit table",
      "why": "Required for compliance and debugging Stripe issues",
      "code_reference": "models/transaction_log.py:40-42",
      "difficulty": "easy",
      "impact": "compliance_auditability"
    }
  ],
  
  "related_entities": [
    "Payment",
    "TransactionLog",
    "Order"
  ],
  
  "common_bugs_avoided": [
    "timing_attack_vulnerability",
    "duplicate_payment_processing",
    "floating_point_currency_error",
    "unauthorized_webhook_processing",
    "audit_trail_gaps"
  ],
  
  "success_factors": [
    "Pattern search found existing webhook handler in codebase",
    "Spec-driven approach ensured all edge cases covered",
    "Auto-patch caught timing attack vulnerability",
    "100% test coverage for webhook handlers",
    "Critic loop ran twice; first run flagged missing idempotency"
  ],
  
  "metrics": {
    "generation_time_seconds": 47,
    "cost_usd": 0.42,
    "test_coverage_percent": 92,
    "tests_passing": 47,
    "first_attempt_success": false,
    "attempts_to_success": 2
  },
  
  "embedding": "vector_representation_for_similarity_search"
}
```

---

## Stage 2: Storage — Learning Added to Memory Database

**What happens**: The learning is stored with embeddings for semantic search.

```
Memory Database Structure:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

table: learnings
├─ id: UUID (learning_20240525_001)
├─ timestamp: DateTime
├─ task: Text (what user asked for)
├─ pattern_name: String (payment_webhook_validation)
├─ category: String (stripe_integration)
├─ description: Text
├─ key_insights: JSON array (5 insights)
├─ embedding: Vector (768-dim, searchable)
├─ success: Boolean (true/false)
├─ confidence: Float (0.98)
├─ metrics: JSON (generation time, cost, test coverage)
└─ source_project: String (ecommerce)

Example query:
SELECT * FROM learnings
WHERE similarity(embedding, query_vector) > 0.75
ORDER BY confidence DESC
LIMIT 3
```

---

## Stage 3: Curriculum Update — Future Tasks Benefit

**What happens**: The curriculum (used in Stage 1 of future generations) is updated.

```
Curriculum Entry Added:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pattern: payment_webhook_validation
Added: 2024-05-25T14:35:23Z
Success Rate: 98% (1 success, 0 failures)
Times Recommended: 0 (waiting for similar request)
Times Applied: 1

Hints for Next Time:
1. ✅ Always use hmac.compare_digest() for webhook signature (critical)
2. ✅ Store webhook_id in Payment model for idempotency (critical)
3. ✅ Use amount_cents (integer), not amount (float) (critical)
4. ✅ Validate signature before ANY database writes (critical)
5. ✅ Audit trail required: log full webhook body (compliance)

When to Suggest:
- Keywords: "webhook", "stripe", "payment", "charge", "signature"
- Task similarity > 0.7 to original task
```

---

## Second Project: SaaS Application

Three weeks later, in a different project, you run:

```bash
cd ~/projects/saas-platform
/one-shot "add Stripe billing with webhook support for subscription updates" @./
```

---

## Stage 1: Predictive Failure Detection — Memory Activated

**What happens**: At the START of generation, the curriculum agent checks for similar patterns.

**Similarity search:**
```json
{
  "user_task": "add Stripe billing with webhook support for subscription updates",
  "similar_patterns_found": [
    {
      "pattern_name": "payment_webhook_validation",
      "pattern_source": "ecommerce project (May 25)",
      "similarity_score": 0.82,
      "confidence": 0.98,
      "key_insights": [
        "Use hmac.compare_digest() for webhook signature validation",
        "Store webhook_id to prevent duplicate processing",
        "Use amount_cents (integer), not float",
        "Validate signature before database writes",
        "Log full webhook body for audit"
      ],
      "recommendation": "STRONG - Use these practices for billing webhooks"
    }
  ]
}
```

**Output to user:**
```
🧠 MEMORY ACTIVATED: Found similar pattern!

Pattern: payment_webhook_validation
Last used: ecommerce project (May 25)
Similarity: 82% match to your current task

Key Lessons from Previous Success:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ✅ Webhook Signature Safety
   Remember: Always use hmac.compare_digest() instead of == operator.
   Why: Prevents timing attacks that could expose your webhook secret.
   
2. ✅ Idempotency Prevention
   Remember: Store webhook_id in your Subscription/Billing model.
   Why: Stripe retries webhooks. Without this, same charge processes twice.
   
3. ✅ Amount Precision
   Remember: Use amount_cents (integer), never float for money.
   Why: Floating-point math causes rounding errors, losing pennies over time.
   
4. ✅ Signature First
   Remember: Validate webhook signature BEFORE any processing.
   Why: Malicious requests must be rejected before touching the database.
   
5. ✅ Audit Trail
   Remember: Log the full webhook body for compliance.
   Why: You'll need this for debugging and regulatory audits.

Apply these practices? [Y/n] (proceeding with Y...)
```

---

## Stage 2: Architect Phase — Spec Uses Memory

**What happens**: When the architect agent generates spec.json, it incorporates the remembered patterns.

**Generated spec.json (with memory hints):**
```json
{
  "name": "SaaS Billing with Stripe",
  "description": "Subscription billing using Stripe webhooks",
  
  "_memory_notes": {
    "similar_pattern": "payment_webhook_validation",
    "confidence": 0.82,
    "patterns_applied": [
      "signature_verification_timing_attack_safe",
      "idempotency_key_for_retries",
      "amount_precision_use_cents",
      "validate_webhook_signature_first",
      "log_full_webhook_body_for_audit"
    ]
  },
  
  "entities": [
    {
      "name": "Subscription",
      "description": "Stripe subscription billing",
      "attributes": [
        {
          "name": "id",
          "type": "uuid",
          "primary_key": true
        },
        {
          "name": "user_id",
          "type": "uuid",
          "foreign_key": true,
          "references": "users.id"
        },
        {
          "name": "stripe_subscription_id",
          "type": "string",
          "unique": true,
          "nullable": false,
          "description": "Stripe's subscription ID"
        },
        {
          "name": "amount_cents",
          "type": "integer",
          "nullable": false,
          "description": "Monthly amount in cents (NOT float!)"
        },
        {
          "name": "status",
          "type": "enum",
          "enum_values": ["active", "paused", "cancelled"],
          "default": "active"
        },
        {
          "name": "stripe_webhook_id",
          "type": "string",
          "nullable": true,
          "description": "Idempotency key to prevent double-processing"
        },
        {
          "name": "created_at",
          "type": "timestamp",
          "auto_set": "now"
        }
      ]
    },
    {
      "name": "BillingLog",
      "description": "Audit trail for billing webhooks (required for compliance)",
      "attributes": [
        {
          "name": "id",
          "type": "uuid",
          "primary_key": true
        },
        {
          "name": "subscription_id",
          "type": "uuid",
          "foreign_key": true,
          "references": "subscriptions.id"
        },
        {
          "name": "event_type",
          "type": "enum",
          "enum_values": ["customer.subscription.created", "invoice.created", "invoice.paid", "invoice.failed"],
          "description": "Stripe webhook event type"
        },
        {
          "name": "webhook_body",
          "type": "json",
          "nullable": false,
          "description": "Full webhook payload (required for debugging)"
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
      "description": "Handles Stripe billing webhooks",
      "methods": [
        {
          "name": "verify_signature",
          "description": "Validate webhook using hmac.compare_digest() (timing-attack safe)",
          "note": "From payment_webhook_validation pattern (ecommerce, May 25)"
        },
        {
          "name": "process_webhook",
          "description": "Handle subscription events with idempotency check"
        }
      ]
    }
  ],
  
  "validations": [
    {
      "entity": "Subscription",
      "field": "amount_cents",
      "rule": "Must be positive integer (cents, not float)",
      "source": "memory_pattern: amount_precision_use_cents"
    },
    {
      "entity": "Subscription",
      "field": "stripe_webhook_id",
      "rule": "Must be unique to prevent duplicate processing",
      "source": "memory_pattern: idempotency_key_for_retries"
    }
  ]
}
```

---

## Stage 3: Implementation — Directly Applies Memory

**What happens**: When code is generated, the remembered lessons are directly applied.

**Generated stripe_webhook_service.py:**
```python
# Auto-generated with memory pattern: payment_webhook_validation

import hmac
import hashlib
from typing import Dict, Any

class StripeWebhookService:
    def __init__(self, webhook_secret: str):
        self.webhook_secret = webhook_secret
    
    def verify_signature(self, payload: bytes, signature_header: str) -> bool:
        """
        Validate Stripe webhook signature using timing-attack-safe comparison.
        
        Memory pattern: signature_verification_timing_attack_safe
        Source: ecommerce project (May 25, 2024)
        Why: Prevents timing attacks from revealing webhook secret
        """
        # CRITICAL: Use hmac.compare_digest() NOT == operator
        expected_sig = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Timing-attack safe comparison
        return hmac.compare_digest(expected_sig, signature_header)
    
    def process_webhook(self, event: Dict[str, Any]) -> bool:
        """
        Process Stripe webhook with idempotency.
        
        Memory pattern: idempotency_key_for_retries
        Source: ecommerce project (May 25, 2024)
        Why: Stripe retries webhooks; without this, same charge processes twice
        """
        webhook_id = event.get('id')
        
        # Check if we've already processed this webhook
        existing = Subscription.objects.filter(
            stripe_webhook_id=webhook_id
        ).first()
        
        if existing:
            # Idempotent: already processed, return success
            return True
        
        # Process new event
        if event['type'] == 'customer.subscription.created':
            return self._handle_subscription_created(event, webhook_id)
        
        # ... more handlers
    
    def _handle_subscription_created(self, event: Dict, webhook_id: str) -> bool:
        """Handle subscription.created webhook."""
        subscription = Subscription.create(
            stripe_subscription_id=event['data']['object']['id'],
            amount_cents=int(event['data']['object']['items']['data'][0]['price']['unit_amount']),
            # CRITICAL: Use amount_cents (integer), NOT amount (float)
            # Why: Floating-point math loses pennies over time
            stripe_webhook_id=webhook_id  # Store for idempotency
        )
        
        # Log full webhook body for audit trail and compliance
        BillingLog.create(
            subscription=subscription,
            event_type=event['type'],
            webhook_body=event  # Full payload for debugging
        )
        
        return True
```

---

## Stage 4: Verification — Auto-Patch Uses Memory

**What happens**: The auto-patch step checks the code against remembered patterns.

**Auto-patch results:**
```
🔧 AUTO-PATCH: Applying Memory Patterns
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Checking against pattern: payment_webhook_validation (confidence: 98%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ signature_verification_timing_attack_safe
   Status: FOUND in code
   Location: stripe_webhook_service.py:22-24
   Verified: hmac.compare_digest() used ✓

✅ idempotency_key_for_retries
   Status: FOUND in code
   Location: models/subscription.py:18
   Verified: stripe_webhook_id field exists ✓

✅ amount_precision_use_cents
   Status: FOUND in code
   Location: models/subscription.py:12
   Verified: amount_cents (integer) used, not float ✓

✅ validate_webhook_signature_first
   Status: FOUND in code
   Location: api/webhooks.py:15-18
   Verified: verify_signature() called before processing ✓

✅ log_full_webhook_body_for_audit
   Status: FOUND in code
   Location: models/billing_log.py:8
   Verified: webhook_body (JSON) stored ✓

Result: ALL 5 memory patterns found and correctly applied!
Confidence: 98% → This will succeed with high probability.
```

---

## Stage 5: Tests — Pass Immediately

**What happens**: Tests pass on first try because memory patterns prevent common bugs.

```
pytest results:

collected 18 items

tests/test_stripe_webhook_service.py::test_verify_signature_valid PASSED
tests/test_stripe_webhook_service.py::test_verify_signature_invalid PASSED
tests/test_stripe_webhook_service.py::test_verify_signature_timing_safe PASSED
tests/test_stripe_webhook_service.py::test_handle_subscription_created PASSED
tests/test_stripe_webhook_service.py::test_idempotency_prevents_duplicates PASSED
tests/test_stripe_webhook_service.py::test_webhook_id_stored PASSED
tests/test_stripe_webhook_service.py::test_amount_cents_precision PASSED
tests/models/test_subscription.py::test_create_subscription PASSED
tests/models/test_subscription.py::test_amount_stored_as_cents PASSED
tests/models/test_billing_log.py::test_webhook_body_stored PASSED
tests/integration/test_webhook_end_to_end.py::test_subscribe_and_invoice PASSED
tests/integration/test_webhook_end_to_end.py::test_concurrent_webhooks PASSED
tests/integration/test_webhook_end_to_end.py::test_webhook_retry_idempotent PASSED
tests/integration/test_webhook_end_to_end.py::test_failed_invoice_handling PASSED
tests/integration/test_webhook_end_to_end.py::test_audit_trail_complete PASSED
tests/integration/test_webhook_end_to_end.py::test_timing_attack_safe PASSED
tests/integration/test_webhook_end_to_end.py::test_amount_precision_large_numbers PASSED
tests/integration/test_webhook_end_to_end.py::test_concurrent_and_retry_mixed PASSED

18 passed in 1.23s

✅ CRITIC VERDICT: SHIP IT ✓
   All tests passing on FIRST RUN.
   Memory patterns prevented common bugs.
```

---

## Comparison: With vs Without Memory

| Aspect | Without Memory | With Memory |
|--------|---|---|
| **Startup** | Fresh generation each time | Learnings pre-loaded |
| **Bugs avoided** | 0 (catch during testing) | 5 (caught by patterns) |
| **First run pass** | 60% | 98% |
| **Tests passing** | After 2-3 iterations | First iteration |
| **Time to ship** | 2 hours | 20 minutes |
| **User confidence** | "Hope it works" | "This pattern succeeded last time" |

---

## Memory Learning Features

### 1. Automatic Extraction
- ✅ Success/failure status detected automatically
- ✅ Key insights extracted from code and spec
- ✅ Patterns identified by curator agent
- ✅ Confidence scores computed from metrics

### 2. Semantic Search
- ✅ Embeddings computed for each pattern
- ✅ Similar tasks find relevant learnings
- ✅ Threshold (0.7) balances precision/recall
- ✅ Top 3 recommendations shown to user

### 3. Integration Points
- ✅ Curriculum hints at task start
- ✅ Spec includes memory annotations
- ✅ Generated code directly applies patterns
- ✅ Auto-patch validates patterns were used

### 4. Feedback Loop
- ✅ Each success increases pattern confidence
- ✅ Each failure decreases pattern confidence
- ✅ Curriculum adapts based on outcomes
- ✅ User can manually rate recommendations

---

## How to Use Memory Learnings

### View Available Learnings
```bash
/curriculum --list-learnings
```

Output:
```
Available Learnings (11 total):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. payment_webhook_validation (confidence: 98%)
   Source: ecommerce (May 25)
   Times applied: 1 (all successes)

2. django_form_validation (confidence: 92%)
   Source: django-order-service (May 18)
   Times applied: 3 (2 successes, 1 failure)

3. redis_caching_patterns (confidence: 87%)
   Source: fastapi-async-api (May 10)
   Times applied: 2 (all successes)

... and 8 more
```

### Filter by Category
```bash
/curriculum --list-learnings --category stripe_integration
```

### Show Details
```bash
/curriculum --show-learning payment_webhook_validation
```

### Disable Learning for Task
```bash
/one-shot "your feature" @./ --skip-learnings
```

---

## Troubleshooting Memory Learning

**Problem**: "Pattern recommended but not applied?"
- **Solution**: Use `--show-spec` to review the architect's decisions

**Problem**: "Too many recommendations, hard to choose"
- **Solution**: Use `--filter-learnings 0.85` to show only high-confidence (85%+) patterns

**Problem**: "Learning from failed attempt is being suggested"
- **Solution**: Patterns drop in confidence after failures. Use `/curriculum --delete-learning <id>` to remove bad patterns

**Problem**: "Embedding similarity seems wrong"
- **Solution**: Run `/curriculum --recompute-embeddings` to refresh similarity scores

---

## Next Steps

1. **Use memory from Day 1**: Run features, collect learnings
2. **Monitor confidence**: Check `/curriculum --list-learnings` monthly
3. **Share learnings**: Export patterns to team with `/curriculum --export`
4. **Customize threshold**: Adjust similarity threshold (default 0.7) for your taste
5. **Iterate**: Each successful generation makes the system smarter

**Key insight**: The more you use one-shot-prompting, the smarter it becomes. Memory transforms it from a one-shot tool into a learning system that improves over time.
