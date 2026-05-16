---
name: phase-planner
description: Plans Phase 4-5 implementation — reads roadmap, opens beads per module
trigger: manual
---

# Phase Planner Agent

Plans implementation of Phase 4 or Phase 5 features.

---

## When to Invoke

When starting Phase 4 or Phase 5 work:

```bash
/phase-planner "plan Phase 4 DDD/CQRS implementation"
```

---

## What It Does

1. **Read Phase Status**
   - Load `docs/phase-status.md`
   - Identify which modules are stubs (❌ not implemented)
   - Count total modules, lines of code, release target

2. **Read Roadmap**
   - Load `ROADMAP.md`
   - Extract Phase 4-5 module descriptions
   - Identify dependencies and ordering

3. **Create Implementation Plan**
   - Break Phase 4-5 into chunks (10-15 modules per chunk)
   - Propose implementation order (e.g., DDD first, then CQRS, then compliance)
   - Estimate effort per chunk

4. **Open Beads**
   - Create bd-XXX for each chunk
   - Link to ROADMAP.md and phase-status.md
   - Mark as `open` with `blocked_by: null`

5. **Document in Planning File**
   - Create or update `.claude/PHASE_4_IMPLEMENTATION_PLAN.md` (or PHASE_5...)
   - List modules in order
   - Link beads to each module group

---

## Output

Phase implementation plan:

```
PHASE 4 IMPLEMENTATION PLAN
===========================

Total modules: 60 (DDD 15, CQRS 10, Event Sourcing 8, TDD 8, Compliance 19)
Effort estimate: 200-300 hours
Release target: v3.0.0

Breakdown by chunk:
1. DDD Fundamentals (bd-003)
   - ddd_aggregate_design.py
   - ddd_value_objects.py
   - ddd_repositories.py
   Est: 40h, ~3 SKILL.md sections

2. CQRS Pattern (bd-004)
   - cqrs_pattern.py
   - cqrs_event_bus.py
   Est: 30h, ~2 SKILL.md sections

3. Event Sourcing (bd-005)
   - event_sourcing.py
   - event_store.py
   Est: 35h, ~2 SKILL.md sections

...

Recommendation:
- Start with DDD (bd-003) — foundational, other modules depend on it
- Then CQRS (bd-004) — uses DDD concepts
- Then Compliance (bd-006) — orthogonal, can parallelize
```

---

## Session End Protocol

When planning is complete:

1. Create `.claude/PHASE_4_IMPLEMENTATION_PLAN.md` (or PHASE_5_...)
2. Open beads for each chunk (bd-003, bd-004, ...)
3. Update `docs/phase-status.md` with progress
4. Commit: "docs: Phase 4 implementation plan (60 modules, 3 chunks)"
5. Append to `## Self-Improvement Log` below

---

## Self-Improvement Log

<!-- Append learnings from each phase planning session -->

- **2026-05-16**: Created Phase Planner agent. Phase 4-5 not yet started. Ready for planning when scheduled.
