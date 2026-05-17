---
type: router
last_verified: 2026-05-18
owner: claude
---

# one-shot-prompting Plugin — v4.0.0

Production agentic one-shot generation. Claude conducts 9-stage
pipeline → 10 specialist agents → 25+ deterministic tools.

## Quick Navigation

| For... | See... |
|---|---|
| Tier 1 pipeline | `docs/tier1-pipeline.md` |
| Tier 2 (closed loop) | `docs/tier2-pipeline.md` |
| Tier 2.5 (spec-driven) | `docs/tier25-pipeline.md` |
| Tier 3 (curriculum, drift) | `docs/tier3-pipeline.md` |
| Tier 3.5 (agentic restructure) | `docs/tier35-agentic.md` |
| Tier 4 (self-extending) | `docs/tier4-self-extending.md` |
| Tier 5 (observability) | `docs/tier5-observability.md` |
| Scorecard v4 | `docs/scorecard-v4.md` |
| Path to 10/10 | `docs/path-to-10.md` |
| Production deployment | `docs/production-deployment.md` |
| Observability stack | `docs/observability/` |
| Cookbook | `docs/cookbook.md` |
| Marketplace submission | `MARKETPLACE_SUBMISSION.md` |

## Structure (v4.0.0)

```
.claude/    hooks, 10 agents, standards, registry, beads
skills/     9 skills
commands/   20 slash commands
docs/       per-tier reference + observability + cookbook + scorecards
tests/      133 invocation tests + evals + agentic replays
```

## Agentic pipeline stages (9 total)

```
0    curriculum + predictive failure scan
0.5  external discovery (registry + curator)
1    scan + extract domain model
1.5  cost-budget gate
2    architect → spec.json
2.5  spec review (--review flag)
2.7  service-author (when invariants exist)
3    implementer×N + test-author (parallel)
4    verify + auto-patch
5    reviewer
6    wire + 6.5 migration
7    critic (N-iter loop, max 3)
8    record (graph + beads)
```

## Critical Rules

1. CLAUDE.md < 100 lines — route to L2/L3
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

# Operations
/rollback                  # undo last --apply
/docs-drift                # propose doc updates
/autonomy get-level
/curate <task>             # find external agents/MCPs

# Tests
bash .claude/scripts/smoke-test.sh
python -m pytest tests/
python tests/evals/pass_k_runner.py --mode deterministic-replay --k 5
```

---

Updated 2026-05-18 (v4.0.0)
