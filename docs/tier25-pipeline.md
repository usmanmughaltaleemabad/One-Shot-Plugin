---
type: reference
last_verified: 2026-05-18
owner: claude
---

# Tier 2.5 — Spec-Driven, FK-Aware, Critic-Looped

Tier 2.5 closes the last big gap between Tier 1's per-entity scaffolding
and a truly multi-entity, relationship-aware one-shot. The orchestrator
now switches automatically to the spec-driven path whenever it targets a
FastAPI project.

## What's new

| Module | Purpose |
|---|---|
| `spec_driven_generator.py` | Reads a `spec.json` and produces ONE coherent set of files covering every new entity, with FK columns inferred from extracted relationships. Uses `textwrap.dedent` + `.format(**kwargs)` instead of f-string concatenation — eliminating the `NameError: name 'self'` bug class. |
| `run_critic_loop.py` | N-iteration closed loop: generate → static verify → auto-patch → re-verify → critic (pytest) → route → respec → regenerate. Stops at `max_iters` (default 3). |
| `codebase_diff.py` | Diffs the current codebase against the cached graph. Reports added/removed/modified files plus per-class field deltas. |
| `live_critic.py` | Runs pytest against the **wired** project (not the sandbox) and partitions outcomes into new-feature outcomes vs regressions. |
| Orchestrator spec-driven path | Auto-engaged when framework is FastAPI; calls the critic loop with the compiled spec; one sandbox holds every entity in the feature. |

## The change in concrete terms

For `"Build a shopping cart with line items and discounts"`:

**Before (Tier 2):**
```
3 separate phase2 invocations, 18 files
line_item/models.py: NO cart_id FK   ← the feature didn't actually wire
```

**After (Tier 2.5):**
```
1 spec_driven invocation, 17 files (3 entities + database stub + tests + README)
line_item/models.py:
    shopping_cart_id = Column(Integer, ForeignKey("shopping_carts.id"),
                              nullable=False, index=True)
```

The FK is derived from the `has_many` relationship inferred by
`extract_domain_model`, then carried through `compile_spec`'s spec.json,
then materialised by `spec_driven_generator`. Every layer of the
pipeline knows about the relationship; the final code reflects it.

## How the critic loop respecs after a failure

When the inline critic (pytest run in the sandbox) reports failures with
routing hints like:

```json
{"nodeid": "tests/test_cart.py::test_unauthorized",
 "route_to": "test-author",
 "reason": "test asserts 401 but router has no auth"}
```

…`run_critic_loop` updates the spec's `test_contract.auth='none'` for the
next iteration, then regenerates. The architect/implementer routes are
no-ops here (those belong to the multi-agent flow in `.claude/agents/`),
but test-author routes are handled deterministically end-to-end.

## Persistent memory: `codebase_diff`

`codebase_graph.py` caches an `.osp_codebase_graph.json` at the project
root keyed on a file-mtime + manifest signature. `codebase_diff.py`
compares the current state against the cache and emits:

```json
{
  "signature_unchanged": false,
  "added": ["returns/models.py"],
  "removed": [],
  "modified": [
    {"file": "models.py", "new_classes": [], "new_fields": {"Product": ["barcode"]}}
  ],
  "summary": "1 added, 1 modified"
}
```

Future orchestrator runs will consult the diff before re-scanning — so
"Add returns flow" can incorporate the freshly-added `Tax` model from
yesterday's run without losing context.

## Tests

`tests/test_tier25_pipeline.py` — 9 invocation-based tests covering:
- spec_driven_generator emits files per entity
- FK columns are derived correctly from `has_many`
- database.py stub appears only when project lacks `get_db`
- existing `get_db` is reused when the codebase graph has one
- run_critic_loop ships on a clean spec
- codebase_diff detects added files and reports unchanged signatures
- live_critic partitions feature vs regression outcomes
- orchestrator's spec-driven path is auto-engaged for FastAPI

Full suite: **29 / 29 green** on Py 3.14 / Windows (Tier 1 + 2 + 2.5).

## What's still queued for Tier 3+

- **Streaming spec emission**: orchestrator should print spec.json before
  generation so the user can `--review` before the loop starts.
- **Real multi-agent execution**: the 6 specialist agents are defined; a
  session driver that spawns them in parallel via Agent tool with
  `spec.json` as the shared input is the next concrete step.
- **Live `--apply` mode**: orchestrator's wire step is still dry-run by
  default; `--apply` exists but pairs with running migrations + live_critic
  for a complete one-shot deployment.
- **Cross-language spec generators**: spec_driven_generator is FastAPI
  only at v1.0; Django / Spring / NestJS variants are the obvious follow-up.
