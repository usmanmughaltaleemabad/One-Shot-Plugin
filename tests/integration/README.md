---
type: runbook
last_verified: 2026-05-18
owner: claude
---

# Integration Tests

Two harnesses live here. One is free; one costs real money.

## 1. `validate_templated_pipeline.py` (free — run on every check-in)

Creates a synthetic FastAPI project in `/tmp` and walks all 15
deterministic-path stages in templated mode. Asserts each succeeds.

```bash
# Run it
python tests/integration/validate_templated_pipeline.py

# Keep the synthetic project for inspection afterwards
python tests/integration/validate_templated_pipeline.py --keep-temp

# Show artifact paths under each stage
python tests/integration/validate_templated_pipeline.py --verbose
```

Expected output (~8 seconds on M1 / modern Intel):

```
[setup] synthetic project: /tmp/osp-validate-XXXX/fake-fastapi
[setup] spec.json: .../spec.json

  [OK] extract_domain_model           (~ 200ms)  3 entities extracted
  [OK] codebase_graph                 (~ 200ms)  scanned project
  [OK] scaffold_planner               (~ 200ms)  21 files planned across 6 kinds
  [OK] incremental_planner            (~ 200ms)  3 slices ordered by FK dependency
  [OK] source_docs_fetcher            (~ 200ms)  detected fastapi 0.115.6 + 4 doc lookups
  [OK] body_hints                     (~ 800ms)  101 hints loaded; 4/4 probes succeeded
  [OK] critic_loop_driver             (~ 400ms)  init + record + SHIPPED verdict working
  [OK] doubt_driver                   (~ 400ms)  init + record + PROCEED working
  [OK] adr_writer                     (~ 200ms)  ADR #1 emitted + index regenerated
  [OK] ship_gates                     (~2500ms)  verdict=BLOCKED · 10 gates evaluated
  [OK] cost_budget                    (~ 200ms)  cost estimate emitted
  [OK] cost_calibrator                (~ 200ms)  graceful skip (no observations yet)
  [OK] run_finalize                   (~ 800ms)  3 agents recorded after SHIPPED
  [OK] learnings_hub_dashboard        (~ 250ms)  dashboard returned
  [OK] live_api_graceful_skip         (~1700ms)  skipped cleanly: missing_anthropic_api_key

SUMMARY  15 pass · 0 fail · 0 skip
```

Wrapped by `test_validate_pipeline.py::test_full_pipeline_validator_passes_end_to_end`
so it also runs in the normal `pytest tests/` suite.

## 2. `canary_live_api.py` (costs real money — opt-in)

Single architect-agent spawn against the **real Anthropic API**.
Validates the headless SDK path end-to-end with a minimal 1-entity
spec (~$0.05-0.10 actual cost, typically).

### Guards

```bash
# (a) Show me what it would do, without spending anything
python tests/integration/canary_live_api.py --dry-run

# (b) No consent flag → exit 1
python tests/integration/canary_live_api.py
# > ABORT: live runs cost real money...

# (c) Consent but no key → exit 1
python tests/integration/canary_live_api.py --i-know-this-costs-money
# > ABORT: ANTHROPIC_API_KEY is not set.
```

### Live run

```bash
pip install anthropic    # one-time
export ANTHROPIC_API_KEY=sk-ant-...

python tests/integration/canary_live_api.py \
    --i-know-this-costs-money \
    --max-cost-usd 0.15
```

Expected output (real run):

```
[setup] project: /tmp/osp-canary-XXXX/fake-fastapi
[setup] spec:    .../spec.json
[setup] out:     .../out
[mode]  LIVE (real API calls)

[results]
  status:              completed
  spawns_run:          1
  total_input_tokens:  4,200
  total_output_tokens: 1,800
  total_cost_usd:      $0.0395
  out_dir:             .../out

[per-spawn]
  [OK] architect              in=  4200  out=  1800  $0.0395  (5400 chars text)

[architect output excerpt]
  {
    "feature": "user signup with email verification",
    "framework": "fastapi",
    "entities": [
      ...
    ],
    ...
  }

  [OK] architect emitted valid spec with 1 entities
```

### Reading the results

- `total_cost_usd` is the actual money spent on this run.
- Per-spawn JSONs land in `out_dir/` for inspection (system_prompt,
  user_prompt, full text response, token counts).
- If the architect's text isn't parseable JSON, a `[WARN]` line surfaces
  — in production the orchestrator would route to architect again with
  the error.

## When to run each

| When | Run |
|---|---|
| Every CI check-in | `validate_templated_pipeline.py` (free, 8s) |
| Pre-release smoke | both — templated for free coverage, canary for live-api proof |
| Debugging a new agent prompt | `canary_live_api.py --keep-temp --i-know...` then inspect `out_dir/` |
| Before merging changes to a `*.py` in `scripts/` | `validate_templated_pipeline.py` to confirm nothing broke wiring |

## Related

- Per-script unit tests under `tests/test_*.py` (340 of them)
- Smoke test: `bash .claude/scripts/smoke-test.sh` (~5s, syntax + frontmatter)
- Eval harnesses: `python tests/evals/eval_runner.py` (deterministic replays)
