---
type: guide
last_verified: 2026-05-20
owner: claude
---

# MCP GitHub Approval Integration Guide

This guide shows how to wire the zone approval gates to GitHub PR approval workflows using Model Context Protocol (MCP).

## Current State

- **Zone Approval Gate (Stage 2.5)**: Interactive. Asks user: "Approve spec? [y/n/s]"
- **Approval Gate (Stage 5.9)**: Autonomous. POSTs to webhook, polls callback.
- **MCP GitHub Approval**: Skeleton server at `scripts/mcp_github_approval.py`

This guide shows the **optional wiring** to integrate zones with GitHub.

## The Pattern

```
┌─────────────────┐
│ Zone Gate       │
│ (Stage 2.5)     │
└────────┬────────┘
         │
         ├─ Interactive mode: ask user [y/n/s]
         │
         └─ GitHub mode: POST approval request to PR
              ↓
         ┌──────────────────┐
         │ MCP GitHub Srv   │
         │ (skeleton)       │
         └────────┬─────────┘
                  │
                  ├─ POST comment to PR
                  │
                  └─ Poll for approval (@bot approve/@bot deny/@bot revise)
                       ↓
         ┌──────────────────┐
         │ Zone Gate        │
         │ (resume)         │
         └──────────────────┘
```

## Setup Instructions

### 1. Enable MCP GitHub Approval (Optional)

If you want zone gates to integrate with GitHub PRs:

```bash
# Check if MCP is configured in your Claude Code settings
cat ~/.claude/settings.json | grep -A5 mcp

# If not present, add MCP server section:
{
  "mcp": {
    "servers": {
      "github-approval": {
        "command": "python",
        "args": ["skills/one-shot-generator/scripts/mcp_github_approval.py", "server"],
        "env": {
          "GITHUB_TOKEN": "$GITHUB_TOKEN",
          "GITHUB_REPO": "owner/repo"
        }
      }
    }
  }
}
```

### 2. Configure GitHub Token

```bash
# Add your GitHub personal access token to environment
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
export GITHUB_REPO=owner/repo
```

### 3. Test the Skeleton (No GitHub Required)

```bash
# Simulate an approval request → decision flow
python skills/one-shot-generator/scripts/mcp_github_approval.py simulate

# Output:
# [MCP] Simulating approval flow for PR #123
# [MCP] Comment:
# ## Zone Approval Gate — PLAN → BUILD
# ...
# Decision: approved
```

### 4. Use in Zone Gates (Future)

When you invoke `/one-shot`, if `GITHUB_TOKEN` and `GITHUB_REPO` are set:

```bash
/one-shot "add payment API" @./my-project --github-approval
```

The zone gate will:
1. Generate spec.json (architect stage)
2. POST approval request as a GitHub PR comment
3. Wait for approval (@bot approve / @bot deny / @bot revise)
4. Resume code generation based on decision

## MCP Server API (Skeleton)

The skeleton implements these operations:

### POST /approval/request

Send an approval request to a GitHub PR.

**Request:**
```json
{
  "pr_number": 123,
  "repo": "owner/repo",
  "spec_summary": "Add shopping cart",
  "cost_estimate": "$0.45",
  "entities": ["ShoppingCart", "LineItem"]
}
```

**Response:**
```json
{
  "status": "pending",
  "comment_url": "https://github.com/owner/repo/pull/123#comment-xxx",
  "timeout_at": "2026-05-20T14:30:00Z"
}
```

### GET /approval/decision

Poll for approval decision from PR comments.

**Request:**
```json
{
  "pr_number": 123,
  "repo": "owner/repo"
}
```

**Response:**
```json
{
  "status": "approved|denied|pending",
  "decided_by": "github-username",
  "comment": "Looks good! @bot approve",
  "decided_at": "2026-05-20T14:25:00Z"
}
```

## Approval Commands (GitHub PR Comments)

Approvers reply to the zone gate comment with:

- **`@bot approve`** — Proceed to BUILD zone (code generation)
- **`@bot deny`** — Abort this run
- **`@bot revise`** — Return to architect, revise spec

Example:
```
@bot approve

Spec looks good, the FK relationships are correct and the cost estimate is reasonable.
```

## Known Limitations (Skeleton)

1. **No real GitHub API calls yet** — `mcp_github_approval.py` is a skeleton showing the pattern
2. **No OAuth/auth** — requires `GITHUB_TOKEN` env var (personal access token)
3. **No timeout handling** — skeleton polls indefinitely
4. **Single PR only** — hardcoded to one repo
5. **No concurrency** — one approval request at a time

## Roadmap

- [ ] Real GitHub API integration (POST comment, poll PR comments)
- [ ] OAuth flow (no personal token required)
- [ ] Timeout with graceful exit
- [ ] Multi-repo support
- [ ] Concurrent approvals
- [ ] Slack integration (alternative to GitHub)
- [ ] PagerDuty escalation (for production changes)

## See Also

- `scripts/mcp_github_approval.py` — MCP server skeleton
- `scripts/zone_approval_gate.py` — Interactive zone gate
- `scripts/approval_gate.py` — Autonomous approval (Stage 5.9)
- `stages/plan.md` Stage 2.5 — Zone approval gate invocation
