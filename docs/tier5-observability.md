---
type: reference
last_verified: 2026-05-18
owner: claude
---

# Tier 5 — Observability + Self-Improvement Loop

Tier 5 closes the operational gaps the scorecard called out in Tier 3.5:
the eval harness, the rule extractor that turns observed fixes into new
auto_patch rules, and OpenTelemetry tracing. Plus battle-tested critic
routing and an empirically-validated real-world architect run.

## What's new

| Module | Role |
|---|---|
| `tests/evals/` | Known-good fixtures + golden outputs + scoring harness. Catches regressions in the deterministic pipeline. |
| `skills/one-shot-generator/scripts/auto_rule_extractor.py` | Watches git history for fixes to generated files, pattern-matches each diff into a candidate `auto_patch` rule, surfaces high-frequency patterns as ready-to-promote. |
| `skills/one-shot-generator/scripts/lib/telemetry.py` | Optional OTLP tracing across every deterministic script. No-op when `opentelemetry-sdk` isn't installed; W3C-shaped traceparent always available. |
| `tests/test_critic_loop_battle.py` | 7 synthetic failure scenarios that exercise the critic loop's routing protocol. Caught a real collection-error gap in `critic_runner.py` and forced a fix. |

## Eval harness

```
tests/evals/
├── fixtures/                # input projects + expected entities
│   ├── cart-with-line-items.json
│   ├── product-catalog-existing-base.json
│   └── user-auth-flow.json
├── golden/                  # frozen expected outputs (regenerable)
├── eval_runner.py           # runs every eval, scores against golden
└── README.md
```

Score breakdown per eval:

| Component | Weight | Metric |
|---|---|---|
| `domain_extraction` | 0.4 | F1 over entity names + relationship triples |
| `scaffold_paths` | 0.3 | Jaccard over file paths |
| `cost_estimate` | 0.15 | Within ±25% of golden total |
| `stub_detection` | 0.15 | Exact list match |

Overall ≥ 0.85 = pass. All 3 shipped evals currently score 1.00.

Adding a new eval:

```bash
# 1. Create fixtures/<name>.json with task + expected entities/relationships
# 2. Bootstrap the golden
python tests/evals/eval_runner.py --eval <name> --update-golden
# 3. CI / pre-commit will diff against golden from now on
python tests/evals/eval_runner.py --eval <name>
```

## Auto rule extractor

The Tier-3.5 scorecard flagged a self-improvement gap: when a user
manually fixes generated code, nothing extracts the fix as a new
`auto_patch` rule. Now:

```bash
# After a few real /one-shot runs and manual fixes:
python skills/one-shot-generator/scripts/auto_rule_extractor.py extract \
    --since "7 days ago"

# Inspect candidates that recurred >= 2 times:
python ...auto_rule_extractor.py list-candidates --min-occurrences 2

# Mark a candidate as ready for human review + manual auto_patch.py update:
python ...auto_rule_extractor.py promote --rule-id rule-20260518-001
```

The extractor is deliberately conservative — it never edits
`auto_patch.py` automatically. Promotion just marks the candidate;
adding it as a real P5/P6/... rule is a human action that goes through
code review.

Storage: `.beads/proposed_patch_rules.jsonl` (append-only; deduplicated
by SHA-256 of trigger pattern).

## OpenTelemetry tracing

```python
from lib.telemetry import span

with span("scan_codebase", attrs={"project": path}) as sp:
    # ... work ...
    sp.set_attr("entities_found", n)
```

Environment config:

| Variable | Effect |
|---|---|
| `OSP_OTEL_ENABLED=1` | Turn it on (default: off, no-op) |
| `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318` | OTLP collector endpoint |
| `OTEL_SERVICE_NAME=one-shot-prompting` | Service name in spans |

When `opentelemetry-sdk` isn't installed OR `OSP_OTEL_ENABLED` is unset,
every span is a `_NoOpSpan` that still exposes:
  * `.set_attr(key, value)`
  * `.record_exception(exc)`
  * `.duration_ms()`
  * `.traceparent` — synthetic but W3C-shaped (so it can be passed
    through to subprocess / Task spawns without special-casing)

`extract_domain_model.py` is the first hot-path wired up. Future PRs
extend to scaffold_planner, generate_and_verify, auto_wirer, critic_runner.

## Critic loop battle-test

`tests/test_critic_loop_battle.py` runs 7 synthetic failure scenarios
against `critic_runner` and verifies the routing protocol from
SKILL.md Stage 7:

| Scenario | Expected route |
|---|---|
| Test asserts 401 with no auth wired | test-author |
| Test asserts `"next" in response.json()` on a list endpoint | test-author |
| Import error in test file | implementer (NEW — caught a bug in critic_runner) |
| Multiple test-author concerns in one run | grouped into one bucket |
| Collection error short-circuits the rest | one route, to implementer |
| All tests pass | empty routes (SHIPPED) |
| Same failure twice | same classification (deterministic) |

The battle-test caught a **real bug**: `critic_runner.py` previously
didn't surface pytest collection errors (exit code 2 with no per-test
output lines). Fixed in this tier — collection failures now produce
synthetic "errored" outcomes that route to the implementer.

## Real-world architect dry-run (extended)

A second architect dry-run via the Task tool with messy extractor
output (the rule-based extractor misparsed "Tag with name, plus
TagAssignment connecting tags to products" into noise like
"TagassignmentConnectingTagsToProduct"). The architect agent **cleaned
it up**: demoted `Name` to a field, renamed the join entity to
`TagAssignment`, recognised the many-to-many through join table,
marked existing `Product` as reuse. 25,287 tokens at ~$0.10. Empirical
evidence that the agentic layer compensates for the deterministic
extractor's limits — exactly the design intent of Tier 3.5.

The cost observation has been logged to
`.beads/cost_observations.jsonl` so `cost_budget.recalibrate_from_log()`
will use it as a real data point.

## Tests

`tests/test_tier5_observability.py` — 9 tests covering eval harness +
rule extractor + telemetry.
`tests/test_critic_loop_battle.py` — 7 tests covering critic routing.

**Full plugin test suite: 88/88 green** on Py 3.14 / Windows.

## What's still queued

- **Wire telemetry into the other hot-paths** — scaffold_planner,
  auto_patch, auto_wirer, critic_runner. Mechanical work; safe.
- **Real OTLP collector smoke-test** — confirm spans land in Jaeger /
  Honeycomb when `OSP_OTEL_ENABLED=1` and an endpoint is set.
- **Eval harness coverage for the agentic path** — separate
  `agentic_evals.py` that does require Task spawns. The deterministic
  harness here doesn't exercise the agent layer.
- **Rule extractor promotion CLI** — auto-generate a P-rule stub in
  `auto_patch.py` from a promoted candidate, ready for human review.
