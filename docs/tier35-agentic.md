---
type: reference
last_verified: 2026-05-18
owner: claude
---

# Tier 3.5 — The Agentic Restructure

Tier 3.5 is the architectural answer to the question *"is this a Claude
Code plugin, or a Python application masquerading as one?"*

Earlier tiers (1, 2, 2.5) put almost everything in Python scripts —
including the code-generation step itself, via f-string templates. That
approach produced mediocre code and a long tail of template-leak bugs.
Tier 3.5 moves code generation out of Python and into Claude (the
model), while keeping every deterministic muscle in Python where it
belongs.

## The split that matters

```
┌──────────────────────────────────┬──────────────────────────────────┐
│ Stays in Python (deterministic)  │ Moves to Claude (reasoning)      │
├──────────────────────────────────┼──────────────────────────────────┤
│ scan codebase (AST)              │ architect a spec                 │
│ extract domain model             │ implement a file's body          │
│ persist codebase graph           │ author tests independently       │
│ diff codebase since last run     │ review for security / perf       │
│ verify syntax + contracts        │ critic on test failures          │
│ auto-patch known classes         │ decide loop vs ship              │
│ wire main.py / urls.py           │                                  │
│ run pytest (live + sandbox)      │                                  │
│ append failure beads             │                                  │
│ curriculum lookup                │                                  │
│ cost estimate                    │                                  │
└──────────────────────────────────┴──────────────────────────────────┘
```

## What ships in Tier 3.5

### 1. A real slash command

[`commands/one-shot.md`](../commands/one-shot.md) — proper Claude Code
frontmatter (`argument-hint`, `allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task`).
Routes to the new skill.

### 2. The conducting skill

[`skills/one-shot-generate/SKILL.md`](../skills/one-shot-generate/SKILL.md) —
Claude's 8-stage playbook:

| Stage | What runs | Deterministic? |
|---|---|---|
| 0 | `beads_curriculum.py` — past failures matching this task | ✅ script |
| 1 | `extract_domain_model.py` + `codebase_graph.py` | ✅ script |
| 2 | **architect agent** (via Task) → `spec.json` | 🤖 Claude |
| 3 | **implementer + test-author agents** in parallel (via Task) | 🤖 Claude |
| 4 | `generate_and_verify.py` + `auto_patch.py` | ✅ script |
| 5 | **reviewer agent** (via Task) | 🤖 Claude |
| 6 | `auto_wirer.py` (dry-run unless `--apply`) | ✅ script |
| 7 | **critic agent** (via Task) — runs `critic_runner.py` and verdicts | 🤖 Claude |
| 8 | Refresh `codebase_graph` + (on failure) `beads_writer.py` | ✅ script |

### 3. Six tightened agent definitions

Every agent in [`.claude/agents/`](../.claude/agents/) now has:
- `tools:` — explicit allowlist
- `model:` — cost-aware routing (Haiku for file-writers, Sonnet for reasoners)
- Explicit handoff contract (what they read, what they emit, what they refuse)

| Agent | Model | Tools |
|---|---|---|
| architect | sonnet | Read, Grep, Glob, Bash, Write |
| implementer | **haiku** | Read, Grep, Edit, Write, Bash |
| test-author | sonnet | Read, Grep, Write, Bash |
| reviewer | sonnet | Read, Grep, Bash |
| wirer | **haiku** | Read, Edit, Bash |
| critic | sonnet | Read, Bash |

### 4. `scaffold_planner.py` (replaces `spec_driven_generator`'s template emission)

Pure structural plumbing. Given a `spec.json`, returns a `plan.json`
listing files to create + their FK columns + import contracts. **No code
bodies.** The implementer agents fill them in. `spec_driven_generator.py`
stays in the repo as the headless/templated fallback.

### 5. `cost_budget.py` — token gate

Estimates the agentic spend before the pipeline runs:

