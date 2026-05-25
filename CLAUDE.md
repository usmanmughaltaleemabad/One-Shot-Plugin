---
type: router
last_verified: 2026-05-25
owner: claude
---

# one-shot-prompting Plugin — v1.2.2

> **Orientation:** read `docs/architecture/agent-first-principle.md`, then
> `skills/one-shot-generate/SKILL.md`, then `.claude/agents/`. The agents
> are where the work happens; scripts are deterministic helpers they call.

Agentic code-generation plugin. `/one-shot` is the primary command.
For current numbers (test count, agent count, etc.) run the commands
listed in README §"Verifying any of this yourself" — numbers belong in
shell output, not in markdown headers.

## Quick Navigation

| For... | See... |
|---|---|
| Agent-first principle | `docs/architecture/agent-first-principle.md` |
| Pipeline tier docs | `docs/tier1-pipeline.md` ... `docs/tier35-agentic.md` |
| Command maturity tiers | `docs/command-maturity.md` |
| Validation pathway (zero external users today) | `docs/validation-pathway.md` |
| OTel monitoring guide | `docs/observability/README.md` |
| Ride-sharing example (29 of 87 endpoints, runnable) | `examples/ride-sharing-system/README.md` |
| Troubleshooting | `TROUBLESHOOTING.md` |
| Release history | `CHANGELOG.md` |

## Structure

```
.claude/         hooks, agents (run `ls .claude/agents/` for current list), standards, registry
skills/          skills (one-shot-generate is primary; see skills/CLAUDE.md for index)
commands/        slash commands (see docs/command-maturity.md for stable/beta/experimental tiers)
docs/            per-tier reference + observability + patterns + validation pathway
examples/        ride-sharing-system (real code), shopping-cart, auth, etc.
tests/           pytest suite + tests/evals/ replay scenarios
.claude-plugin/  plugin.json manifest
```

## Agentic pipeline stages (14 total — 9 default-on)

```
0    curriculum + predictive failure scan
0.5  external discovery (registry + curator)
0.7  legacy-safe gate (--legacy-safe)                          ← v4.12
1    scan + extract domain model
1.5  cost-budget gate
1.8  source-driven doc lookup (pre-architect)                  ← v4.11
2    architect → spec.json (+ adr_writer)
2.5  spec review (--review)
2.6  incremental slicing (--incremental)                        ← v4.8/4.13
2.7  service-author (when invariants exist)
3    implementer × N + test-author (parallel)
4    verify + auto-patch
5    reviewer
5.5  doubter (DEFAULT ON; --no-doubt)                           ← v4.6
5.7  cross-agent consistency + security deep scan (DEFAULT ON)  ← v4.12
5.9  approval-gate webhook (--require-approval-webhook)         ← v4.11
6    ship-gates → wire (DEFAULT ON; --no-ship-check)
6.5  migration generator (Alembic / Django / Flyway)
7    critic (multi-iter loop, max 3) + mutation testing + N+1   ← v4.14
8    record (graph + beads + learnings.jsonl via run_finalize)
8.5  dream — pattern mine failures → data-driven curriculum    ← v4.15
```

For per-release feature lists see `CHANGELOG.md`.

## Critical Rules

1. CLAUDE.md ≤ 100 lines — route to L2/L3 (this file)
2. Deterministic scripts: stdlib + optional pip deps (graceful fallback)
3. All .md files: YAML frontmatter (type, last_verified, owner)
4. Agents: explicit `tools:` + `model:` (haiku for writers, sonnet for reasoners)

## Quick Commands

```bash
/one-shot "<feature>" @./my-project              # dry-run (primary)
/one-shot "..." @./my-project --apply            # mutate main.py
/one-shot "..." @./my-project --templated        # free-tier fallback
```

Other commands: see `docs/command-maturity.md` for the full list with
stable / beta / experimental tiers.

```bash
bash .claude/scripts/smoke-test.sh               # 8/8 expected
python -m pytest tests/ -q                       # full test suite
python scripts/cost_stats.py                     # cost calibration confidence
python scripts/curriculum_status.py              # self-learning loop state
```

---

Updated 2026-05-25 (v1.2.2) — audit-response corrections; no new features.
