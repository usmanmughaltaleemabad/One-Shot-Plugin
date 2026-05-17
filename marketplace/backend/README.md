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

### Agents

```
GET    /api/v1/agents                    # List with filters
GET    /api/v1/agents/{id}               # Get details
POST   /api/v1/agents/publish            # Publish new agent
PUT    /api/v1/agents/{id}               # Update agent metadata
GET    /api/v1/agents/{id}/versions      # Version history
POST   /api/v1/agents/{id}/rate          # Submit rating/review
```

### Subscriptions

```
POST   /api/v1/subscribe                 # Start subscription
DELETE /api/v1/subscriptions/{id}        # Cancel subscription
GET    /api/v1/subscriptions/{id}        # Get subscription status
```

### Users & Authentication

```
POST   /api/v1/auth/signup               # Register
POST   /api/v1/auth/login                # Login
GET    /api/v1/me                        # Current user profile
POST   /api/v1/me/agents                 # Creator dashboard
```

### Payments & Revenue

```
GET    /api/v1/creators/{id}/analytics   # Creator metrics
GET    /api/v1/creators/{id}/payouts     # Payout history
POST   /api/v1/webhooks/stripe           # Stripe webhook
```

## Architecture

```
marketplace/backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── agents.py         # Agent endpoints
│   │       ├── subscriptions.py  # Subscription endpoints
│   │       ├── auth.py           # Authentication
│   │       └── payments.py       # Payment endpoints
│   ├── models/                   # SQLAlchemy models
│   │   ├── agent.py
│   │   ├── user.py
│   │   ├── subscription.py
│   │   ├── rating.py
│   │   └── transaction.py
│   ├── services/                 # Business logic
│   │   ├── agent_service.py
│   │   ├── subscription_service.py
│   │   ├── payment_service.py
│   │   └── analytics_service.py
│   ├── schemas/                  # Pydantic models
│   ├── database.py               # SQLAlchemy setup
│   └── main.py                   # FastAPI app
├── migrations/                   # Alembic migrations
├── tests/                        # Test suite
├── requirements.txt
├── .env.example
├── alembic.ini
└── README.md
```

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
