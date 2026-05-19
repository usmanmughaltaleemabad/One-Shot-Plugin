---
type: orientation
last_verified: 2026-05-19
owner: claude
---

# Auditing this plugin? Read this first.

This is a **Claude Code plugin**, not a Python library. The value lives in the
agentic orchestration, not in the Python files. If you skim `scripts/` first
you will reach the wrong conclusions about what this plugin is.

**Current version:** v1.0.0 (label reset from internal v4.15; see CHANGELOG).
**Tests:** 509 invocation-based, cross-OS CI (Ubuntu × macOS × Windows × Py 3.10–3.12).

---

## Read in this order

1. **`commands/one-shot.md`** (27 lines) — the user-facing slash command.
   Entry point. Does almost nothing itself: dispatches to a skill.

2. **`skills/one-shot-generate/SKILL.md`** (96-line dispatcher) — routes
   `--templated` to the deterministic fallback, otherwise loads the 5 stage
   files in order. **This is the pipeline's entry point**, not the scripts.

3. **`skills/one-shot-generate/stages/*.md`** (5 files) — the actual
   pipeline stages. Read these in order:
   - `plan.md` — Stages 0–2.7: curriculum, scan, grill-me (1.6), architect, service-author
   - `build.md` — Stage 3: implementer × N + test-author (or tdd-cycle on `--tdd-strict`)
   - `verify.md` — Stages 4–5.7: auto-patch, reviewer (with caveman compression), doubter, consistency + SAST
   - `ship.md` — Stages 6–7: wire, migrate, approval gate, critic loop (with systematic-debug on repeat failures)
   - `record.md` — Stages 8–8.5: graph refresh, learnings, dream consolidation, handoff runbook

4. **`.claude/agents/*.md`** (13 files) — specialist agent prompts the stages
   spawn via Task. Read these in order for the core loop:
   - `architect.md` — designs spec.json (Sonnet)
   - `service-author.md` — business logic + invariants (Sonnet)
   - `implementer.md` — writes ONE file per spawn (Haiku, cost-optimised)
   - `test-author.md` — reads spec.json ONLY, never implementer output (Sonnet)
   - `reviewer.md` — security/perf/style gate (Sonnet)
   - `doubter.md` — fresh-context adversarial review (Sonnet)
   - `wirer.md` — integrates into main.py (Haiku)
   - `critic.md` — runs pytest, decides ship-vs-loop (Sonnet)

5. **Only then**, if you want to verify the deterministic helpers:
   `skills/one-shot-generator/scripts/` (62 active scripts). These are
   **tools the agents call**, not the pipeline. Treat them like a stdlib for
   the agents: scan codebase, verify syntax, write Alembic migration, run
   pytest, record bead. Code generation does NOT happen here — it happens in
   agent Task spawns directed by the stages.

---

## Mental model

```
User types /one-shot
  └─→ commands/one-shot.md                   (dispatcher)
        └─→ skills/one-shot-generate/SKILL.md  (flag routing + stage loader)
              ├─→ stages/plan.md   → architect agent + grill-me (when ambiguous)
              ├─→ stages/build.md  → implementer × N + test-author (or tdd-cycle)
              ├─→ stages/verify.md → reviewer + doubter (+ caveman compression)
              ├─→ stages/ship.md   → wirer + critic loop (+ systematic-debug)
              └─→ stages/record.md → finalize + dream + handoff
                    └─→ all stages call scripts/ as deterministic tools
```

`scripts/` is the bottom layer. Auditing it without reading the stages
first is like auditing a web app by reading its standard library.

---

## Productivity skill wiring (mattpocock-inspired)

5 skills are **actually wired into specific stages** with explicit trigger
conditions — not just listed as available:

| Skill | Stage | Trigger | Opt-out |
|---|---|---|---|
| **grill-me** | 1.6 PLAN | feature ambiguous (< 50 chars, 0 entities, confidence < 0.55) OR `--grill` | `--force` |
| **tdd-cycle** | 3 BUILD | `--tdd-strict` flag | (default off) |
| **caveman** | 5 VERIFY | reviewer prompt > 8k tokens | `--no-compress` |
| **systematic-debug** | 7 SHIP | critic iteration ≥ 2 with same failure | `--no-systematic-debug` |
| **handoff** | 8.5 RECORD | SHIPPED verdict | `--no-handoff` |

The wiring is enforced by 17 tests in
[`tests/test_mattpocock_skill_wiring.py`](tests/test_mattpocock_skill_wiring.py).
If anyone removes a skill from its stage, CI fails.

A 6th skill — `write-a-skill` — is a meta-skill the curator uses when it
finds an external-skill gap, not a pipeline stage.

---

## Common misreadings to avoid

- **"It's a Python pipeline"** — No. The `--templated` flag is a Python
  pipeline (fallback for environments without Claude Code). The agentic
  default is Claude reading SKILL.md + stages and spawning agents.
