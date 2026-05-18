---
type: reference
last_verified: 2026-05-18
owner: claude
---

# Discord Launch Announcement

For the Anthropic Discord `#community-showcase` (or equivalent) channel.

---

## Short version (1 paragraph, for Twitter / quick share)

```
Just shipped v4.10 of ONE SHOT PLUGIN for Claude Code: production
agentic code-gen for existing projects. 9-stage pipeline, 10
specialist agents (architect → service-author → implementer × N +
test-author in parallel → reviewer → wirer → critic), real Alembic
migrations, FK-aware multi-entity, cost-gated. Supports FastAPI,
Django, Spring, Go, NestJS. MIT licensed. Looking for first 10
brave testers — drop your project, I'll help you /one-shot it.

GitHub: https://github.com/usmanmughaltaleemabad/One-Shot-Plugin
```

## Medium version (Discord post, ~200 words)

```
**ONE SHOT PLUGIN v4.10 — production agentic code generation for
Claude Code** (367/367 tests green · 101 body hints · 29 slash commands
· 12-stage pipeline with 9 default-on rigour gates)

A few months building, all-night production push last night, now
asking for first real-world testers.

What it does: type `/one-shot "shopping cart with line items and
discounts" @./my-project` — the plugin spawns the architect agent
(designs spec.json with entities + invariants + relationships),
service-author (writes business logic with transactions + event
emission), N parallel implementer agents (one per entity, Haiku for
cost), independent test-author (defends against test-router contract
drift), reviewer (security/perf/style gate), wirer (mutates main.py
with .osp.bak safety), and critic (runs pytest, decides ship vs
loop). Real Alembic migrations. OpenAPI 3.1 docs. Cost typically
$0.30–0.80 per generation; --templated fallback is free.

Differentiators (vs Aider, Cursor Composer, Devin):
- Deterministic + agentic split (most plugins pick one)
- Self-extending registry with curator skill (WebSearch finds new
  agents/MCPs with user approval)
- Per-agent cost-budget gate before spawn
- Beads-as-curriculum (failure log surfaces past mistakes pre-flight)

143/143 tests green on Py 3.14 / Windows. Cross-OS CI ready.

**Looking for**: 10 brave devs willing to /one-shot a feature into
their real project and tell me what broke. Open issue or DM.

GitHub: https://github.com/usmanmughaltaleemabad/One-Shot-Plugin
Cookbook: docs/cookbook.md
Scorecard: docs/scorecard-v4.md (honest 0–10 across 36 dimensions)
```

## Long version (Hacker News "Show HN" post)

```
Show HN: Agentic code generation Claude Code plugin (9-stage pipeline,
10 specialist agents)

Hi HN. I built a Claude Code plugin that takes "build a shopping cart
with line items and discounts" and produces a working FastAPI feature
— complete with foreign-key relationships, an Alembic migration,
service layer enforcing business invariants, JWT auth helpers,
OpenAPI 3.1 docs, and tests. Cost ~$0.50 per generation.

Architecture: 9-stage pipeline orchestrated through 10 specialist
agents (architect, service-author, implementer × N + test-author in
parallel, reviewer, wirer, critic, plus extractor / docs-author /
rollback for edge cases). Cost-tiered model routing (Haiku for
file-writers, Sonnet for reasoners). Self-extending registry of
external agents + MCP servers, growable via a curator skill that
uses WebSearch with explicit user approval.

What's different from {Aider, Cursor Composer, Devin}:

1. Explicit deterministic + agentic split. Code generation happens
   in Claude; scanning / verification / patching / wiring stays in
   Python. Each layer is testable independently. Most competitors
   pick one or the other.

2. Self-extending. The curator skill adds external agents/MCPs to a
   registry with provenance + ratings. Agents get reputation across
   sessions via a learnings_hub.

3. Cost-budget gate BEFORE agent spawn (not just observability after
   the fact). --budget=0.30 halts if estimate exceeds.

4. Beads-as-curriculum: every failure auto-logs structured
   diagnostics. Future tasks consult the failure log first via
   TF-IDF cosine similarity.

Honest about gaps: zero production users. The architecture is sound,
the 143 invocation tests are green, but the empirical run-it-in-
real-projects data doesn't exist yet. That's why I'm here — first
10 users get my full attention. MIT licensed.

GitHub: https://github.com/usmanmughaltaleemabad/One-Shot-Plugin
Scorecard (honest, includes 1.5/10 for community adoption):
  docs/scorecard-v4.md
3 worked examples: docs/cookbook.md

Happy to answer questions about the architecture, why the agentic
+ deterministic split, cost mechanics, or anything else.
```

## Reddit r/programming version

Similar to HN but with markdown formatting. Lead with the demo line:

```
**ONE SHOT PLUGIN for Claude Code: type "build a shopping cart with
line items" → 17 files, real Alembic migration, $0.50, 3 minutes**

[full HN post body adapted]
```

## Recommended posting cadence

| Day | Platform | Goal |
|---|---|---|
| Mon | Discord (Anthropic community) | First reactions; small audience |
| Tue | Hacker News (Show HN, ~8am ET) | Engineering crowd; ~50% chance of front-page |
| Wed | Reddit r/programming + r/Python | Reach broader devs |
| Thu | Twitter/X with demo screencast | Visual share |
| Fri | LinkedIn (technical post) | Director-level engineering audience |

**Don't post all at the same time.** Stagger so you can respond to
each platform's questions before the next surge.
