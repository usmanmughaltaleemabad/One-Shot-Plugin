---
type: reference
last_verified: 2026-05-18
owner: claude
---

# Implementation Status — v3.5.0 (Agentic Restructure)

**Last audit: 2026-05-18 — Tier 3.5 alignment complete**

---

## Where the plugin stands

The plugin is structured as a Claude Code plugin proper: commands as user
entry points, skills as Claude's playbooks, agents as specialists, scripts
as deterministic helpers. Code generation happens primarily via Claude
(through the agents); templates remain as a free fallback path.

| Layer | Status | Detail |
|---|---|---|
| **Slash commands** | ✅ aligned | 15 commands; `/one-shot` is the primary entry point with real frontmatter (`argument-hint`, `allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task`) |
| **Skills** | ✅ aligned | 7 skills; `one-shot-generate` is the agentic path; `one-shot-generator` is the deprecated legacy template path |
| **Specialist agents** | ✅ aligned | 6 agents with explicit `tools:` + `model:` (sonnet for reasoners, haiku for file-writers) |
| **Deterministic services** | ✅ shipped | 14 modules covering scan, graph, diff, verify, patch, wire, critic, beads, consistency, self-improvement, scaffold-planning, cost-budget |
| **Template generators (legacy)** | ✅ retained | ~99 phase scripts kept as the `--templated` fallback path |
| **Tests** | ✅ green | 48/48 invocation-based tests across 4 tier suites |
| **Documentation** | ✅ aligned | Per-tier reference docs; README leads with `/one-shot`; CHANGELOG entry for 3.5.0 |

---

## Code generation: two paths, one plugin

### Primary: Agentic path (default)

```bash
/one-shot "<feature description>" @./project
```

7-stage pipeline, conducted by Claude through the `one-shot-generate`
skill:

| Stage | What runs | Where |
|---|---|---|
| 0 | `beads_curriculum.py` — past failures matching this task | Python script |
| 1 | `extract_domain_model.py` + `codebase_graph.py` | Python scripts |
| 1.5 | `cost_budget.py` (if `--budget=USD` is set) | Python script |
| 2 | **architect agent** (Task) → spec.json | Sonnet via Task |
| 3 | **implementer + test-author agents** (parallel Task) → file contents | Haiku + Sonnet via Task |
| 4 | `generate_and_verify.py` + `auto_patch.py` | Python scripts |
| 5 | **reviewer agent** (Task) — security/perf/style gate | Sonnet via Task |
| 6 | `auto_wirer.py` (dry-run unless `--apply`) | Python script |
| 7 | **critic agent** (Task) — runs `critic_runner.py`, verdicts | Sonnet + Bash |
| 8 | Refresh `codebase_graph` + (on failure) `beads_writer.py` | Python scripts |

Cost: ~$0.30–0.80 per generation. Quality: Claude reasons about the
user's actual codebase, not a template.

### Fallback: Templated path

```bash
/one-shot "<feature description>" @./project --templated
```