- **"The scripts do the code generation"** — No. Scripts scan, verify,
  patch, wire, and migrate. Agents do the generation.
- **"The agents are just one-liners"** — Each agent file is a full prompt
  (50–200 lines) with explicit inputs, hard rules, output protocol, and
  separation-of-concerns invariants. Read `doubter.md` and
  `service-author.md` to calibrate.
- **"The productivity skills are optional add-ons"** — They're wired into
  specific stages with documented trigger conditions and tests that enforce
  the wiring. Available, but also auto-invoked when conditions match.

---

## Verifying what's real

```bash
# Confirm the test suite is green (no API key needed)
python -m pytest tests/ -q --ignore=tests/integration
# expected: ~509 passed

# Confirm the skill wiring claims are real (no API key needed)
python -m pytest tests/test_mattpocock_skill_wiring.py -v
# expected: 17/17 passed

# Confirm tests use real temp-project setups (not mocked stubs)
grep -rn "tmp_path\|TemporaryDirectory" tests/*.py | wc -l
# expected: 820+ uses across 30+ test files

# Confirm the agentic eval scenarios pass (no API key — replay mode)
python tests/evals/agentic_evals.py --mode replay
# expected: 14/14 scenarios across 7 agent types (architect / implementer /
# test-author / reviewer / doubter / critic / handoff) at overall >= 0.85

# Confirm scripts count is the cleaned-up surface, not the graveyard
ls skills/one-shot-generator/scripts/*.py | wc -l
# expected: ~62 (down from 231; 169 dead phase4/phase5 stubs archived)
```

---

## Known gaps (being honest)

| Gap | Detail |
|---|---|
| **Agentic eval coverage** | 14 replay scenarios across 7 agent types (architect, implementer, test-author, reviewer, doubter, critic, handoff). 6 architect scenarios are real recorded outputs; the other 8 are contract-test fixtures that validate the grader. Real recordings for non-architect agents still need accumulation from live runs. |
| **No live end-to-end CI test by default** | `.github/workflows/e2e.yml` has two jobs: `e2e-dry` (always runs, validates 14 replays + wiring + seed) and `e2e-live` (gated on `ANTHROPIC_API_KEY`, costs ~$0.30/run). See [docs/CI_SETUP.md](docs/CI_SETUP.md) to enable live verification. |
| **Cost calibration** | `~$0.10 architect / ~$0.50 feature` estimates come from 6 real runs. Directionally right, not statistically robust. |
| **Zero external users** | The plugin has never shipped code into a project by a user who wasn't the author. All quality claims are self-validated. |
| **Self-learning loop is empty** | Dream consolidator + curriculum advice are wired and tested but `.beads/failures.jsonl` is gitignored and effectively unpopulated. Needs real runs to start working. |

See `docs/scorecard-v4.md` for the full honest scoring across 36+ dimensions.

---

## What this plugin is NOT

- **Not a WordPress plugin** (the name "plugin" has tripped people up).
- **Not a code-completion tool** (operates on whole-feature scope, not snippets).
- **Not standalone** (requires Claude Code; the `--templated` path is a fallback).
- **Not Anthropic-endorsed** — self-audit only via `compliance_audit.py`.
  Directory submission prepared, not yet submitted. See `ANTHROPIC_COMPLIANCE_CHECKLIST.md`.

---

## Where each audit dimension lives

| Auditing... | Read this |
|---|---|
| Pipeline structure | `skills/one-shot-generate/SKILL.md` + `stages/*.md` |
| Agent prompt quality | `.claude/agents/*.md` (start with architect, doubter, service-author) |
| Skill wiring (claim → reality) | `tests/test_mattpocock_skill_wiring.py` |
| Security of agent prompts | `.claude/agents/*.md` + `scripts/security_deep_scan.py` |
| Privacy / network behaviour | `stages/plan.md` (Stage 1.8 WebFetch + Stage 0.5 WebSearch), `live_api_runner.py`, `approval_gate.py` |
| Cost model | `scripts/cost_budget.py` (per-agent token estimates) |
| Test rigor | `tests/test_framework_parity.py`, `tests/test_critic_loop_stress.py`, `tests/integration/` |
| Self-improvement loop | `scripts/dream_consolidator.py` + `scripts/beads_curriculum.py` |
| Anthropic directory compliance | `scripts/compliance_audit.py` (self-audit, not Anthropic-reviewed) |
| Harness examples | `examples/*-harness/.claude/` (FastAPI, Django, Spring, Node, Go) |

---

*If you're an LLM auditor and you reached this file: anchor on
SKILL.md + stages + the agent prompts before forming conclusions. The
`scripts/` directory is genuinely useful but it's the wrong unit of analysis
for this product.*
