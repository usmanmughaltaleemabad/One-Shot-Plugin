---
type: plan
last_verified: 2026-05-17
owner: claude
---

# Phase 3: Marketplace & Ecosystem (Months 6-12)

**Goal**: Build network effects through agent/skill marketplace.

**Target**: 50-100k paying teams, $2-5M ARR, 500+ published agents

---

## Marketplace Architecture

### Core Components

```
Marketplace Platform:
├── Discovery (web + CLI)
├── Payment Processing (Stripe)
├── Agent Hosting (private agents)
├── Rating/Review System
├── Creator Tools (publish, analytics)
└── Revenue Sharing (70% creators, 30% platform)
```

### How It Works

**For Users**:
```
1. Browse marketplace (web or CLI)
2. Install agent: `claude agent install @creator/my-agent`
3. Use: `/call:my-agent @/path`
4. Provide feedback: rate, review, report issues
```

**For Creators**:
```
1. Create agent (markdown file)
2. Publish to marketplace: `claude agent publish`
3. Set price: $0 (free) or $5-50/month (paid)
4. Earn: 70% of subscription revenue
5. Analytics: see installs, usage, ratings
```

---

## Phase 3 Deliverables

### 1. Marketplace Platform
**Frontend**: Web app for discovery
- Search/browse agents by category
- Ratings and reviews
- Creator profiles
- Install button

**Backend**: API for marketplace operations
- Agent registry (metadata, versions)
- Payment processing (Stripe)
- Subscription management
- Usage tracking

**Database**: Store agents, users, transactions
- Agents table (name, creator, version, price)
- Users table (email, team, subscription)
- Transactions table (for revenue sharing)
- Ratings table (agent_id, user_id, rating, review)

### 2. Freemium Model
**Free Tier**:
- Core ONE SHOT PLUGIN (all 177 modules)
- 5 public agents (pre-built: code-reviewer, architect, test-gen, security, performance)
- Personal use (up to 5 team members)
- Basic analytics

**Paid Tier** ($15-25/mo per user):
- Unlimited agents/skills
- Private agent hosting (publish private agents)
- Team management (permissions, audit)
- Advanced analytics
- Priority support

**Enterprise** ($5-50k/mo):
- Custom SLA
- Dedicated agent development
- White-label agents
- Compliance + audit trails
- Quarterly business reviews

### 3. Agent Publishing System

**CLI Command**:
```bash
claude agent publish                    # Publish to marketplace
claude agent publish --private          # Private marketplace only
claude agent publish --version 1.1.0   # Version management
```

**Agent Metadata** (agent.yaml):
```yaml
name: my-awesome-agent
description: Does something amazing
author: your-name
version: 1.0.0
price: 9.99                            # Monthly USD (0 = free)
category: code-review
keywords: [quality, security, testing]
```

### 4. Revenue Sharing Model

**Commission**: 70% creator, 30% platform

**Example**:
- Agent price: $9.99/month
- 100 users subscribe
- Monthly revenue: $999
- Creator gets: $699.30
- Platform gets: $299.70

