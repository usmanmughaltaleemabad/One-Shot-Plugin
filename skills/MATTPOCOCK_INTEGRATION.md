# mattpocock/skills Integration Guide

Adapted six key engineering skills from mattpocock's repository to power your
one-shot-prompting pipeline. Two core (systematic-debug, tdd-cycle) + four
productivity (caveman, grill-me, handoff, write-a-skill).

## Skills Overview

### Tier 1: Core Pipeline Skills (mattpocock-adapted)

#### 1. **systematic-debug** (6-phase root cause investigation)

Adapted from: mattpocock/skills **diagnose**

**What it does:** Structured debugging when generated code fails tests.

Phases:
- **PHASE 0: Build Feedback Loop** — Deterministic pass/fail signal (test, curl, CLI)
- **PHASE 1: Reproduce** — Confirm bug is real and reproducible  
- **PHASE 2: Hypothesize** — Generate 3–5 falsifiable hypotheses
- **PHASE 3: Instrument** — Target logging at highest-confidence hypothesis
- **PHASE 4: Observe** — Compare actual vs. predicted behavior
- **PHASE 5: Fix + Regression Test** — Write test BEFORE applying fix
- **PHASE 6: Cleanup + Post-Mortem** — Record lessons learned

**Integration point:** When `/one-shot` critic agent encounters test failures, it now:
1. Ensures a fast feedback loop exists (pytest passes ✓)
2. Reproduces the exact failure
3. Generates falsifiable hypotheses
4. Instruments code to distinguish between causes
5. Writes regression test BEFORE fixing

**Invocation:**
```bash
/systematic-debug "test failures in payment processing" @./project \
  --error-log=test-failure.log --feedback-method=test
```

---

#### 2. **tdd-cycle** (tracer bullets + vertical slicing)

Adapted from: mattpocock/skills **tdd**

**What it does:** Enforce behavior-driven development with vertical slicing.

Phases:
- **PLAN** — Align on observable behaviors before any code
- **RED** — Write failing test for ONE behavior
- **GREEN** — Minimal implementation to pass test
- **REFACTOR** — Align code with conventions (no behavior change)
- **REPEAT** — Plan next behavior

**Why:** Prevents hollow test suites (all tests upfront, then all code).
Emphasizes behavior-driven, end-to-end cycles. No speculation, no empty tests.

**Integration point:** When implementer + test-author agents run in parallel:
- Test-author writes RED → GREEN → REFACTOR cycle (1 behavior)
- Implementer mirrors minimal code output
- Natural REPEAT returns to PLAN for next behavior

**Invocation:**
```bash
/tdd-cycle "add payment charging with Stripe" @./project --phase=plan
/tdd-cycle "add payment charging with Stripe" @./project --phase=red
/tdd-cycle "add payment charging with Stripe" @./project --phase=green
```

---

### Tier 2: Productivity Skills (mattpocock-adapted)

#### 3. **caveman** (token compression ~75%)

Adapted from: mattpocock/skills **caveman**

**What it does:** Compress verbose output while preserving technical accuracy.

Compression rules:
1. Drop commentary & filler ("This is because...", "Note that...")
2. Compress repetition (deduplicate across sections)
3. Bullet lists over prose (one fact per bullet)
4. Code blocks verbatim (never compress actual code)
5. Reorder by priority (critical info first)

**Integration points:**
- **ARCHITECT REVIEW:** Compress long specs before handing to implementer
- **CRITIC LOOP:** Compress verbose error logs (keep unique errors, strip duplicates)
- **ANYTIME:** Context window check (if transcript getting long, compress)

**Invocation:**
```bash
# Compress spec before implementer sees it
/caveman @./spec.json --preserve-code --target-reduction=75

# Compress error logs when debugging
/caveman @./test-failure.log --preserve-errors --target-reduction=80

# Compress long summary before next turn
/caveman @./long-summary.md --target-reduction=70
```

**Typical benefit:** 500-token spec → 125 tokens (same facts, fewer words)

---

#### 4. **grill-me** (exhaustive questioning before design)

Adapted from: mattpocock/skills **grill-me**