```
COST ESTIMATE — shopping cart with line items and discounts
  architect     sonnet  ×1   in= 8000  out= 6000  $0.1140
  implementer   haiku   ×9   in=45000  out=36000  $0.1800
  test-author   sonnet  ×1   in= 6000  out= 5000  $0.0930
  reviewer      sonnet  ×1   in= 8000  out= 2500  $0.0615
  wirer         haiku   ×1   in= 2000  out= 1500  $0.0076
  critic        sonnet  ×1   in= 3000  out= 1500  $0.0315
  TOTAL                                          $0.4876
```

Pass `--budget=0.50` to gate; if estimate exceeds the budget, halt and
ask the user.

### 6. Archive of 9 thin stubs

[`.archive/phase4-5-aspirational/`](../.archive/phase4-5-aspirational/) —
nine Phase 5 placeholders (<60 LOC each, hardcoded template returns)
moved out of `scripts/`. Documented as "the agentic path replaces these"
with the new invocation pattern.

## What stayed (correctly so)

The 99 healthy phase 4-5 scripts remain in `scripts/`. They constitute
the `--templated` fallback path for users / CI runs that need
deterministic, zero-cost generation. The new skill calls them when the
user passes `--templated`; otherwise the agentic path runs.

## Two modes, one plugin

```bash
# Agentic (default) — quality, costs ~$0.30-0.80 per generation
/one-shot "shopping cart with line items and discounts" @./my-project

# Templated (free) — lower quality, zero LLM tokens
/one-shot "shopping cart with line items and discounts" @./my-project --templated

# Apply mode — actually mutates main.py + runs migrations
/one-shot "shopping cart" @./my-project --apply

# Budget gate — halt if estimate exceeds ceiling
/one-shot "shopping cart" @./my-project --budget=0.30
```

## Tests

[`tests/test_tier35_agentic.py`](../tests/test_tier35_agentic.py) —
15 invocation-based tests covering:

- slash command exists with proper frontmatter
- SKILL.md exists, references all 6 agents, calls all deterministic services
- every agent has `tools:` and `model:` frontmatter
- implementer + wirer use Haiku (cost optimisation)
- scaffold_planner emits FK columns from `has_many` relationships
- scaffold_planner respects existing `get_db` imports
- cost_budget produces believable USD figures
- cost_budget exits non-zero when over-budget
- 9 thin stubs were archived (and `README.md` explains why)

**Full suite across all tiers: 57/59 green** (2 pre-existing Django
fixture failures unrelated to this work).

## Why this is the right architecture for "world's greatest one-shot"

| Property | Template (Tier 0–2.5) | Agentic (Tier 3.5) |
|---|---|---|
| Code adapted to user's project | ❌ uses defaults | ✅ Claude reads the codebase |
| Test contract matches router contract | ❌ drift everywhere | ✅ independent agents read same spec |
| New patterns require new scripts | ❌ N scripts | ✅ Claude reasons |
| Cost per generation | $0 | $0.30-0.80 |
| Time to add a new framework | Days (write phase2 variant) | Hours (write a stub generator hint) |
| Bug class: unsubstituted `{placeholder}` | ✅ exists (we fixed 17) | ❌ no templates = no template-leak |
| Bug class: missing FK from relationship | ✅ existed pre-2.5 | ❌ architect always emits FKs |
| Bug class: tests assert what router can't do | ✅ existed pre-2.5 | ❌ critic catches it; agents respec |
| Self-improving from accumulated failures | partial (curriculum reads logs) | full (proposer + curriculum + critic loop) |

## What's still queued

- **Multi-iteration critic loop driver in SKILL.md**: the playbook lists
  the steps, but the actual N-iter regeneration when critic returns LOOP
  isn't fully fleshed out in the markdown — it's clear what *should*
  happen but the exact prompt structure for "respec and re-spawn" needs
  refinement after first real-world runs.
- **Streaming spec emission**: SKILL.md hands off spec.json to the
  implementer agents in one shot; a future iteration could emit it to
  the user first for `--review` approval.
- **Cross-language scaffold templates**: scaffold_planner is
  FastAPI-only; Django/Spring/Go variants are the obvious next-rung.
- **Real-world cost measurement**: the per-agent token estimates in
  `cost_budget.py` are conservative guesses. After 20-30 real
  generations, replace them with empirical p50/p95 measurements.
