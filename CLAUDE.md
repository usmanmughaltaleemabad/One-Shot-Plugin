---
type: router
last_verified: 2026-05-25
owner: claude
---

# one-shot-prompting Plugin — v1.1.0

> **Auditing?** Start with [docs/architecture/agent-first-principle.md](docs/architecture/agent-first-principle.md),
> then read `SKILL.md` → agents → scripts (in that order).
> See [AUDIT_ME_FIRST.md](AUDIT_ME_FIRST.md).

Production agentic one-shot generation. 14-stage pipeline → 13 specialist agents → 50+ deterministic tools.
**800+ tests green**, 101 body hints, 35+ slash commands. TIER A Workstreams (WS1-5) complete: OTel monitoring,
docs drift detection, autonomous rollback, predictive failure detection, awesome-ai-apps integration.

## Quick Navigation

| For... | See... |
|---|---|
| Agent-first principle (NEW) | `docs/architecture/agent-first-principle.md` |
| TIER A Workstreams summary | `docs/tier35-agentic.md` → "TIER A Completion" section |
| Pipeline tier docs | `docs/tier{1,2,25,3,35-agentic,4-self-extending,5-observability}.md` |
| OTel monitoring guide | `docs/observability/README.md` |
| Docs drift & rollback | `/docs-drift` command, `/rollback` command |
| Multi-stage workflow | `/multi-stage-workflow` skill, examples/ |
| MCP discovery & integration | `/curate --discover-mcp` flag |
| Production deployment | `docs/production-deployment.md` |
| Troubleshooting | `TROUBLESHOOTING.md` |
| Release history | `CHANGELOG.md` |

## Structure

```
.claude/         hooks, 13 agents + 3 new WS1-5 agents, standards, registry, external/
skills/          14 skills (one-shot-generate primary; docs-drift, multi-stage-workflow NEW)
commands/        35+ slash commands (9 marked experimental; /docs-drift, /rollback, /curate)
docs/            per-tier reference + observability (OTel) + awesome-ai-apps patterns + WS guides
docs/architecture/agent-first-principle.md (NEW)
tests/           800+ invocation tests + evals + agentic replays + integration harness
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
# Primary
/one-shot "<feature>" @./my-project              # dry-run
/one-shot "..." @./my-project --apply            # mutate main.py
/one-shot "..." @./my-project --budget=0.30
/one-shot "..." @./my-project --review
/one-shot "..." @./my-project --templated        # free fallback
/one-shot "..." @./my-project --incremental      # entity-per-slice
/one-shot "..." @./my-project --legacy-safe      # critical-codebase mode

# WS1-5 Operations (NEW in v1.1.0)
/docs-drift                                       # Detect docstring drift (WS2)
/rollback --apply-safety-check                   # Autonomous rollback on failure (WS3)
/multi-stage-workflow "<steps>"                  # Orchestrate multi-step workflows (WS5)
/curate --discover-mcp                           # Discover & integrate MCP services (WS5)

# Legacy Operations
/autonomy /prune /ship-check /perf-audit
/learnings /dashboard /interview /refine /context /adr /explain /dream

# Observability (WS1 OTel)
OSP_OTEL_ENABLED=1 /one-shot "..."               # Enable Jaeger tracing

# Tests + audit
bash .claude/scripts/smoke-test.sh
python -m pytest tests/
python skills/one-shot-generator/scripts/compliance_audit.py
```

---

Updated 2026-05-25 (v1.1.0) — TIER A Workstreams complete