**What it does:** Explore every branch of the decision tree before architect runs.

Questioning categories (6):
1. **SCOPE & CONSTRAINTS** — Data volume, hard limits, integrations, failure modes
2. **DATA MODEL** — Entities, relationships, cardinality, historical retention
3. **BEHAVIOR & WORKFLOWS** — Happy path, failures, edge cases, notifications
4. **INTEGRATION & DEPENDENCIES** — External APIs, sequencing, transactions, retries
5. **NON-FUNCTIONAL REQUIREMENTS** — Performance, security, concurrency, observability
6. **TRADE-OFFS & ASSUMPTIONS** — Out of scope, assumptions, cost-benefit, blind spots

**Integration point:** PLAN stage, before architect generates code.

Prevents expensive rework: catch fuzzy requirements now, not in VERIFY phase.

**Invocation:**
```bash
# Deep questioning on ambiguous feature
/grill-me "add payment processing" @./project --depth=deep

# Focus on constraints after initial spec
/grill-me @./spec.json --focus=constraints --depth=medium
```

**Typical output:** 30–50 Q&A pairs. User reviews and confirms. Then architect
proceeds with full context.

---

#### 5. **handoff** (conversation to runbook)

Adapted from: mattpocock/skills **handoff**

**What it does:** Transform verbose generation logs into compact runbook for
next person (human dev, ops, or next agent).

Output sections:
1. **WHAT WAS BUILT** — Summary + file list
2. **HOW TO RUN IT** — Quick start, prerequisites, setup commands
3. **WHAT WAS TESTED** — Test coverage snapshot + test locations
4. **DEPLOYMENT CHECKLIST** — Pre-deploy, during, post-verification, rollback
5. **KNOWN ISSUES & NEXT STEPS** — Completed, limitations, prioritized next work

**Integration point:** SHIP stage (after critic passes all tests).

When generation complete, hand off to human or next system.

**Invocation:**
```bash
# Generate runbook for human developer
/handoff --from-last-output @./project --audience=developer

# Generate runbook for ops team
/handoff @./project --audience=operator

# Between iterations: summarize phase 1, pass to phase 2
/handoff @./project --format=json --audience=machine
```

**Typical benefit:** 50KB verbose logs → 2KB compact runbook (same actionability)

---

#### 6. **write-a-skill** (skill authoring guide)

Adapted from: mattpocock/skills **write-a-skill**

**What it does:** Template + checklist for creating production-ready skills.

Includes:
- SKILL.md frontmatter + phase structure
- Helper script template (Python)
- Test scaffold (pytest)
- Linting & verification
- Publishing checklist

**Integration point:** When curator discovers gaps or team needs new workflow.

Promotes repeatability: one-off scripts → reusable, tested, documented skills.

**Invocation:**
```bash
# Generate starter skill template
/write-a-skill "my-new-workflow" --phases=3 --complexity=medium

# Lint existing skill
/write-a-skill @./skills/my-skill/SKILL.md --lint
```

---

## How They Work Together

Complete end-to-end flow:

```
User invokes: /one-shot "add payment processing" @./project
    ↓
PLAN Stage: /grill-me (expand fuzzy requirements)
    ├─ Surface all constraints, edge cases, assumptions
    └─ User confirms expanded spec
    ↓
ARCHITECT Stage: Generate spec.json
    ├─ /caveman (compress spec before handoff to implementer)
    └─ Implementer gets dense, technical spec
    ↓
BUILD Stage (parallel):
    ├─ Test-author: /tdd-cycle (PLAN → RED → GREEN → REFACTOR → REPEAT)
    └─ Implementer: mirrors test signals
    ↓
VERIFY Stage:
    ├─ Auto-patch (deterministic rules)
    └─ Reviewer agent (security, perf, style)
    ↓
SHIP Stage → Tests fail?
    └─ Critic invokes /systematic-debug:
       1. Build loop (pytest passes ✓)
       2. Reproduce (confirm failure)
       3. Hypothesize (falsifiable causes)
       4. Instrument (targeted logging)
       5. Observe (compare vs. predictions)
       6. Fix + Regression test
       7. Cleanup + post-mortem
    ↓
Loop 1–3 iterations, then:
   ✅ SHIPPED (if all pass) or ❌ ESCALATED (after 3 fails)
    ↓
HANDOFF Stage:
    └─ /handoff (convert logs to runbook)
       └─ Human dev takes over, or next iteration begins
```

