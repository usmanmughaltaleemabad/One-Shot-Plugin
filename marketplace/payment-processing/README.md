---
type: guide
last_verified: 2026-05-17
owner: claude
---

# Payment Processing & Revenue Sharing

Stripe integration for subscription billing and creator revenue distribution.

## Subscription Model

### Pricing Tiers

**Free Agents**
- Price: $0/month
- No subscription required
- Direct download & install

**Paid Agents**
- Price: $5-50/month (set by creator)
- Monthly recurring subscription via Stripe
- Cancel anytime

**Enterprise Pricing**
- Custom: $500-50k/month
- Annual billing available
- White-label options
- Dedicated support

### Example

Agent: "code-reviewer-enterprise"
- Creator: company-x
- Price: $19.99/month
- Subscribers: 150 teams
- Monthly revenue: $2,999.50
- Creator gets: $2,099.65 (70%)
- Platform gets: $899.85 (30%)

## Stripe Integration

### 1. Customer Management

```python
# Create/update customer
stripe.Customer.create(
    email=user.email,
    name=user.name,
    metadata={"user_id": user.id}
)

# Store stripe_customer_id in database
user.stripe_customer_id = customer.id
```

### 2. Product & Price Setup

```python
# Create product for agent
product = stripe.Product.create(
    name="code-reviewer",
    description="Comprehensive code review agent",
    metadata={
        "agent_id": agent.id,
        "creator_id": creator.id
    }
)

# Create price
price = stripe.Price.create(
    product=product.id,
    type="recurring",
    recurring={"interval": "month", "interval_count": 1},
    unit_amount=1999,  # $19.99 in cents
    currency="usd"
)
```

### 3. Subscription Creation

```python
# When user subscribes
subscription = stripe.Subscription.create(
    customer=customer.stripe_id,
    items=[{"price": price.id}],
    payment_behavior="error_if_incomplete",
    metadata={
        "agent_id": agent.id,
        "user_id": user.id
    }
)

# Save to database
Subscription.create(
    user_id=user.id,
    agent_id=agent.id,
    stripe_subscription_id=subscription.id,
    status="active",
    renews_at=subscription.current_period_end
)
```

### 4. Webhook Handling

```python
# Process Stripe webhooks
@app.post("/api/v1/webhooks/stripe")
async def stripe_webhook(request: Request):
    event = stripe.Event.construct_from(
        json.loads(await request.body()), 
        stripe.api_key
    )
    
    if event["type"] == "customer.subscription.updated":
        # Update subscription status
        handle_subscription_updated(event)
    
    elif event["type"] == "customer.subscription.deleted":
        # Handle cancellation
        handle_subscription_canceled(event)
    
    elif event["type"] == "invoice.payment_succeeded":
        # Update revenue, trigger payout
        handle_payment_succeeded(event)
    
    return {"status": "ok"}
```

## Revenue Distribution

### Monthly Process

```
Month N Subscriptions:
├── Collect all active subscriptions
├── Calculate amounts
│   ├── Stripe processing fee: ~2.9% + $0.30
│   ├── Platform revenue: 30%
│   └── Creator payout: 70% (after Stripe fee)
├── Create payout batch
└── Execute via Stripe Connect

Example:
  Subscription: $19.99/month
  - Stripe fee: $1.20 (2.9% + $0.30)
  - Net: $18.79
  - Platform (30%): $5.64
  - Creator (70%): $13.15
```

### Payout Schedule

```
Day 1-5:   Calculate revenue from previous month
Day 5-10:  Generate invoices (internal tracking)
Day 10:    Execute payouts via Stripe
Day 10-15: Creators receive funds in their bank accounts
```

### Creator Payout Account

```python
# Create Stripe Connect account for creator
creator.stripe_account_id = stripe.Account.create(
    type="express",
    country="US",
    email=creator.email,
    capabilities={
        "card_payments": {"requested": True},
        "transfers": {"requested": True}
    }
).id

# Payout to creator's Stripe account
transfer = stripe.Transfer.create(
    amount=int(creator_payout * 100),  # cents
    currency="usd",
    destination=creator.stripe_account_id,
    metadata={"month": month, "agent_ids": [agent_ids]}
)
```

