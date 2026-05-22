---
name: one-shot-generate
description: |
  End-to-end agentic one-shot. Claude conducts a pipeline of deterministic
  scripts + specialist agents to take a natural-language feature request and
  produce verified, wired code in the user's existing codebase. Trigger words:
  "one-shot", "generate feature", "build feature", "add CRUD/API/endpoints",
  "add batch job", "scaffold". Accepts an optional ``--templated`` flag that
  falls back to the legacy Python-only pipeline (no Claude tokens) for users
  who need free, deterministic generation.
argument-hint: "[task description] [@path/to/project] [--apply] [--templated] [--budget=USD]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task
---

<!--
  AUDITORS: This file is the pipeline dispatcher. The stages live in
  stages/plan.md, stages/build.md, stages/verify.md, stages/ship.md,
  stages/record.md. Claude reads all of them in sequence.
  See AUDIT_ME_FIRST.md at the repo root for orientation.
-->

# One-Shot Generate — Agentic Pipeline

You are conducting the one-shot generation pipeline. The user has invoked
`/one-shot "their feature description" @/path/to/project`. Your job is to
run the pipeline below, spawning specialist agents at the right points,
and ship working code into their project.

The arguments are: `$ARGUMENTS`

---

## Step 0 — Initialize routing trace & route: templated vs agentic (DO THIS FIRST)

Initialize the routing trace (enables introspection into decision layers):

```!
SESSION_ID=$(date +%s)-$(openssl rand -hex 3)
PROJECT_ROOT="$2"  # from @./path argument
python "../one-shot-generator/scripts/routing_trace.py" --init "$SESSION_ID" "$PROJECT_ROOT"
```

**Route on `--templated`:**

If `$ARGUMENTS` contains `--templated` / `--legacy` / `--free`:

```!
python "../one-shot-generator/scripts/one_shot_orchestrator.py" "$ARGUMENTS"
```

Log the decision:
```python
from scripts.routing_trace import get_or_create_trace
trace = get_or_create_trace(SESSION_ID, PROJECT_ROOT)
trace.log_decision(
    stage='SKILL.Step0',
    layer='L1_ROUTER',
    decision='route_templated',
    context={'arguments': ARGUMENTS},
    consequence='Use legacy Python pipeline, zero Claude tokens, lower quality'
)
```

Summarise the output and stop. This costs zero Claude tokens but produces
lower-quality code. It is a fallback, not the main path.

**For everything else: continue below (agentic route).**

Log the agentic route decision:
```python
trace.log_decision(
    stage='SKILL.Step0',
    layer='L1_ROUTER',
    decision='route_agentic',
    context={'arguments': ARGUMENTS},
    consequence='Proceed through 5-stage agentic pipeline'
)

---

## Flags (read once, apply throughout)

- `--apply` — Stage 6: mutate project files (default is dry-run)
- `--budget=USD` — Stage 1.5: halt if cost estimate exceeds this
- `--force` — bypass clarification gate even at confidence < 0.55
- `--review` — Stage 2.5: show spec.json to user before agents fire
- `--incremental` — Stage 2.6: one entity per commit
- `--legacy-safe` — Stage 0.7: `legacy_guard.py` caps to 3 files, blocks --apply
- `--no-doubt` — skip Stage 5.5 (DEFAULT ON: doubt-driven adversarial pass)
- `--no-ship-check` — skip Stage 6 ship gates (DEFAULT ON); gates run
  `ship_gates.py` which returns READY or BLOCKED before any --apply
- `--no-adr` — skip ADR emission (Stage 2, `adr_writer.py` writes to docs/adr/)
- `--no-consistency-check` — skip Stage 5.7 (`cross_agent_consistency.py` + `security_deep_scan.py`, DEFAULT ON);
  catches subtle logic bugs that per-agent review misses
- `--require-approval-webhook=URL` — Stage 5.9: POST before wiring

**Productivity-skill integration flags** (skills wired into specific stages):

- `--grill` — force grill-me invocation in Stage 1.6 (otherwise fires only
  when feature description is ambiguous: < 50 chars, 0 entities extracted,
  or extractor confidence < 0.55)
- `--tdd-strict` — Stage 3 routes through tdd-cycle skill (RED → GREEN →
  REFACTOR per entity) instead of parallel implementer + test-author
- `--no-compress` — skip caveman compression of reviewer/critic inputs in
  Stages 5 and 7 (DEFAULT ON when prompt > 8k tokens)
- `--no-systematic-debug` — skip systematic-debug skill in Stage 7 when
  critic hits the same failure twice (DEFAULT ON: forces 6-phase root-cause
  investigation instead of guess-loop)
- `--no-handoff` — skip Stage 8.5 handoff document emission (DEFAULT ON on
  SHIPPED runs)

---

## Pipeline — execute in order

Read and execute each stage file in sequence:

**PLAN** → `@./stages/plan.md`
Stages 0 – 2.7: curriculum, scan, extract, cost gate, **grill-me (1.6)**,
doc lookup, architect, spec review, incremental slice, service-author.

**BUILD** → `@./stages/build.md`
Stage 3: implementer × N + test-author (parallel) — or **tdd-cycle**
when `--tdd-strict`.

**VERIFY** → `@./stages/verify.md`
Stages 4 – 5.7: auto-patch, reviewer (with **caveman** compression on
large inputs), doubter, consistency + SAST.

**SHIP** → `@./stages/ship.md`
Stages 6 – 7: wire, migrate, approval gate, critic loop (max 3 iter,
with **systematic-debug** triggered on repeat failures).

**RECORD** → `@./stages/record.md`
Stages 8 – 8.5: graph refresh, learnings, dream consolidation,
**handoff** runbook on SHIPPED.

---

After RECORD completes, give the user a summary:
- Files generated / modified
- Entities and their relationships
- Migration file location (if any)
- Wire plan (what was added to main.py / urls.py)
- Total estimated cost
- Critic verdict (SHIPPED / ESCALATED)

**Emit routing trace summary** (L1 memory introspection):
```python
from scripts.routing_trace import get_or_create_trace
trace = get_or_create_trace(SESSION_ID, PROJECT_ROOT)
summary = trace.emit_summary()
print("\n=== L1 Memory Routing Trace ===")
print(f"Session: {summary['session_id']}")
print(f"Total decisions: {summary['total_decisions']}")
print(f"By layer: {summary['by_layer']}")
print(f"Trace saved: {summary['trace_file']}")
```

Users can inspect `.one-shot/routing_trace.jsonl` to see the exact layer
(L1 Router, L2 Module, L3 Data) that made each decision.