---

## Integration Points by Pipeline Stage

| Stage | Skills | Purpose |
|-------|--------|---------|
| **PLAN (0.5)** | grill-me | Expand fuzzy requirements exhaustively |
| **ARCHITECT (2)** | caveman | Compress spec before implementer sees it |
| **BUILD (3)** | tdd-cycle | Enforce red-green-refactor on each behavior |
| **VERIFY (4–5)** | caveman | Compress verbose error logs when debugging |
| **SHIP (6–7)** | systematic-debug | Root cause investigation if tests fail |
| **SHIP (6–7)** | handoff | Transform logs to runbook after passing |
| **EXTEND (Curator)** | write-a-skill | Create new skills when gaps emerge |

---

## Key Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Spec clarity** | Fuzzy 1–2 sentences | Exhaustive Q&A before code |
| **Context efficiency** | Verbose, repetitive specs | 75% token reduction, zero info loss |
| **Debugging failed code** | Guess-and-check, multiple attempts | Structured 6-phase diagnosis, 1 fix attempt |
| **Test quality** | Hollow test suites (all tests upfront) | Tracer bullets (one behavior = one cycle) |
| **Hypothesis testing** | Ad-hoc | Falsifiable format (if X, then Y disappears) |
| **Regression prevention** | Test added after fix | Regression test written before fix |
| **Handoff friction** | "Read the 50KB log" | "Read the 2KB runbook" |
| **Skill extensibility** | Copy-paste scripts | Structured templates + checklists |

---

## When to Use Each Skill

| Scenario | Skill | Invocation |
|----------|-------|-----------|
| Feature description is vague | grill-me | `/grill-me "..." --depth=deep` |
| Architect generates long spec | caveman | `/caveman @./spec.json` |
| Writing test-driven code | tdd-cycle | `/tdd-cycle "..." --phase=red` |
| Generated code fails tests | systematic-debug | `/systematic-debug --error-log=...` |
| Tests pass, need to hand off | handoff | `/handoff --from-last-output` |
| New workflow needed | write-a-skill | `/write-a-skill "name"` |

---

## Testing the Integration

### Smoke Test (5 min)

```bash
# Verify all 6 skills are loadable
cd one-shot-prompting
python -m pytest tests/ -k "mattpocock" -v

# Or manual check
ls skills/caveman/SKILL.md
ls skills/grill-me/SKILL.md
ls skills/handoff/SKILL.md
ls skills/write-a-skill/SKILL.md
ls skills/systematic-debug/SKILL.md
ls skills/tdd-cycle/SKILL.md
```

### Integration Test (Full pipeline)

```bash
# End-to-end test
/one-shot "add shopping cart" @./test_contexts/django_minimal \
  --budget=0.50 --grill-me --review
```

Expected: All 6 skills invoked at appropriate stages.

---

## mattpocock/skills Attribution

These skills adapt patterns from [mattpocock/skills](https://github.com/mattpocock/skills):

| Your Skill | Adapted From | Key Pattern |
|-----------|--------------|-------------|
| systematic-debug | diagnose | Deterministic feedback loops before hypothesis testing |
| tdd-cycle | tdd | Vertical slicing to prevent hollow test suites |
| caveman | caveman | Token compression by dropping filler, keeping data |
| grill-me | grill-me | Exhaustive questioning of decision tree |
| handoff | handoff | Conversation-to-runbook transformation |
| write-a-skill | write-a-skill | Skill authoring templates + checklists |

**Key principles borrowed across all:**
- Deterministic signals before speculation
- Falsifiable hypotheses (if X then Y)
- Vertical slicing (one behavior at a time)
- Structured gates (no hand-wavy transitions)
- Regression tests written before fixes
- Attribution and skill reuse as core architecture

---

**Last updated:** 2026-05-19
**Version:** v1.0.0 (all 6 skills documented)
