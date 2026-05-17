---
type: reference
last_verified: 2026-05-18
owner: claude
---

# Tier 2 — Closed Loop + Multi-Agent Specialisation

Tier 2 builds on the [Tier 1 pipeline](tier1-pipeline.md) by closing the
generate → verify → patch → re-verify loop and giving each specialised
concern (architecture, implementation, testing, review, wiring, criticism)
its own agent with an explicit handoff contract.

## What's new at Tier 2

| Module | Role |
|---|---|
| `critic_runner.py` | Actually runs `pytest` against generated tests, parses outcomes, and emits routing hints for the multi-agent system |
| `auto_patch.py` | Deterministic edits that resolve the four most common diagnostics we've observed (401, pagination, placeholder leak, missing imports) |
| `compile_spec.py` | Bridges the orchestrator's JSON report into `spec.json`, the canonical contract for the six specialist agents |

The agent definitions live under [.claude/agents/](../.claude/agents/):
`architect.md`, `implementer.md`, `test-author.md`, `reviewer.md`,
`wirer.md`, `critic.md`.

## The closed loop, in practice

The `generate_and_verify` runner now performs:

```
attempt 1
    ↓
generate (phase2 or phase3)
    ↓
sandbox write
    ↓
verify (syntax + template + test/router contract)
    ↓
auto_patch ← attempts to fix any diagnostic with a known rule
    ↓
re-verify (records the patch as an info-level diagnostic)
    ↓
succeeded? → done.  else loop attempt 2.
```

The end result observed against the FastAPI fixture:

```
[info] test_category_api.py:—  auto_patched: P1: skipped test asserting HTTP 401 (router has no auth)
[info] test_category_api.py:—  auto_patched: P2: rewrote "next" pagination check to list-shape check
Result: ✅ PASS
```

Two semantic warnings that would previously have shipped to the user are
fixed automatically before the wirer sees the code.

## Auto-patch rules

| Rule | Diagnostic it resolves | Edit |
|---|---|---|
| P1 | test asserts 401 but router has no auth | replace test body with `pytest.skip("auth not implemented per spec")` |
| P2 | test asserts `"next" in response.json()` but router returns list | rewrite to `assert isinstance(response.json(), list)` |
| P3 | unsubstituted `{plural}` / `{resource}` placeholder in docstring | substitute with inferred resource name |
| P4 | `from database import get_db` doesn't exist in project | rewrite to the import path discovered by `codebase_graph` |

All four rules are conservative: they only fire when the diagnostic clearly
matches their signature, and they always preserve a record of what changed
(as `auto_patched` info diagnostics).

## The critic loop

`critic_runner.py` runs pytest in subprocess and turns the output into a
structured report:

```json
{
  "exit_code": 1,
  "passed": 4,
  "failed": 1,
  "outcomes": [
    {"nodeid": "tests/test_cart.py::test_pagination",
     "outcome": "failed",
     "short_traceback": "assert 'next' in response.json()"}
  ],
  "routes": [
    {"nodeid": "...",
     "route_to": "test-author",
     "reason": "test asserts paginated envelope but router returns list"}
  ]
}
```

The critic agent (`.claude/agents/critic.md`) consumes that report and
either emits `VERDICT: SHIPPED` or `VERDICT: LOOP (iteration N of 3)` with
each failure routed to the responsible agent (test-author, implementer,
architect, etc.).

## How to invoke the multi-agent flow

```bash
# 1. Run the deterministic pipeline
python skills/one-shot-generator/scripts/one_shot_orchestrator.py \
    "shopping cart with line items, discounts" \
    --project ./my-project --json > orchestrator.json

# 2. Compile a spec.json for the agents
python skills/one-shot-generator/scripts/compile_spec.py \
    --orchestrator-json orchestrator.json --out spec.json

# 3. Hand spec.json to the architect agent (via Claude Code's Agent tool)
#    The architect emits a refined spec; the implementer/test-author/
#    reviewer/wirer agents consume it in parallel.

# 4. Critic runs pytest after wiring; loops if red.
python skills/one-shot-generator/scripts/critic_runner.py \
    --tests ./tests --route --json
```

## Tests

`tests/test_tier2_pipeline.py` — 11 invocation-based smoke tests covering
every Tier-2 module:

- critic_runner: pass/fail outcomes, 401 routing
- auto_patch: P1, P2 rule application
- compile_spec: API surface generation
- (plus shared coverage of Tier-3 modules — see [tier3-pipeline.md](tier3-pipeline.md))

All 20 tests across Tier-1 and Tier-2 pass on Py 3.14 / Windows.
