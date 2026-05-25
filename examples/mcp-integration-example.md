# MCP Integration Example

## Overview

This example shows how one-shot-prompting **discovers and integrates Model Context Protocol (MCP) services** to enhance feature generation. MCP enables Claude to access external tools like GitHub, Linear, Slack, and more—making your feature requests smarter by accessing real project data.

## MCP Service Discovery

### Available MCP Services

The awesome-ai-apps curator agent automatically discovers available MCP services in your workspace:

```bash
/curator --discover-mcp
```

**Output:**
```
🔍 MCP SERVICE DISCOVERY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Discovered MCP Servers:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ GitHub (connected)
   Capabilities:
   - list_issues (get all issues, filter by label/state)
   - search_code (find patterns in your repo)
   - create_pr (create pull requests programmatically)
   - get_file_content (read file content)
   - list_commits (history)
   
   Example usage in generation:
   "Find payment-related issues. If any are open, reference them in docs."

✅ Linear (connected)
   Capabilities:
   - query_issues (search issues, boards, sprints)
   - create_issue (file new issue)
   - get_issue_details (full issue context)
   - add_comment (collaborate)
   
   Example usage in generation:
   "Before generating, check Linear for similar features in progress."

✅ Slack (connected)
   Capabilities:
   - search_messages (find past discussions)
   - post (send updates to team)
   - read_channel (context from conversations)
   - create_thread (reply with status)
   
   Example usage in generation:
   "After generation, post a summary of changes to #engineering."

✅ Notion (connected)
   Capabilities:
   - fetch (read pages and databases)
   - create_pages (document learnings)
   - query_databases (search for specs)
   
   Example usage in generation:
   "Query specs database to find approved designs first."

⚠️  Google Drive (not connected)
   → Requires OAuth. To connect: /curator --auth-mcp google-drive

⚠️  Jira (not connected)
   → Requires API key. To connect: /curator --auth-mcp jira --key XXX

Updated registry: .claude/mcp-registry.json
Timestamp: 2024-05-25T14:32:10Z
Service count: 4 active, 2 available (requires auth)
```

---

## Task: Generate with GitHub Context

Let's say you want to generate a feature but first want to see what GitHub issues are related.

```bash
/one-shot "add payment dispute resolution workflow" @./ecommerce --with-mcp-context
```

---

## Stage 1: Discover Requirements via MCP

**What happens**: The curator agent uses GitHub to find related issues and discussions.

**MCP GitHub search:**
```json
{
  "operation": "search_code",
  "query": "dispute OR refund OR chargeback",
  "in_repo": true
}
```

**Results:**
```
📋 GITHUB SEARCH RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Found Issues:
├─ #127: "Add dispute resolution for Stripe chargebacks" [open, payment]
│  Author: @alice-payments
│  Created: 2024-05-01
│  Context: "Customers report disputes without feedback. Need workflow."
│
├─ #156: "Implement refund audit trail" [open, compliance]
│  Author: @bob-compliance
│  Created: 2024-05-10
│  Context: "Must log all refunds for SOX compliance"
│
└─ #089: "Payment status transitions" [closed, payment] ✓
   Author: @charlie-eng
   Created: 2024-04-15
   Merged: 2024-04-20
   Context: "Defines state machine for payment lifecycle"

Found Code References:
├─ services/payment_processor.py (line 87)
│  "TODO: add dispute handling"
│
└─ models/payment.py (line 42)
│  "status: Enum('pending', 'completed', 'refunded')"
│  → Missing: 'dispute', 'chargeback_resolved'
```

---

## Stage 2: Extract Context from Issues

**What happens**: The analyzer reads full issue details and existing code patterns.

**GitHub Issue Details Extracted:**
```
Issue #127: "Add dispute resolution for Stripe chargebacks"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Requirements:
1. Accept dispute submissions from customers
2. Link disputes to Stripe chargeback events
3. Track dispute status: submitted → under_review → resolved/lost
4. Notify customer of resolution
5. Generate compliance report

Acceptance Criteria:
✓ Customer can submit dispute within 30 days
✓ Admin can review and respond
✓ System logs all interactions
✓ Email notifications sent on status change
✓ Stripe webhook events trigger status updates

Comments:
- @alice-payments (May 5): "Consider Stripe's dispute API lifecycle"
- @bob-compliance (May 8): "SOX requires immutable audit trail"
- @charlie-eng (May 10): "Payment state machine in #089 has transitions"
```

