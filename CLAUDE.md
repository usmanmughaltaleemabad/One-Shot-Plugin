---
type: router
last_verified: 2026-05-25
owner: claude
---

# one-shot-prompting Plugin — v1.2.0

> **Auditing?** Start with [docs/architecture/agent-first-principle.md](docs/architecture/agent-first-principle.md),
> then read `SKILL.md` → agents → scripts (in that order).
> See [AUDIT_ME_FIRST.md](AUDIT_ME_FIRST.md).

Production agentic one-shot generation. 14-stage pipeline → 18 specialist agents → 50+ deterministic tools.
**960+ tests green**, 101 body hints, 35+ slash commands. Phase 3 Complete: Policy engine, knowledge store,
intent routing, advanced curriculum. Phase 4 Complete: Comprehensive audit (8.3/10 score). PRODUCTION READY.

## Quick Navigation

| For... | See... |
|---|---|
| Phase 3: Policy, Knowledge, Routing | `docs/governance/` + `docs/learning/` + `docs/routing/` |
| Phase 4 Audit Results (8.3/10) | `audit/AUDIT_SUMMARY_2026-05-25.md` |
| v1.2.0 Release Notes | `RELEASE_NOTES_v1.2.0.md` |
| Ride-sharing Example (87 endpoints) | `examples/ride-sharing-system/README.md` |
| Agent-first principle | `docs/architecture/agent-first-principle.md` |
| Pipeline tier docs | `docs/tier{1,2,25,3,35-agentic,4-self-extending,5-observability}.md` |
| OTel monitoring guide | `docs/observability/README.md` |
| Production deployment | `docs/production-deployment.md` |
| Troubleshooting | `TROUBLESHOOTING.md` |
| Release history | `CHANGELOG.md` |

## Structure

```
.claude/         hooks, 18 agents (core + Phase 3 + WS1-5), standards, registry, external/
skills/          16 skills (one-shot-generate primary; P3 policy/routing/knowledge)
commands/        35+ slash commands (policy, knowledge, routing, rollback, docs-drift, curate)
docs/            per-tier reference + Phase 3 guides (governance, learning, routing) + observability
examples/        ride-sharing-system complete example (87 endpoints, 11 tables)
tests/           960+ invocation tests + evals + agentic replays + integration harness
audit/           Phase 4 comprehensive audit (8.3/10 score, production ready)
.archive/        historical phase4-5 stubs (untracked since v4.13)
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
# Primary Feature Generation
/one-shot "<feature>" @./my-project              # dry-run
/one-shot "..." @./my-project --apply            # mutate main.py
/one-shot "..." @./my-project --budget=0.30
/one-shot "..." @./my-project --review

# Phase 3 Operations (NEW in v1.2.0)
/policy "<policy-rule>"                          # Define governance policy
/knowledge "<query>"                             # Query knowledge store
/routing "<intent>"                              # Analyze intent routing

# Advanced Operations
/docs-drift                                       # Detect docstring drift (WS2)
/rollback --apply-safety-check                   # Autonomous rollback (WS3)
/multi-stage-workflow "<steps>"                  # Workflow orchestration (WS5)
/curate --discover-mcp                           # MCP service discovery (WS5)

# Operations & Maintenance
/autonomy /prune /ship-check /perf-audit
/learnings /dashboard /interview /refine /context /adr /explain /dream

# Observability
OSP_OTEL_ENABLED=1 /one-shot "..."               # Enable Jaeger tracing

# Tests & Audit
bash .claude/scripts/smoke-test.sh
python -m pytest tests/ -q
python skills/one-shot-generator/scripts/compliance_audit.py
```

---

Updated 2026-05-25 (v1.2.0) — Phase 3 + Phase 4 Complete
