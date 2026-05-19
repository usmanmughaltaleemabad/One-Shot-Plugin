# mattpocock/skills Integration Guide

Adapted two key engineering skills from mattpocock's repository to power your one-shot-prompting pipeline.

## What Changed

### 1. **systematic-debug** (was 4-phase → now 6-phase diagnose)

**Added phases:**
- **PHASE 0: Build Feedback Loop** — Non-negotiable deterministic signal (test, curl, CLI)
- **PHASE 1: Reproduce** — Confirm bug is real and reproducible  
- **PHASE 6: Cleanup + Post-Mortem** — Record lessons learned

**Why:** Prevents blind hypothesis-testing. Your critic loop now has structured recovery when tests fail.

**Integration point:** When `/one-shot` critic agent encounters test failures, it now:
1. Ensures a fast feedback loop exists (pytest passes already)
2. Reproduces the exact failure
3. Generates falsifiable hypotheses
4. Instruments code to distinguish between causes
5. Writes regression test BEFORE fixing

---

### 2. **tdd-cycle** (added tracer bullets + planning)

**Added phases:**
- **PLAN** — Align on observable behaviors before any code
- **REPEAT** — Formalize the loop for next behavior

**Replaced concept:** "Three phases" → "Tracer bullet cycles (vertical slicing)"

**Why:** Prevents hollow test suites (all tests upfront, then all code). Emphasizes behavior-driven, end-to-end cycles.

**Integration point:** When implementer + test-author agents run in parallel:
- Test-author writes RED → GREEN → REFACTOR cycle (1 behavior)
- Implementer mirrors minimal code output
- Natural "REPEAT" returns to PLAN for next behavior
- No speculation, no empty test suitee

---

## How They Work Together

```
User invokes: /one-shot "add payment processing" @./project
    ↓
one-shot-generate PLAN stage (calls architect agent)
    ↓
Architect specifies domain model
    ↓
one-shot-generate BUILD stage (parallel tasks)
    ├─ Test-author: tdd-cycle PLAN → RED → GREEN → REFACTOR → REPEAT
    └─ Implementer: mirrors agent output from test-author signal
    ↓
one-shot-generate VERIFY stage
    ├─ Auto-patch (deterministic rules fix common bugs)
    └─ Reviewer agent (security, perf, style)
    ↓
one-shot-generate SHIP stage → Tests fail?
    └─ Critic agent triggers systematic-debug:
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
```

---

## Key Integration Points for Agents

### Test-Author Agent (Sonnet)
- Use `tdd-cycle` skill during implementer parallel tasks
- Call PLAN phase to align on next behavior
- Enforce RED → GREEN → REFACTOR gates
- Never write code before test

### Implementer Agent (Haiku)
- Mirrors test-author's progress (watches for RED, then codes for GREEN)
- No speculation; code only in response to failing tests
- Minimal first implementation, refactor in response to test signals

### Critic Agent (Sonnet)
- When pytest fails: invoke `systematic-debug` skill
- Build deterministic feedback loop (you already have pytest ✓)
- Generate falsifiable hypotheses before trying fixes
- Write regression tests before applying fixes

### Reviewer Agent (Sonnet)
- Runs AFTER systematic-debug fixes applied
- Gates on security, performance, style
- Confirms regression tests are meaningful (not hollow)

---

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Debugging failed code** | Guess-and-check, multiple fix attempts | Structured 6-phase diagnosis, 1 fix attempt |
| **Test quality** | Hollow test suites (all tests upfront) | Tracer bullets (one behavior = one cycle) |
| **Hypothesis testing** | Ad-hoc | Falsifiable format (if X, then Y disappears) |
| **Regression prevention** | Test added after fix | Regression test written before fix |
| **Post-mortem learning** | None | Structured lesson recorded |

---

## When to Use Each Skill

| Scenario | Skill | Phase |
|----------|-------|-------|
| Implementer agent writing new code | `tdd-cycle` | PLAN → RED → GREEN → REFACTOR → REPEAT |
| Critic agent encounters failing test | `systematic-debug` | BUILD-LOOP → REPRODUCE → HYPOTHESIZE → INSTRUMENT → OBSERVE → FIX → CLEANUP |
| Manual debugging during dev | Either | Use PLAN/PHASE-0 to build feedback loop first |

---

## mattpocock/skills Attribution

These skills adapt patterns from [mattpocock/skills](https://github.com/mattpocock/skills):
- **diagnose** → your `systematic-debug` (6-phase root cause investigation)
- **tdd** → your `tdd-cycle` (tracer bullets + vertical slicing)

Key principles borrowed:
- Deterministic feedback loops before hypothesis testing
- Falsifiable hypotheses (if X then Y)
- Vertical slicing to prevent hollow test suites
- Regression tests written before fixes
- One behavior per cycle (not spec-first-then-code)

---

**Last updated:** 2026-05-19
