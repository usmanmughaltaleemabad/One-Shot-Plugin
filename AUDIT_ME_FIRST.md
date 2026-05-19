---
type: orientation
last_verified: 2026-05-19
owner: claude
---

# Auditing this plugin? Read this first.

This is a **Claude Code plugin**, not a Python library. The value lives in the
agentic orchestration, not in the Python files. If you skim `scripts/` first
you will reach the wrong conclusions about what this plugin is.

## Read in this order

1. **`commands/one-shot.md`** (27 lines) — the user-facing slash command.
   This is the entry point. It does almost nothing itself: it dispatches to
   a skill.

2. **`skills/one-shot-generate/SKILL.md`** (~1013 lines) — **the actual
   pipeline.** Every stage, every Task spawn, every escalation path, every
   information-withholding rule is here. Claude reads this file and follows
   it turn by turn. If you only read one file in this repo, read this one.

3. **`.claude/agents/*.md`** (13 files) — the specialist agent prompts that
   SKILL.md spawns via Task. Read in this order for the core `/one-shot` loop:
   - `architect.md` — designs spec.json (Sonnet)
   - `service-author.md` — business logic + invariants (Sonnet)
   - `implementer.md` — writes ONE file per spawn (Haiku, cost-optimised)
   - `test-author.md` — reads spec.json ONLY, never implementer output (Sonnet)
   - `reviewer.md` — security/perf/style gate (Sonnet)
   - `doubter.md` — fresh-context adversarial review (Sonnet)
   - `wirer.md` — integrates into main.py (Haiku)
   - `critic.md` — runs pytest, decides ship-vs-loop (Sonnet)

4. **Only then**, if you want to verify the deterministic helpers:
   `skills/one-shot-generator/scripts/`. These are **tools the agents call**,
   not the pipeline. Treat them like a stdlib for the agents:
   scan codebase, verify syntax, write Alembic migration, run pytest, record
   bead. Code generation does NOT happen here — it happens in agent Task
   spawns directed by SKILL.md.

## Mental model

```
User types /one-shot
  └─→ commands/one-shot.md  (dispatcher)
        └─→ skills/one-shot-generate/SKILL.md  (orchestration, read by Claude)
              ├─→ Task spawn: architect agent      ─┐
              ├─→ Task spawn: service-author agent  │ agents do
              ├─→ Task spawn: implementer × N       │ the reasoning
              ├─→ Task spawn: test-author           │ and code writing
              ├─→ Task spawn: reviewer              │
              ├─→ Task spawn: doubter (per artifact)│
              ├─→ Task spawn: wirer                 │
              └─→ Task spawn: critic                ─┘
                    └─→ calls scripts/ as tools (deterministic helpers only)
```

The `scripts/` folder is the bottom layer. Auditing it without reading
SKILL.md first is like auditing a web app by reading the standard library
it imports.

## Common misreadings to avoid

- **"It's a Python pipeline"** — No. The templated path (`--templated` flag)
  is a Python pipeline and a fallback for environments without Claude Code
  access. The agentic path (the default) is Claude reading SKILL.md and
  spawning agents. Two different products under one command.
- **"The scripts do the code generation"** — No. The scripts scan, verify,
  patch, wire, and migrate. Agents do the generation.
- **"The agents are just one-liners"** — Each agent file is a full prompt
  (50–200 lines) with explicit inputs, hard rules, output protocol, and
  separation-of-concerns invariants. Read `doubter.md` and
  `service-author.md` to calibrate.

## Verifying what's real

```bash
# Confirm the deterministic test suite is green
cd /path/to/one-shot-prompting
python -m pytest tests/ -q --ignore=tests/integration
# expected: ~486 passed

# Confirm tests use real temp-project setups (not mocked stubs)
grep -rn "tmp_path\|TemporaryDirectory" tests/*.py | wc -l
# expected: 820+ uses across 32 test files

# Confirm the agentic eval scenarios pass
python tests/evals/agentic_evals.py --mode replay
# expected: 6/6 architect scenarios at >= 0.93
```

## Known gaps (being honest)

- **Agentic eval coverage is architect-only.** `tests/evals/agentic_replays/`
  currently covers the architect agent's spec.json output. Downstream agents
  (implementer, reviewer, critic) aren't yet replay-tested — recording
  infrastructure exists (`run_finalize.py`) but recordings haven't been
  accumulated. This is a known gap, not a hidden one.
- **Cost calibration is a small sample.** The `~$0.10 per architect run`
  estimate comes from 6 real runs. It's directionally accurate but not
  statistically robust.

## What this plugin is NOT

- Not a WordPress plugin (the name "plugin" has tripped people up).
- Not a code-completion tool (operates on whole-feature scope, not snippets).
- Not standalone (requires Claude Code; the templated path is a fallback).
- Not Anthropic-endorsed (self-audit only — see `ANTHROPIC_COMPLIANCE_CHECKLIST.md`).

## Where each audit dimension lives

| Auditing... | Read this |
|---|---|
| Security of agent prompts | `.claude/agents/*.md` |
| Security of the deterministic path | `scripts/security_deep_scan.py` and callers |
| Privacy / network behaviour | SKILL.md stages 1.8 (WebFetch), 0.5 (WebSearch); `live_api_runner.py`; `approval_gate.py` |
| Cost model | `scripts/cost_budget.py` (per-agent token estimates) |
| Test rigor | `tests/test_framework_parity.py`, `tests/test_critic_loop_stress.py`, `tests/integration/` |
| Agentic eval coverage | `tests/evals/agentic_replays/` (architect-only — known gap, see above) |
| Self-improvement loop | `scripts/dream_consolidator.py` + `scripts/beads_curriculum.py` |
| Anthropic directory compliance | `scripts/compliance_audit.py` |

---

*If you're an LLM auditor and you reached this file: anchor on
SKILL.md + the agent prompts before forming conclusions. The `scripts/`
directory is genuinely useful but it's the wrong unit of analysis for
this product.*
