---
type: reference
last_verified: 2026-05-17
owner: claude
---

# Tier 1 Pipeline — Codebase-Aware, Self-Verifying One-Shot

Tier 1 is the foundation that takes the plugin from "scaffold template engine"
to "actually-working feature generator." It runs as a unified pipeline through
`one_shot_orchestrator.py`.

## The 7 stages

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  1. UNDERSTAND   │ →  │  2. SCAN          │ →  │  3. RECONCILE    │
│  extract_domain  │    │  codebase_graph   │    │  exists vs new   │
│  multi-entity NER│    │  AST + cache      │    │  per entity      │
└──────────────────┘    └──────────────────┘    └──────────────────┘
                                                          ↓
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  6. WIRE          │ ←  │  5. VERIFY       │ ←  │  4. GENERATE     │
│  auto_wirer       │    │  syntax + sem.   │    │  per-entity loop │
│  main.py/urls.py  │    │  contract checks │    │  phase2/3        │
└──────────────────┘    └──────────────────┘    └──────────────────┘
        ↓                       ↓                       ↓
                       ┌──────────────────┐
                       │  7. RECORD       │
                       │  beads_writer    │
                       │  on failure      │
                       └──────────────────┘
```

## Modules added in Tier 1

| Script | Stage | Purpose |
|---|---|---|
| `lib/base_script.py` | bootstrap | `bootstrap_runtime()` adds Windows UTF-8 + `sys.path` to every entry point |
| `extract_domain_model.py` | 1 | Multi-entity extraction from NL (replaces keyword-routing) |
| `existing_codebase_scanner.py` | 2 | AST-based scan of project models, schemas, conventions |
| `codebase_graph.py` | 2 | Persistent on-disk cache of the scan (`.osp_codebase_graph.json`) |
| `generate_and_verify.py` | 4-5 | Generate → write to sandbox → static + semantic verify → retry |
| `auto_wirer.py` | 6 | Idempotent edit of `main.py`/`urls.py` with `.osp.bak` safety net |
| `beads_writer.py` | 7 | Append-only failure log at `.beads/failures.jsonl` |
| `one_shot_orchestrator.py` | all | Public entry point that runs every stage and emits one report |

## What changed vs the previous design

| Before (Tier 0) | After (Tier 1) |
|---|---|
| `detect_resource_from_description` picked the first non-keyword word → "shopping" from "shopping cart with line items" | `extract_domain_model.extract` returns 4 entities + 3 relationships + intent + confidence |
| Generator didn't look at existing models → duplicated `Product` even when one already existed | `codebase_graph` loaded first; reconciled entities marked `exists` and skipped |
| Tests asserted things the router didn't do; no detection | `generate_and_verify` warns on test/router contract drift (401, `"next"`) |
| User had to manually `app.include_router(...)` after each generation | `auto_wirer` plans and (with `--apply`) executes the wiring |
| Failed generations vanished into stderr | `beads_writer` records every failure as a structured bead for replay |
| Each script had its own Windows-encoding workaround | `lib.base_script.bootstrap_runtime()` does it once, called from one import |

## Public CLI

```bash
# Dry-run an end-to-end one-shot generation on an existing project
python skills/one-shot-generator/scripts/one_shot_orchestrator.py \
    "Build a shopping cart with line items, discounts, and inventory holds" \
    --project ./my-fastapi-project

# Actually apply the wiring (mutates main.py with .osp.bak backup)
python skills/one-shot-generator/scripts/one_shot_orchestrator.py \
    "Add a category API" \
    --project ./my-fastapi-project \
    --apply
```

## Output report

`one_shot_orchestrator` returns a single `OrchestratorReport` JSON that
covers all 7 stages: extracted entities, codebase summary, reconciliation
status, per-entity generation results, verification diagnostics, wire plan,
and (if relevant) the recorded bead ID. This is the single artefact a
caller (Claude, CI, a human) reads to know what happened.

## Tier 2 — already scaffolded

The six specialist agents live under `.claude/agents/`:

| Agent | File | Role |
|---|---|---|
| Architect | `architect.md` | Domain spec → JSON spec consumed by everyone else |
| Implementer | `implementer.md` | Writes one file per invocation |
| Test-author | `test-author.md` | Independent of implementer — reads ONLY the spec |
| Reviewer | `reviewer.md` | Security/perf/style gate |
| Wirer | `wirer.md` | Integrates approved code via `auto_wirer.py` |
| Critic | `critic.md` | Runs tests, decides ship vs loop |

These are Claude Agent SDK definitions, not Python scripts. Tier 1's
orchestrator outputs the JSON the architect consumes, so the handoff is
ready for Tier 2 multi-agent execution.

## Tier 3 — what's queued

- **Persistent codebase memory:** `codebase_graph` already persists per
  project; future sessions will receive a diff of what changed since last
  run, not a full re-scan.
- **Beads-as-curriculum:** failures already recorded; the next step is a
  pre-flight reader that looks up the current task in `failures.jsonl` and
  warns "this pattern failed last time, here's why."
- **Self-improving prompts:** stub work — a `SKILL.md` update suggester
  that proposes changes when a class of failure recurs 3+ times.
- **Clarification-by-uncertainty:** orchestrator already emits a
  `confidence` score; the SKILL.md should ask the user one targeted
  clarifying question only when confidence drops below 0.55.
- **Streaming checkpoints:** emit `spec.json` first, let the user veto,
  then proceed to implementation.
- **Cross-feature consistency:** `codebase_graph` has the data; add a
  consistency scanner that compares new generation against the graph and
  flags naming/error-shape drift before wiring.

## Tests

`tests/test_tier1_pipeline.py` — nine invocation-based smoke tests that
actually run every new script and assert on its structured output. All
pass on Python 3.14 / Windows / cp1252 default code page.
