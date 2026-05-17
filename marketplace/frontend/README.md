---
type: guide
last_verified: 2026-05-17
owner: claude
---

# Marketplace Frontend

Next.js/React frontend for ONE SHOT PLUGIN marketplace discovery and management.

## Quick Start

```bash
# Setup
cd marketplace/frontend
npm install

# Development
npm run dev
# Open http://localhost:3000

# Build
npm run build

# Production
npm start

# Tests
npm test
```

## Features

### Public Pages
- **Home**: Featured agents, categories, search
- **Agent Details**: Description, reviews, creator profile, install button
- **Creator Profile**: Portfolio, earnings, agent list
- **Search & Explore**: Full-text search, category filters, ratings

### Authenticated Pages
- **Dashboard**: My agents, installs, revenue
- **Creator Dashboard**: Analytics, payouts, agent management
- **Settings**: Profile, billing, API keys

## Architecture

```
marketplace/frontend/
├── pages/
│   ├── index.tsx                 # Home page
│   ├── agents/
│   │   ├── index.tsx             # Agent list/search
│   │   └── [id].tsx              # Agent details
│   ├── creators/
│   │   └── [id].tsx              # Creator profile
│   ├── dashboard/
│   │   ├── index.tsx             # User dashboard
│   │   ├── agents.tsx            # Creator agent management
│   │   └── analytics.tsx         # Revenue analytics
│   └── api/                       # API routes
├── components/
│   ├── AgentCard.tsx             # Agent listing card
│   ├── SearchBar.tsx             # Search interface
│   ├── RatingStars.tsx           # Star ratings
│   ├── SubscribeButton.tsx       # Subscribe action
│   └── ...
├── lib/
│   ├── api.ts                    # API client
│   ├── auth.ts                   # Authentication
│   └── stripe.ts                 # Stripe integration
├── styles/                        # CSS/Tailwind
├── public/                        # Static assets
└── package.json
```

## Key Pages

### Home Page
- Featured agents section (4-5 top-rated agents)
- Category browse
- Search bar
- Create Agent CTA (for registered users)

### Agent Details
- Agent metadata (name, description, creator, version)
- Rating & reviews
- Install/Subscribe button
- Creator profile card
- Pricing (free vs paid)
- Changelog/version history

### Creator Dashboard
- My agents list (draft, published, deprecated)
- Analytics: installs, active subscriptions, revenue
- Publish new agent form
- Manage versions
- Payout history

### Search & Browse
- Full-text search
- Filter by: category, price (free/paid), rating, date
- Sort by: popularity, rating, newest, trending
- Display results in grid/list

## Components

```
AgentCard
  - Thumbnail
  - Name, creator
  - Rating & reviews count
  - Price / Free badge
  - Install count
  - Preview/Details link

SearchBar
  - Text input
  - Category dropdown
  - Price filter
  - Rating filter
  - Search button

RatingStars
  - Display: 4.2 ★★★★☆
  - Interactive: click to rate (logged-in users)

SubscribeButton
  - Free agent: "Install" button
  - Paid agent: "Subscribe $X/mo" + Stripe Checkout
  - Installed: "Manage subscription"

CreatorProfile
  - Creator avatar & name
  - Agent count
  - Total revenue (if user)
  - "Follow" button (future feature)
  - Link to creator's profile page
```

## API Integration

Connects to backend at `/api/v1/`:

```typescript
// Get agents list
GET /api/v1/agents?search=...&category=...&sort=rating&page=1

// Get agent details
GET /api/v1/agents/{id}

// Get ratings
GET /api/v1/agents/{id}/ratings

// Create subscription
POST /api/v1/subscribe
  { "agent_id": "uuid" }

// Creator dashboard
GET /api/v1/me/agents
GET /api/v1/creators/{id}/analytics
```

## Authentication

- Signup/Login via email
- JWT token storage in httpOnly cookies
- Protected routes (creator dashboard, etc.)
- OAuth integration (GitHub, Google) - future

## Styling

- **Framework**: Tailwind CSS
- **Components**: Headless UI / Radix UI
- **Icons**: Heroicons
- **Dark mode**: Supported

## Development

### Add New Agent Listing Page
1. Create `pages/agents/[id].tsx`
2. Fetch agent data from API
3. Display metadata, ratings, reviews
4. Implement Subscribe button

### Add Creator Dashboard
1. Create `pages/dashboard/agents.tsx`
2. Fetch user's agents from API
3. List agents with edit/publish/delete actions
4. Show analytics for each agent

### Testing
```bash
npm run test                    # Jest
npm run test:e2e               # Playwright
npm run test:coverage          # Coverage report
```

---

**Status**: Phase 3 Marketplace Frontend  
**Timeline**: Months 6-12  
**Target**: Serve 50-100k paying users