Routes directly to `one_shot_orchestrator.py` which runs the 99 phase
scripts under `scripts/`. Zero Claude tokens. Lower quality (templates
can't reason). Useful for CI / sandboxed / cost-sensitive scenarios.

---

## Deterministic services (the muscles)

Every one of these is a pure-Python script with no LLM calls, no external
dependencies. They are testable via subprocess; they form the foundation
both paths share.

| Module | Role |
|---|---|
| `lib/base_script.bootstrap_runtime()` | Windows UTF-8 + sys.path bootstrap (call from every script) |
| `extract_domain_model.py` | Natural-language → entities + relationships + intent + confidence |
| `existing_codebase_scanner.py` | AST scan of user's project → domain graph |
| `codebase_graph.py` | Persistent on-disk cache of the scan |
| `codebase_diff.py` | What changed since last scan |
| `generate_and_verify.py` | Sandbox write → static verify → diagnostics |
| `auto_patch.py` | Deterministic fixes (P1–P4 rules) |
| `auto_wirer.py` | Idempotent `main.py` / `urls.py` edit + `.osp.bak` backup |
| `critic_runner.py` | `pytest` in subprocess → structured outcomes + routing |
| `live_critic.py` | `pytest` against the wired project (new feature vs regression) |
| `beads_writer.py` | Append-only failure log at `.beads/failures.jsonl` |
| `beads_curriculum.py` | Surfaces past failures matching the current task |
| `cross_feature_consistency.py` | 5-rule drift checker vs codebase graph |
| `self_improvement_proposer.py` | Pattern analysis → markdown proposals |
| `scaffold_planner.py` | spec.json → plan.json (paths + FKs + imports, NO bodies) |
| `cost_budget.py` | Estimates Claude token spend before agent spawn |
| `compile_spec.py` | OrchestratorReport → spec.json |
| `run_critic_loop.py` | N-iteration generate→verify→patch→critic loop |
| `one_shot_orchestrator.py` | Unified deterministic pipeline (headless / `--templated` mode) |

---

## Agentic specialists (the brains)

All under `.claude/agents/`, all with explicit `tools:` and `model:`
frontmatter, all invocable via the Task tool.

| Agent | Model | Tools | Role |
|---|---|---|---|
| `architect` | sonnet | Read, Grep, Glob, Bash, Write | Designs spec.json |
| `implementer` | **haiku** | Read, Grep, Edit, Write, Bash | Writes ONE file from spec |
| `test-author` | sonnet | Read, Grep, Write, Bash | Independent of implementer |
| `reviewer` | sonnet | Read, Grep, Bash | Security/perf/style gate |
| `wirer` | **haiku** | Read, Edit, Bash | Integrates into main.py |
| `critic` | sonnet | Read, Bash | Runs pytest, ship-or-loop verdict |

Cost mix: **Haiku for the bulk** (one implementer per file, plus the
wirer); **Sonnet for the reasoning** (architect, test-author, reviewer,
critic). This is ~5× cheaper than a pure-Sonnet run.

---

## Validation status

- **48 invocation-based pytest tests, all green** on Py 3.14 / Windows
  (Tier 1: 9, Tier 2: 11, Tier 2.5: 9, Tier 3.5: 15)
- **2 pre-existing fixture failures** in `test_integration_fixtures.py`
  documented in `VALIDATION_REPORT.md` (Django `orm == 'django_orm'`
  capitalization mismatch + missing `app_root` in fixture)
- **Architect-agent dry-run via Task tool**: ✅ produced valid spec.json
  with all required keys (Category + Review entities, has_many
  relationship, test_contract correctly inferred from codebase), ~$0.10
  on Sonnet (matches `cost_budget.py` estimate). See
  `.tmp/AGENTIC_DRYRUN_REPORT.md`

---

## Legacy phase generators (still useful as fallback)

The `--templated` path still runs these. They're production-quality for
their original scopes; the agentic path produces better code by reasoning
about the user's project, but the templates remain useful for zero-cost CI.

| Phase | Modules | Status under v3.5 |
|---|---|---|
| Phase 0 | 4 | ✅ kept — planning + verification harness |
| Phase 1 | 8 | ✅ kept — multi-file + auto-wire + migrations |
| Phase 2 | 44 | ✅ kept — REST API CRUD/auth/pagination/webhooks |
| Phase 3 | 13 | ✅ kept — batch jobs (queues, retries, DLQ) |
| Phase 4 | ~49 | ✅ kept — DDD / CQRS / event sourcing / compliance |
| Phase 5 | ~50 (was 59) | ✅ kept; 9 thin stubs archived to `.archive/phase4-5-aspirational/` |

Total: ~168 phase scripts (was 177). All callable via the `--templated`
path. None are required by the agentic path.

---

## What's still queued (not blocking alignment)

These are improvement items, not gaps in the current architecture:

1. **Multi-iteration critic loop driver inside SKILL.md** — the playbook
   lists the stages; the exact prompt structure for "respec on LOOP and
   re-spawn implementer for the failing file" needs first-real-run
   refinement.
2. **Cross-language scaffold_planner variants** — currently FastAPI-only.
   Django, Spring, Go, NestJS variants are the obvious next-rung.
3. **Empirical cost calibration** — `cost_budget.py` uses educated
   estimates; replace with measured p50/p95 after ~20-30 real
   generations.
4. **Streaming spec emission** — orchestrator should emit `spec.json` to
   the user before generation for `--review` approval.

---

## Documentation map

| File | Topic |
|---|---|
| `CLAUDE.md` (root) | L1 router (≤100 lines) |
| `docs/tier1-pipeline.md` | Codebase-aware foundations |
| `docs/tier2-pipeline.md` | Closed loop + agents-as-docs |
| `docs/tier25-pipeline.md` | Spec-driven, FK-aware |
| `docs/tier3-pipeline.md` | Curriculum, drift, gates |
| `docs/tier35-agentic.md` | **Agentic restructure (current architecture)** |
| `VALIDATION_REPORT.md` | 8 real bugs caught by real-use testing |
| `CHANGELOG.md` | Version history (3.5.0 covers Tier 1 → 3.5) |
| `README.md` | User-facing: `/one-shot` quick start |
| `docs/skill-authoring.md` | How to write a new SKILL.md |
| `docs/publish.md` | Release / marketplace workflow |
| `docs/scripts-index.md` | All scripts catalogued |
