---
type: guide
last_verified: 2026-05-17
owner: claude
---

# Marketplace Backend API

FastAPI backend for ONE SHOT PLUGIN marketplace platform.

## Quick Start

```bash
# Setup
cd marketplace/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
export DATABASE_URL="postgresql://..."
export STRIPE_SECRET_KEY="sk_test_..."

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload

# Run tests
pytest --cov=app
```

## API Endpoints

### Agents (marketplace-catalog)

```
GET    /api/v1/agents                      # List with search/filters
GET    /api/v1/agents/{agent_id}           # Get agent details
POST   /api/v1/agents                      # Create agent (creator)
PUT    /api/v1/agents/{agent_id}           # Update agent metadata
POST   /api/v1/agents/{agent_id}/ratings   # Submit rating (1-5 stars)
GET    /api/v1/agents/{agent_id}/ratings   # Get agent ratings
```

Query parameters for listing:
- `search` - text search on name/description/keywords
- `category` - filter by category
- `min_rating` - minimum rating 0-5 (default: 0)
- `max_price` - maximum price in cents
- `sort_by` - rating, newest, popular, price (default: rating)
- `page` - page number (default: 1)
- `page_size` - results per page 1-100 (default: 20)

### Authentication

```
POST   /api/v1/auth/signup                # Register new user
POST   /api/v1/auth/login                 # Login (returns JWT)
GET    /api/v1/auth/me                    # Get current user profile
```

### Subscriptions

```
POST   /api/v1/subscriptions              # Create subscription
DELETE /api/v1/subscriptions/{id}         # Cancel subscription
GET    /api/v1/subscriptions/{id}         # Get subscription status
GET    /api/v1/subscriptions              # List user's subscriptions
```

### Payments & Analytics

```
POST   /api/v1/payments/webhooks/stripe   # Stripe webhook (events)
GET    /api/v1/payments/creators/{id}/analytics   # Creator metrics
GET    /api/v1/payments/creators/{id}/payouts     # Payout history
```

## Architecture

```
marketplace/backend/
├── app/
│   ├── api_agents.py             # Agent discovery & publishing endpoints
│   ├── api_auth.py               # Authentication (signup/login)
│   ├── api_subscriptions.py       # Subscription management
│   ├── api_payments.py            # Stripe webhooks & analytics
│   ├── models.py                  # SQLAlchemy ORM models
│   │   ├── User                   # Users + creators
│   │   ├── Agent                  # Published agents
│   │   ├── AgentVersion           # Version history
│   │   ├── Subscription           # User subscriptions
│   │   ├── Rating                 # Community reviews
│   │   ├── Transaction            # Financial audit trail
│   │   └── Payout                 # Monthly creator payouts
│   ├── schemas.py                 # Pydantic validation models
│   └── database.py                # AsyncSession setup (PostgreSQL + asyncpg)
├── alembic/
│   ├── env.py                     # Migration environment
│   ├── script.py.mako             # Migration template
│   └── versions/
│       └── 001_initial_schema.py  # Create all tables
├── main.py                        # FastAPI app entry
├── requirements.txt               # Dependencies
├── alembic.ini                    # Alembic config
├── .env.example                   # Environment template
└── README.md
```

### Database Models

**User** - marketplace users + creators
- id (UUID)
- email, name, password_hash
- is_creator (boolean), stripe_customer_id, stripe_account_id
- bio, avatar_url, is_active

**Agent** - published agents
- id, creator_id, name, slug (creator/name)
- description, markdown_content, category, keywords
- price_usd (cents, 0=free), status (draft/published/deprecated)
- rating, rating_count, install_count
- version, is_public, published_at

**Subscription** - active subscriptions
- id, user_id, agent_id
- stripe_subscription_id, status (active/canceled/past_due)
- price_usd (locked at time of subscription)
- started_at, current_period_end, canceled_at

**Rating** - community reviews
- id, agent_id, user_id
- rating (1-5), review (optional)
- helpful_count

**Transaction** - financial records
- id, type (subscription_created/payment_succeeded/payout)
- user_id, agent_id
- amount_usd, platform_fee_usd, creator_payout_usd
- stripe_charge_id, stripe_transaction_id

**Payout** - monthly creator payouts
- id, creator_id, month, year
- total_revenue_usd, platform_fee_usd, amount_paid_usd
- stripe_payout_id, status (pending/completed/failed)

## Data Models

### Agent
```python
{
  "id": "uuid",
  "name": "code-reviewer",
  "slug": "creator/code-reviewer",
  "description": "Comprehensive code review agent",
  "author_id": "uuid",
  "version": "1.0.0",
  "price": 9.99,  # Monthly USD, 0 = free
  "category": "code-review",
  "keywords": ["quality", "security"],
  "markdown_content": "...",
  "rating": 4.7,
  "install_count": 1250,
  "status": "published",  # draft | published | deprecated
  "created_at": "2026-05-17T...",
  "updated_at": "2026-05-17T..."
}
```

### Subscription
```python
{
  "id": "uuid",
  "user_id": "uuid",
  "agent_id": "uuid",
  "status": "active",  # active | canceled | expired
  "price_per_month": 9.99,
  "stripe_subscription_id": "sub_...",
  "started_at": "2026-05-17T...",
  "renews_at": "2026-06-17T...",
  "canceled_at": null
}
```

### Rating
```python
{
  "id": "uuid",
  "agent_id": "uuid",
  "user_id": "uuid",
  "rating": 5,  # 1-5 stars
  "review": "Excellent agent, saves hours!",
  "created_at": "2026-05-17T..."
}
```

## Key Features

### 1. Agent Publishing
- Submit agent with metadata (name, description, category, price)
- Automatic versioning (semver)
- Draft → Published workflow
- Version history tracking

### 2. Payment Processing
- Stripe Billing integration
- Monthly subscription management
- Automatic payouts (70% to creator, 30% to platform)
- Invoice generation

### 3. Discovery & Search
- Full-text search on agent name, description, keywords
- Filter by category, price, rating
- Sort by popularity, rating, newest
- Recommended agents algorithm

### 4. Analytics
- Creator dashboard: installs, usage, revenue
- User dashboard: installed agents, spending
- Platform analytics: total revenue, top agents, user growth

### 5. Rating & Reviews
- 1-5 star ratings
- User reviews with text
- Helpful voting on reviews
- Abuse reporting

## Development

### Run Tests
```bash
pytest --cov=app --cov-report=html
```

### Create Database Migrations
```bash
alembic revision --autogenerate -m "add agent table"
alembic upgrade head
```

### Development Checklist
- [ ] All endpoints tested (pytest)
- [ ] 80%+ code coverage
- [ ] Async/await throughout (no blocking I/O)
- [ ] Input validation on all endpoints
- [ ] Error handling with proper status codes
- [ ] Stripe sandbox testing complete

---

**Status**: Phase 3 Marketplace Backend  
**Timeline**: Months 6-12  
**Target**: Handle 500+ agents, $2-5M ARR