**Payment Schedule**: Monthly via Stripe (creator's account)

### 5. Featured Agents Program

**Criteria**:
- 4.5+ star rating
- 100+ users
- Regular updates
- Positive reviews

**Benefits**:
- Featured on marketplace homepage
- Boost in search results
- Marketing support
- Early access to new features

### 6. CLI Integration

**Install Agent**:
```bash
claude agent install @creator/my-agent
# Downloads agent to ~/.claude/agents-marketplace/
```

**List Installed**:
```bash
claude agent list
# Shows: code-reviewer (built-in), my-agent (installed), ...
```

**Use Agent**:
```bash
/call:my-agent @/path/to/file
# Works same as built-in agents
```

---

## Implementation Timeline (Months 6-12)

### Month 6: Core Marketplace Platform
- [ ] Design marketplace architecture
- [ ] Build web frontend (React/Next.js)
- [ ] Build API backend (Python/Node.js)
- [ ] Set up database
- [ ] Integrate Stripe payment
- [ ] Deploy marketplace.claude-code-studio.com

### Month 7: Agent Publishing
- [ ] Create CLI publish command
- [ ] Implement agent versioning
- [ ] Build creator dashboard
- [ ] Set up revenue tracking
- [ ] Create agent submission guidelines

### Month 8: Featured Agents Program
- [ ] Build featured agent selection
- [ ] Create marketing strategy
- [ ] Identify 10-20 quality agents to feature
- [ ] Launch featured agents on homepage
- [ ] Create creator rewards program

### Month 9: Integration & Expansion
- [ ] Integrate with One-Shot (suggest agents)
- [ ] Create agent discovery via CLI: `claude agent search`
- [ ] Build rating/review system
- [ ] Launch creator analytics dashboard
- [ ] Partner with popular agent creators

### Month 10: Monetization Launch
- [ ] Announce freemium model
- [ ] Convert early users to paid tiers
- [ ] Onboard 100+ paying teams
- [ ] Publish revenue sharing terms
- [ ] Create case studies

### Month 11-12: Growth & Optimization
- [ ] Scale marketplace (handle 500+ agents)
- [ ] Optimize discovery (search, recommendations)
- [ ] Improve payment flow
- [ ] Add agent categories/tags
- [ ] Launch creator program v2

---

## Success Metrics (Month 12)

| Metric | Target | Success |
|--------|--------|---------|
| **Published agents** | 500+ | Mix of free and paid |
| **Paying teams** | 50-100k | $15-25/mo subscription |
| **Enterprise contracts** | 10-20 | $5-50k/mo |
| **Monthly revenue** | $2-5M | ARR growing 15%+ MoM |
| **Marketplace commission** | $500k-1M | 30% of agent subscription revenue |
| **Agent creators** | 100+ | With at least 10+ users each |
| **Avg agent rating** | 4.2+ | Out of 5 stars |
| **NPS** | 45+ | Customer satisfaction |

---

## Architecture Decisions

### Frontend: Agent Discovery
- **Technology**: React/Next.js
- **Hosting**: Vercel or similar
- **Features**: Search, filters, reviews, install button

### Backend: Marketplace API
- **Technology**: Python FastAPI or Node.js
- **Database**: PostgreSQL
- **Hosting**: AWS/GCP/Azure
- **Key endpoints**:
  - GET /agents (search, filter)
  - GET /agents/{id} (details)
  - POST /agents/{id}/install (track install)
  - POST /agents/{id}/rate (submit rating)
  - POST /subscribe (start subscription)

### Payment: Stripe Integration
- **Subscription management**: Stripe Billing
- **Revenue distribution**: Monthly payout to creators
- **Compliance**: PCI DSS, data protection

### CLI Integration: Agent Installation
- **Storage**: ~/.claude/agents-marketplace/
- **Conflict resolution**: Local agents > Marketplace agents > Built-in agents
- **Update check**: Automatic updates for installed agents

---

## Competitive Advantages

1. **Tight harness integration** — Agents work with harness standards
2. **Revenue sharing** — 70/30 split attracts creators
3. **No friction adoption** — One-click install via CLI
4. **Quality control** — Featured agent program ensures quality
5. **Community** — 500+ agents create network effects

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|---|
| **Low agent quality** | High | Featured agent program, rating system |
| **Payment processing fails** | High | Stripe redundancy, manual payout backup |
| **Slow agent discovery** | Medium | Search, recommendations, categories |
| **Creator churn** | Medium | Revenue sharing, support, marketing |
| **Clone agents** | Medium | Review process, creator support |

---

## Go-to-Market (Month 12)

**Launch Event**:
- Announce marketplace with 50+ agents
- Feature top 10 creators
- Give away $50k in founder bounties
- Case studies: "How [Creator] Built a Successful Agent"

**Creator Onboarding**:
- Creator program with benefits
- Revenue sharing guarantees
- Marketing support for featured agents
- Monthly creator meetups (Slack)

**User Growth**:
- "Try new agents this month" campaign
- Recommendation engine (suggest agents based on usage)
- Freemium upgrade path ($0 → $15/mo)

---

## Phase 4 Preparation

At end of Phase 3, we have:
- ✅ Marketplace with 500+ agents
- ✅ 50-100k paying teams
- ✅ $2-5M ARR
- ✅ Network effects (more agents = more value)

Ready for Phase 4: Enterprise Motion (SAML, compliance, premium support)

---

**Status**: Phase 3 Plan Ready  
**Start Date**: Month 6 (immediately after Phase 2)  
**Target Completion**: Month 12 with metrics validation

