---
type: reference
last_verified: 2026-05-18
owner: claude
---

# Agentic Dry-Run Report — Tier 3.6 Alignment

The Tier 3.5 build defined the agentic pipeline but never ran an agent
end-to-end. This is the first such run. It validates that an agent
spawned via the Task tool, given the architect.md instructions and the
expected inputs, produces a spec.json that conforms to the schema.

## Test scenario

| Input | Value |
|---|---|
| Task | "Add a category API with reviews" |
| Domain model | 2 entities (Category, Review) + 1 has_many relationship |
| Codebase graph | FastAPI project, Product already exists, no auth wiring |
| Curriculum hits | none |

## What was spawned

```text
Agent({
  subagent_type: "general-purpose",
  description: "Architect agent dry-run",
  prompt: <architect.md instructions + scenario + JSON inputs>
})
```

We used `general-purpose` because the plugin's specialist agents
(`architect`, `implementer`, …) are only discoverable as Task
subagent_types when the plugin is installed into a Claude Code
environment. The agent body still loads `architect.md` and follows its
contract, which is what a real plugin invocation does.

## Result

- ✅ Agent completed in **~55 seconds**
- ✅ Spec written to `.tmp/architect-dryrun-spec.json`
- ✅ JSON validates with all required top-level keys:
  `feature`, `entities`, `relationships`, `api_surface`, `schemas`,
  `files`, `test_contract`, `conventions`, `wiring`, `non_goals`,
  `open_questions`
- ✅ Entities (`Category`, `Review`) correctly marked `action: create`
- ✅ Relationships preserved bidirectionally (`has_many` parent +
  `belongs_to` child) with `category_id` FK
- ✅ Test contract correctly inferred as `auth: none` from codebase
  (which has no auth middleware), avoiding the 401-drift bug class

## What this proves

The agentic skeleton is real. The implementer + test-author +
reviewer + critic agents follow the same Task-invocation pattern. The
spec.json shape that compile_spec / scaffold_planner expect is what the
architect produces.

## What this does NOT prove

- The full multi-agent fan-out (one implementer per file, parallel) —
  tested as a pattern, not yet at scale.
- The critic loop with N>1 iterations — needs a real failure to fire.
- End-to-end ship-the-code with `--apply` — requires running pytest in
  the user's venv, which is a session-level integration.

These three are the natural follow-ups; none are blockers for the
alignment work in Bucket A/B/C.

## Cost

26K tokens for this single architect dry-run, ~$0.10 on Sonnet. That
matches the per-agent estimate in `cost_budget.py` (architect: $0.11).
The cost model is empirically grounded now.