## Compliance & Security

### PCI DSS Compliance
- Never handle raw credit card data (Stripe handles it)
- Use hosted Stripe Checkout
- Tokenize cards on client-side

### Fraud Prevention
```python
# Validate amount
if amount < 499 or amount > 5000000:
    raise ValueError("Invalid subscription amount")

# Check for duplicate recent charges
recent_charges = Subscription.filter(
    user_id=user.id,
    created_at__gte=now() - timedelta(minutes=5)
)
if recent_charges:
    raise ValueError("Duplicate subscription attempt")

# Log all financial transactions
FinancialLog.create(
    type="subscription_created",
    user_id=user.id,
    agent_id=agent.id,
    amount=price.unit_amount / 100,
    stripe_charge_id=subscription.latest_invoice.charge
)
```

### Data Protection
- Minimal PII storage (email, name only)
- Encrypt stripe_customer_id at rest
- Audit logging for all financial operations
- GDPR compliant data retention (6 years for tax)

## Database Schema

```sql
-- Products (Stripe synced)
CREATE TABLE stripe_products (
    id UUID PRIMARY KEY,
    stripe_product_id VARCHAR UNIQUE,
    agent_id UUID REFERENCES agents(id),
    name VARCHAR NOT NULL,
    metadata JSON,
    created_at TIMESTAMP
);

-- Prices (Stripe synced)
CREATE TABLE stripe_prices (
    id UUID PRIMARY KEY,
    stripe_price_id VARCHAR UNIQUE,
    product_id UUID REFERENCES stripe_products(id),
    unit_amount INTEGER,  -- cents
    currency VARCHAR(3),
    recurring_interval VARCHAR,
    created_at TIMESTAMP
);

-- Subscriptions
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    agent_id UUID REFERENCES agents(id),
    stripe_subscription_id VARCHAR UNIQUE,
    status VARCHAR,  -- active, past_due, canceled, unpaid
    started_at TIMESTAMP,
    current_period_end TIMESTAMP,
    canceled_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Transactions (for reporting)
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    type VARCHAR,  -- subscription_created, payment_succeeded, payout
    user_id UUID,
    agent_id UUID,
    amount DECIMAL(10, 2),
    platform_fee DECIMAL(10, 2),
    creator_payout DECIMAL(10, 2),
    stripe_charge_id VARCHAR,
    metadata JSON,
    created_at TIMESTAMP
);

-- Payouts (to creators)
CREATE TABLE payouts (
    id UUID PRIMARY KEY,
    creator_id UUID REFERENCES users(id),
    stripe_payout_id VARCHAR,
    month INTEGER,
    year INTEGER,
    total_revenue DECIMAL(10, 2),
    platform_fee DECIMAL(10, 2),
    amount_paid DECIMAL(10, 2),
    status VARCHAR,  -- pending, completed, failed
    paid_at TIMESTAMP
);
```

## Testing

### Stripe Test Mode
```python
# Use test keys in development
STRIPE_SECRET_KEY = "sk_test_..."

# Test credit cards
TEST_CARDS = {
    "success": "4242 4242 4242 4242",
    "decline": "4000 0000 0000 0002",
    "3d_secure": "4000 0025 0000 3155"
}

# Test customer creation
customer = stripe.Customer.create(
    email="test@example.com",
    source="tok_visa"
)

# Verify webhook in test
event = stripe.Event.construct_from({...}, api_key)
```

### Unit Tests
```python
def test_subscription_created():
    """Test subscription creation and database storage."""
    ...

def test_revenue_split():
    """Test 70/30 revenue split calculation."""
    amount = 1999  # $19.99
    platform_fee = 599  # ~30%
    creator_payout = 1400  # ~70%
    assert platform_fee + creator_payout <= amount
```

---

**Status**: Phase 3 Payment Processing  
**Timeline**: Months 6-12  
**Target**: $2-5M ARR with 70/30 creator split
