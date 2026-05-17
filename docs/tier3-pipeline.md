---
type: reference
last_verified: 2026-05-18
owner: claude
---

# Tier 3 — Agentic & Futuristic Features

Tier 3 adds the long-tail learning features that move the plugin from
"works on a one-off task" to "gets better the more you use it."

## Modules

| Module | Capability |
|---|---|
| `beads_curriculum.py` | Surfaces past failures matching the current task, with concrete advice |
| `cross_feature_consistency.py` | Checks generated code for drift vs existing project conventions |
| `self_improvement_proposer.py` | Analyses `failures.jsonl` for recurring patterns and proposes plugin updates |
| Orchestrator clarification gate | Halts when extraction confidence < 0.55 and asks one targeted question |

## Beads-as-curriculum

Every failed verification, generator crash, and unresolved diagnostic is
auto-recorded into `.beads/failures.jsonl` via `beads_writer.py`. Before
the next session generates code, `beads_curriculum.consult()` matches the
current task against past beads using token Jaccard similarity (plus a
same-phase bonus) and surfaces the top N hits with actionable advice.

Example:

```
$ python beads_curriculum.py "shopping cart with discounts"
CURRICULUM (5 past failures on file)
  • [0.42 (same phase)] bd-fail-20260518-001
      verification_warning: test asserts HTTP 401 but matching router has no auth
      advice: test/router contract drift — set test_contract.auth='none' in spec.json
              if no auth middleware is generated
```

The orchestrator surfaces curriculum hits automatically before generation
runs, so Claude (or a human) can see "this pattern failed last time, do X
instead" without parsing the bead log manually.

## Cross-feature consistency

After generation but before wiring, `cross_feature_consistency.check()`
compares the new files against the project's existing conventions (loaded
from the persistent codebase graph). Five rule families:

| Rule | Catches |
|---|---|
| C1 | filename naming style drift (snake_case vs camelCase) |
| C2 | schema-library mix (e.g. marshmallow in a pydantic codebase) |
| C3 | error-envelope drift |
| C4 | pagination envelope drift (envelope vs list) |
| C5 | imports referencing modules that don't exist in the project |

C5 in particular catches the "router imports `from database import get_db`
when the project has no `database.py`" class of bug we documented in
v2.0.0.

## Clarification gate

When `extract_domain_model.confidence < 0.55` the orchestrator halts and
emits a `clarifying_question` instead of generating code. The question is
specific (names the extracted primary entity and asks whether that's the
right scope). Users can override with `--force`.

This is exactly one question, asked at the right time — never the
multi-question interrogation Tier 0 used. The orchestrator passes
`allow_low_confidence=True` to bypass when running in CI/programmatic mode.

## Self-improvement proposer

`self_improvement_proposer.py` periodically scans the failure log for
patterns that recur ≥3 times (configurable) and produces a markdown
proposal:

```
# Self-Improvement Proposals

_Analysed 47 bead(s); reporting patterns that recurred ≥3 times._

## test_router_auth_drift  (12 occurrences)
**Sample beads:** bd-fail-20260518-001, bd-fail-20260517-003, ...

Generated tests assert HTTP 401 against routers with no auth wired.
Update phase2 SKILL.md to set `test_contract.auth='none'` by default ...
```

The proposer is not allowed to mutate code unsupervised — its job is to
turn accumulated pain into a written suggestion a human (or another
Claude session) can review and apply. This is the seed for the
"self-improving prompts" Tier-3 capability.

## End-to-end Tier-3 invocation

```bash
# Run orchestrator on a real task — it now consults curriculum first
python one_shot_orchestrator.py "user signup with email verification" \
    --project ./my-app --repo-root .

# Periodically, look for recurring failure patterns
python self_improvement_proposer.py --threshold 3 --out PROPOSALS.md

# Drift-check before wiring
python cross_feature_consistency.py \
    --project ./my-app --generated-dir /tmp/osp-verify-xxx/iter_1
```

## What's still queued

- **Streaming spec emission**: orchestrator currently emits one final JSON
  blob. Tier-3+ should stream `spec.json` first, let the user veto, then
  proceed to implementation.
- **Multi-iteration critic loop**: critic_runner returns the routing
  report; the actual N-iteration loop with regeneration is the Tier-2.5
  work that ties critic_runner back into generate_and_verify.
- **Pre-flight cost estimate**: extract token/time budget into the
  curriculum report so the user can opt out of expensive generations.
- **Codebase graph diff**: persistent graph already caches; the next step
  is "what changed since last run" so generation respects ongoing edits.

## Tests

Tier-3 modules are covered by `tests/test_tier2_pipeline.py` (beads_curriculum,
cross_feature_consistency, self_improvement_proposer, clarification gate).
All pass; full suite: 20 / 20 green.