---

## Stage 3: Generate Spec with MCP Context

**What happens**: The architect agent generates spec.json enriched with GitHub context.

**Generated spec.json (with MCP annotations):**
```json
{
  "name": "Dispute Resolution Workflow",
  "description": "Handle Stripe chargebacks and customer disputes",
  "mcp_context": {
    "github_issues": ["#127", "#156", "#089"],
    "related_code": [
      "services/payment_processor.py",
      "models/payment.py"
    ],
    "compliance_notes": "SOX-compliant audit trail required"
  },
  "entities": [
    {
      "name": "Dispute",
      "description": "Customer-initiated or Stripe webhook-initiated dispute",
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
          "name": "stripe_dispute_id",
          "type": "string",
          "unique": true,
          "nullable": true,
          "description": "Stripe dispute ID (if webhook-initiated)"
        },
        {
          "name": "status",
          "type": "enum",
          "enum_values": [
            "submitted",
            "under_review",
            "evidence_requested",
            "won",
            "lost"
          ],
          "default": "submitted"
        },
        {
          "name": "reason",
          "type": "string",
          "description": "Customer's dispute reason"
        },
        {
          "name": "submitted_at",
          "type": "timestamp",
          "auto_set": "now"
        },
        {
          "name": "resolved_at",
          "type": "timestamp",
          "nullable": true
        }
      ]
    },
    {
      "name": "DisputeLog",
      "description": "Immutable audit trail for SOX compliance",
      "attributes": [
        {
          "name": "id",
          "type": "uuid",
          "primary_key": true
        },
        {
          "name": "dispute_id",
          "type": "uuid",
          "foreign_key": true,
          "references": "disputes.id"
        },
        {
          "name": "action",
          "type": "string",
          "description": "What changed (submitted, reviewed, approved, rejected)"
        },
        {
          "name": "actor_id",
          "type": "uuid",
          "nullable": true,
          "description": "Which admin made the change"
        },
        {
          "name": "timestamp",
          "type": "timestamp",
          "auto_set": "now"
        }
      ]
    }
  ],
  "validations": [
    {
      "entity": "Dispute",
      "rule": "Can only be submitted within 30 days of payment",
      "implementation": "submitted_at >= payment.created_at - 30 days"
    },
    {
      "entity": "DisputeLog",
      "rule": "Immutable - no updates allowed",
      "implementation": "Prevent UPDATE/DELETE on disputes_log table"
    }
  ]
}
```

---

## Stage 4: Generate with Full Context

**Code generation now includes:**

✅ **Dispute entity** matches issue #127 requirements
✅ **Audit trail** (DisputeLog) satisfies issue #156 compliance
✅ **State transitions** align with issue #089 design
✅ **Email templates** link from #127 comments

---

## Stage 5: Post Results to GitHub

**What happens**: After generation completes, the wirer posts a summary to the pull request.

**GitHub Comment (auto-posted):**
```markdown
## ✅ Feature: Dispute Resolution Workflow

Generated via one-shot-prompting with MCP context.

### Summary
- **2 new entities**: Dispute, DisputeLog
- **4 new services**: DisputeService, DisputeNotifier, StripeDisputeHandler, ComplianceReporter
- **6 test files**: 47 tests, all passing

### Related Issues
Addresses:
- #127: Dispute resolution workflow ✓
- #156: Refund audit trail ✓
- #089: Payment state transitions (integrated) ✓

### Compliance
- ✅ SOX audit trail (DisputeLog is immutable)
- ✅ 30-day submission window enforced
- ✅ Stripe webhook signature validation
- ✅ Email notifications on status changes

### Next Steps
1. Review `GENERATED_SPEC.json` for schema
2. Run `pytest` to verify all tests pass
3. Check `examples/payment-disputes.md` for workflow walkthrough
4. Deploy to staging with `--apply`

---

_Generated: 2024-05-25 14:35:23 UTC_
_Spec: [view](./GENERATED_SPEC.json) | Cost: $0.42 | Time: 47s_
```

