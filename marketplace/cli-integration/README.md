---
type: guide
last_verified: 2026-05-17
owner: claude
---

# CLI Marketplace Integration

CLI commands for discovering, installing, and managing marketplace agents in Claude Code.

## User Commands

### Discover Agents

```bash
# Search agents
claude agent search "code review"
  # Shows: code-reviewer, pr-reviewer, commit-reviewer

# Browse by category
claude agent list --category code-review
  # Lists all code review agents

# Get agent details
claude agent info @creator/agent-name
  # Shows: description, price, rating, install count, creator

# View agent versions
claude agent versions @creator/agent-name
  # Lists all published versions
```

### Install & Manage

```bash
# Install free agent
claude agent install @creator/code-reviewer
  # Downloads to ~/.claude/agents-marketplace/

# Subscribe to paid agent
claude agent install @creator/premium-agent
  # Prompts: "Subscribe for $9.99/month? [y/n]"
  # Completes Stripe Checkout flow
  # Installs after payment confirmed

# List installed agents
claude agent list
  # Shows built-in agents + installed agents + subscriptions

# Update installed agent
claude agent update @creator/code-reviewer
  # Checks for newer versions
  # Automatic or prompt user

# Uninstall/cancel
claude agent remove @creator/code-reviewer
  # For paid agents: confirm cancellation
  # Uninstalls local version

# Show installed agent details
claude agent info @creator/code-reviewer
  # Shows: installed version, creator, usage stats
```

### Use Agent

```bash
# Call installed agent (works like built-in agents)
/call:code-reviewer @/path/to/file

# Or in one-shot generation
/one-shot-prompting:one-shot-generator "Add tests" @/project
  # Automatically uses installed code-gen agents
```

### Creator Commands

```bash
# Publish agent to marketplace
claude agent publish
  # Interactive: name, description, category, price
  # Creates agent.yaml + markdown file
  # Uploads to marketplace
  # Status: draft → published

# Update agent
claude agent publish --update
  # Bump version, update description
  # Publish new version

# View analytics
claude agent analytics
  # Shows: installs, active subscriptions, revenue
  # This month vs last month
  # Top reviewer comments

# View payouts
claude agent payouts
  # Shows: payment history, next payout date
  # Monthly revenue split (70% creator, 30% platform)

# Deprecate agent
claude agent deprecate @creator/old-agent
  # Marks as deprecated
  # Notifies existing users
  # Still available but hidden from search
```

## Implementation

### 1. Agent Installation Flow

```
User: `claude agent install @creator/code-reviewer`
  ↓
CLI: Check if free or paid
  ├─ Free: Download from marketplace
  ├─ Paid: Open Stripe Checkout
  │   ↓
  │   User completes payment
  │   ↓
  │   Webhook confirms subscription
  │   ↓
  │   Download agent
  └─ Success: "✅ Installed"

Files:
  ~/.claude/agents-marketplace/
    ├── creator-code-reviewer/
    │   ├── code-reviewer.md (agent definition)
    │   └── metadata.json (version, subscription_id)
    └── ...
```

### 2. Agent Loading Priority

```
1. Local agents ~/.claude/agents/
2. Marketplace agents ~/.claude/agents-marketplace/
3. Built-in agents ~/.claude/agents-library/

When user runs: /call:agent-name
  Find in order above, use first match
```

### 3. Subscription Management

```
On startup, CLI checks:
  - Marketplace agents with active subscriptions
  - Stripe status for each subscription
  - If subscription expired/canceled: mark for removal
  - If subscription valid: load agent normally
  
Monthly webhook from Stripe:
  - customer.subscription.updated
  - customer.subscription.deleted
  - Updates local subscription metadata
  - Removes agents with canceled subs
```

### 4. Agent Registry Sync

```
~/.claude/agents-marketplace/registry.json:
{
  "last_sync": "2026-05-17T14:30:00Z",
  "agents": [
    {
      "name": "code-reviewer",
      "creator": "creator",
      "version": "1.2.0",
      "installed_version": "1.2.0",
      "subscription_id": "sub_..." (if paid),
      "free": false,
      "url": "https://marketplace.claude-code-studio.com/agents/creator/code-reviewer"
    },
    ...
  ]
}

Update registry:
  - On `claude agent list`
  - On `claude agent search`
  - Daily background sync (if online)
```

## File Structure

```
marketplace/cli-integration/
├── commands/
│   ├── search.py             # claude agent search
│   ├── list.py               # claude agent list
│   ├── install.py            # claude agent install
│   ├── publish.py            # claude agent publish
│   ├── analytics.py          # claude agent analytics
│   └── remove.py             # claude agent remove
├── services/
│   ├── registry_service.py   # Agent registry management
│   ├── marketplace_client.py # API client
│   ├── stripe_client.py      # Stripe integration
│   ├── agent_loader.py       # Load/execute agents
│   └── version_manager.py    # Version handling
├── models/
│   ├── agent.py              # Agent metadata
│   ├── subscription.py       # Subscription state
│   └── config.py             # Configuration
├── tests/
│   └── test_install.py       # Integration tests
└── README.md
```

## Configuration

File: `~/.claude/marketplace-config.json`

```json
{
  "marketplace_url": "https://marketplace.claude-code-studio.com",
  "api_key": "pk_live_...",
  "stripe_public_key": "pk_live_...",
  "auto_update": true,
  "update_check_interval": 86400,
  "cache_agents": true,
  "last_sync": "2026-05-17T14:30:00Z"
}
```

## Webhooks

Stripe webhooks → CLI local sync:

```
Stripe Event                    → Local Action
charge.succeeded               → Update subscription status
customer.subscription.updated  → Sync new version
customer.subscription.deleted  → Mark for removal
```

---

**Status**: Phase 3 CLI Integration  
**Timeline**: Months 6-12  
**Target**: Seamless agent discovery & installation