---

## Stage 6: Create Linear Issue for Review

**What happens**: A Linear issue is created to track code review.

**Linear Issue (auto-created):**
```
Title: Code Review: Dispute Resolution Workflow

Description:
Generated via one-shot-prompting on 2024-05-25.

Related:
- GitHub PR #1234
- Issue #127, #156

Requirements Met:
- [x] Customer can submit disputes
- [x] Admin review workflow
- [x] Stripe webhook integration
- [x] Email notifications
- [x] SOX audit trail
- [x] All tests passing

Test Coverage:
- 47 tests
- 92% code coverage
- 0 known issues

Ready for:
- [ ] Code review (assign to @alice)
- [ ] Compliance review (assign to @bob)
- [ ] Performance testing
- [ ] Stage deployment

Priority: High
Due: 2024-05-27
```

---

## Stage 7: Notify Team in Slack

**What happens**: After all stages complete, a message is posted to #engineering.

**Slack Message (auto-posted):**
```
🎉 New Feature: Dispute Resolution Workflow

Generated in 47 seconds using one-shot-prompting with MCP context.

📊 Stats:
• 2 new entities (Dispute, DisputeLog)
• 47 tests, all passing
• 92% code coverage
• Addresses issues #127, #156, #089

🔗 Links:
• [GitHub PR](https://github.com/...)
• [Linear Issue](https://linear.app/...)
• [Spec](./GENERATED_SPEC.json)

Next:
→ Code review (assigned to @alice)
→ Compliance check (assigned to @bob)

Questions? Reply in thread!
```

---

## MCP Integration Benefits

| Feature | Without MCP | With MCP |
|---------|------------|----------|
| **Context discovery** | Manual search | Automated via GitHub/Linear |
| **Related issues** | Might miss context | Auto-linked in spec |
| **Compliance checks** | Manual verification | Checked against Linear requirements |
| **Team notifications** | Slack message (manual) | Auto-posted with results |
| **Issue updates** | Manual GitHub comments | Auto-posted PR comments |
| **Spec quality** | 60% complete | 95% complete |
| **Time to ready** | 2 hours | 5 minutes |

---

## Supported MCP Services

### GitHub (via gh CLI)
```bash
- list_issues: Find open/closed issues by label
- search_code: Find code patterns or TODOs
- create_pr: Create pull request with generated code
- get_file_content: Read existing files for context
- list_commits: Get commit history for patterns
```

### Linear
```bash
- query_issues: Search issues by status/assignee/team
- create_issue: File new issues for needed work
- get_issue_details: Full issue context
- add_comment: Post updates to issues
- update_issue_status: Close/resolve issues
```

### Slack
```bash
- search_messages: Find past discussions
- post: Send announcements to channels
- read_channel: Get context from conversations
- create_thread: Reply with status updates
```

### Notion
```bash
- fetch: Read spec pages and databases
- create_pages: Document generated features
- query_databases: Search for related specs
```

### Google Drive
```bash
- list_files: Find design docs
- read_file: Extract requirements from docs
- create_file: Export generated specs
```

---

## Troubleshooting MCP Integration

**Problem**: "GitHub service not authenticated"
- **Solution**: Run `/curator --auth-mcp github` and follow OAuth flow

**Problem**: "Linear issue query returned 0 results"
- **Solution**: Check that your Linear API key is set. Use `/curator --list-mcp-config`

**Problem**: "Slack post failed - missing channel"
- **Solution**: Add `slack_channel: "#engineering"` to `.claude/one-shot-config.json`

**Problem**: "MCP service timeout during generation"
- **Solution**: Services have 5-second timeout. If slow, use `--skip-mcp` to generate without context

**Problem**: "Can't find related code in GitHub"
- **Solution**: Run `/curator --discover-mcp --verbose` to see search patterns being used

---

## Next Steps

1. **Connect MCP services**: `/curator --discover-mcp`
2. **Generate with context**: `/one-shot "your feature" @./project --with-mcp-context`
3. **Watch results**: Links to GitHub/Linear/Slack posted automatically
4. **Review**: Use generated spec and code as starting point

Each MCP service you connect makes generation smarter. Start with GitHub (your code is the best reference), then add Linear (requirements) and Slack (team context).
