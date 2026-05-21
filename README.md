# ONE SHOT PLUGIN (Claude Code Studio)

> **Auditing or evaluating this plugin?** Start with **[AUDIT_ME_FIRST.md](AUDIT_ME_FIRST.md)** — the agentic pipeline lives in `skills/one-shot-generate/SKILL.md` and the agent prompts under `.claude/agents/`, not in `scripts/`. Reading `scripts/` first leads to the wrong mental model.

**Production agentic one-shot code generation for existing codebases.**

Type `/one-shot "shopping cart with line items and discounts" @./my-project` and Claude reads `skills/one-shot-generate/SKILL.md` and orchestrates a 14-stage pipeline through 13 specialist agents — architect → service-author → implementer×N + test-author (parallel) → reviewer → doubter → wirer → critic — to ship verified, FK-aware, migration-emitting, cost-gated code into your project.

5 mattpocock-inspired productivity skills are wired into specific stages: **grill-me** sharpens ambiguous requirements (Stage 1.6), **tdd-cycle** enforces RED→GREEN→REFACTOR on `--tdd-strict` (Stage 3), **caveman** compresses reviewer prompts >8k tokens (Stage 5), **systematic-debug** breaks the critic guess-loop on repeat failures (Stage 7), and **handoff** emits a deployment runbook on SHIPPED (Stage 8.5). 17 enforcement tests guard the wiring.

Multi-entity, relationship-aware. Real Alembic migrations. Real OpenAPI 3.1 docs. Real bcrypt + JWT auth helpers. Real service layer enforcing business invariants. Cost-tiered model routing (Haiku for file-writers, Sonnet for reasoners) keeps a typical generation at ~$0.50. Free `--templated` fallback for CI / cost-sensitive contexts.

## ⭐ v1.0.0 — Status

| Metric | Value |
|---|---|
| **Tests** | 531 / 531 green (32 suites, cross-OS CI: Ubuntu × macOS × Windows × Py 3.10–3.12) |
| **Active scripts** | 62 (down from 231; 169 dead phase4/phase5 stubs archived) |
| **Specialist agents** | 13 in `.claude/agents/` |
| **Skills** | 13 (one-shot-generate primary + 6 productivity + 6 supporting) |
| **Slash commands** | 30 (9 marked experimental) |
| **Skill-wiring tests** | 17 / 17 enforce mattpocock integration |
| **Agentic eval coverage** | 14 / 14 replays passing across 7 agent types (6 real architect recordings + 8 contract-test fixtures for implementer/test-author/reviewer/doubter/critic/handoff) |
| **Cost calibration anchor** | 6 real architect runs, mean 26,621 tokens / 60.4s / ~$0.10 (small sample) |
| **Anthropic Directory** | submission prepared, not yet submitted ([DIRECTORY_SUBMISSION_FORM.md](DIRECTORY_SUBMISSION_FORM.md)) |
| **Directory compliance (self-audit)** | 15/15 PASS · 0 WARN · 0 FAIL ([`compliance_audit.py`](skills/one-shot-generator/scripts/compliance_audit.py)) — not reviewed by Anthropic |
| **Try it risk-free** | [GitHub Codespaces sandbox](.devcontainer/README.md) — one-click demo, free tier |

---

## 🚀 30-second start

```bash
# 1. Clone + install
git clone https://github.com/usmanmughaltaleemabad/One-Shot-Plugin
claude --plugin-dir ./One-Shot-Plugin

# 2. Generate a feature (dry-run wire)
/one-shot "shopping cart with line items and discounts" @./your-fastapi-project

# 3. Review the spec + diff, then ship
/one-shot "..." @./your-project --apply
```

That's it. Claude takes over from here — scans your project, designs the spec, spawns the agents in parallel, runs tests, wires the routers, and writes the migration.

---

## How it works (30-second mental model)

Four phases. You only ever type one command; the plugin does the rest.

```
┌──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│      PLAN        │      BUILD       │     VERIFY       │       SHIP       │
├──────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ scan codebase    │ implementer × N  │ auto-patch       │ wire main.py     │
│ extract entities │ + test-author    │ reviewer agent   │ ship-gates check │
│ grill-me if      │ (parallel) or    │ + caveman if     │ Alembic migration│
│ ambiguous (1.6)  │ tdd-cycle on     │ prompt > 8k      │ critic runs tests│
│ architect → spec │ --tdd-strict     │ doubter agent    │ + systematic-debug│
│ source-doc fetch │                  │ (fresh-context)  │  on repeat fails │
│ ADR emission     │                  │                  │ handoff runbook  │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┘
     ~$0.10              ~$0.20            ~$0.10            ~$0.05
```

**Total: ~$0.30–0.80 per multi-entity feature.** Free with `--templated`.

### Under the hood — 14 numbered stages

<details>
<summary>Click to expand the full stage breakdown</summary>

```
PLAN
  Stage 0    curriculum + predictive failure scan      (free)
  Stage 0.5  external-agent registry discovery         (free)
  Stage 1    scan codebase + extract domain model      (free)
  Stage 1.5  cost-budget gate (halts if over --budget) (free)
  Stage 1.6  grill-me — sharpen ambiguous features     (when triggered)
  Stage 1.8  source-driven doc lookup (WebFetch)       (free)
  Stage 2    architect agent → spec.json + ADR         ~$0.10
  Stage 2.5  spec review (--review flag)
  Stage 2.6  incremental slicing (--incremental flag)
  Stage 2.7  service-author (when invariants exist)    ~$0.08

BUILD
  Stage 3    implementer × N + test-author (parallel)  ~$0.20
             OR tdd-cycle on --tdd-strict

VERIFY
  Stage 4    verify + auto-patch                       (free)
  Stage 5    reviewer agent (+ caveman compression)    ~$0.09
  Stage 5.5  doubt-driven adversarial pass (DEFAULT ON; --no-doubt)
  Stage 5.7  cross-agent consistency + SAST deep scan (DEFAULT ON)

SHIP
  Stage 6    ship-gates → wirer + 6.5 migration_generator
  Stage 7    critic loop (max 3 iter) + systematic-debug on repeat failures
  Stage 8    record (graph refresh + per-agent learnings)
  Stage 8.5  dream consolidation + handoff runbook on SHIPPED
```

Stages 5.5, 5.7, 6, 2 (ADR), 8.5 (handoff) are **default-on** — opt out
individually via `--no-doubt`, `--no-consistency-check`, `--no-ship-check`,
`--no-adr`, `--no-handoff`.

</details>

### Productivity skills wired into the pipeline

Five skills auto-fire at specific stages. Wiring is enforced by tests — see [`tests/test_mattpocock_skill_wiring.py`](tests/test_mattpocock_skill_wiring.py).

| Skill | Stage | Trigger | Opt-out |
|---|---|---|---|
| **[grill-me](skills/grill-me/SKILL.md)** | 1.6 PLAN | feature < 50 chars, 0 entities, extractor confidence < 0.55, or `--grill` | `--force` |
| **[tdd-cycle](skills/tdd-cycle/SKILL.md)** | 3 BUILD | `--tdd-strict` flag | (default off) |
| **[caveman](skills/caveman/SKILL.md)** | 5 VERIFY | reviewer prompt > 8k tokens | `--no-compress` |
| **[systematic-debug](skills/systematic-debug/SKILL.md)** | 7 SHIP | critic iteration ≥ 2 with same failure nodeid | `--no-systematic-debug` |
| **[handoff](skills/handoff/SKILL.md)** | 8.5 RECORD | SHIPPED verdict | `--no-handoff` |

A 6th skill, **[write-a-skill](skills/write-a-skill/SKILL.md)**, is a meta-skill the curator uses when finding gaps — not a pipeline stage.

### What ships for a typical multi-entity feature

For `/one-shot "shopping cart with line items and discounts"`:

- `cart/models.py` — SQLAlchemy model with auto-generated id/created_at/updated_at
- `cart/schemas.py` — Pydantic v2 Base/Create/Read/Update schemas
- `cart/service.py` — **business logic layer** with invariants enforced + events emitted on state transitions
- `cart/router.py` — FastAPI router that delegates to the service
- `line_item/models.py` — with `shopping_cart_id` FK derived from the `has_many` relationship
- `line_item/{schemas,service,router}.py`
- `discount/{models,schemas,service,router}.py`
- `tests/test_cart_api.py` + `test_cart_service.py` (per entity)
- `common/events.py` — pub/sub stub (swap for Kafka in production)
- `common/exceptions.py` — `DomainError` hierarchy (`NotFoundError`, `ConflictError`, `ForbiddenError`, `ValidationError`)
- `alembic/versions/{timestamp}_shopping_cart.py` — **real migration** with `create_table`, FK constraints, indexes, `downgrade` in reverse
- Wire plan applied to `main.py` (`app.include_router(cart_router)` × 3)
- OpenAPI 3.1 doc with tags, descriptions, examples, security schemes

**Cost: ~$0.45. Time: ~3.5 minutes wall-clock. Files: 17.**

### Flags worth knowing

```bash
/one-shot "<feature>" @./project              # dry-run wire (default)
/one-shot "..." @./project --apply            # mutate main.py + run migrations
/one-shot "..." @./project --budget=0.30      # halt if estimated cost > $0.30
/one-shot "..." @./project --review           # gate on spec.json before agents fire
/one-shot "..." @./project --force            # bypass clarification gate (skips grill-me)
/one-shot "..." @./project --templated        # zero-token Python fallback (free, lower quality)
/one-shot "..." @./project --incremental      # ship one entity per slice with green tests + git commit
/one-shot "..." @./project --tdd-strict       # route Stage 3 through tdd-cycle (RED → GREEN → REFACTOR)
/one-shot "..." @./project --grill            # force grill-me at Stage 1.6
/one-shot "..." @./project --legacy-safe      # critical-codebase mode — caps to 3 files, blocks --apply
```

---

## 🏗️ Architecture

A proper Claude Code plugin — **skills + commands + agents as first-class units**; scripts as deterministic helpers the agents call.

```
commands/                       ← 30 slash commands (9 experimental)
  one-shot.md                     ⭐ /one-shot — primary agentic dispatcher
  rollback.md, docs-drift.md      operations
  dream.md                        self-learning consolidation
  (experimental: strangler, tour, browser-test, ...)

skills/                          ← Claude reads SKILL.md and acts
  one-shot-generate/SKILL.md      ⭐ 96-line dispatcher
  one-shot-generate/stages/       ← 5 focused stage files (plan, build, verify, ship, record)
  grill-me, caveman, tdd-cycle    ← wired into pipeline stages
  systematic-debug, handoff       ← wired into pipeline stages
  write-a-skill                   ← meta-skill, used by curator
  curator                         ← external-agent discovery via WebSearch
  one-shot-generator              ← templated fallback (--templated)

.claude/agents/                  ← 13 specialists invocable via Task
  architect       (sonnet) — designs spec.json
  service-author  (sonnet) — business logic, invariants, transactions, events
  implementer     (haiku)  — writes ONE file per spawn (cost-optimised)
  test-author     (sonnet) — independent of implementer (defends contract)
  reviewer        (sonnet) — security / perf / style gate
  doubter         (sonnet) — adversarial review, context isolation
  wirer           (haiku)  — integrates into main.py + .osp.bak safety
  critic          (sonnet) — runs pytest, decides ship-or-loop
  extractor       (sonnet) — fallback for ambiguous prose
  docs-author     (haiku)  — proposes doc updates on entity drift
  rollback        (haiku)  — undoes failed --apply, git-stash safety
  phase-planner   (sonnet) — multi-feature roadmap planning
  skill-validator (haiku)  — frontmatter + structure checks

.claude/registry/                ← self-extending capability marketplace
  agents.json, skills.json, mcp_servers.json, learnings.jsonl

.claude/hooks/                   ← 5 hooks wired via .claude/settings.json
  block-bad-commands.sh, guard-file-writes.sh, validate-after-write.sh,
  session-start.sh, session-end.sh

skills/one-shot-generator/scripts/   ← 62 active deterministic tools
  Pipeline:   extract_domain_model, codebase_graph, scaffold_planner,
              generate_and_verify, auto_patch, auto_wirer, critic_runner
  Generation: migration_generator, openapi_doc_generator, spec_driven_generator
  Learning:   beads_writer, beads_curriculum, dream_consolidator,
              learnings_hub, cost_calibrator
  Quality:    mutation_tester, context_pruner, nplus1_detector,
              sast_runner, hybrid_lint_runner, anti_rationalization_check
  Operations: cost_budget, ship_gates, approval_gate, legacy_guard,
              source_docs_fetcher
  These are NOT the pipeline. See AUDIT_ME_FIRST.md.
```

---

## Three worked examples

### Example 1 — Multi-entity feature

```bash
/one-shot "Build a shopping cart with line items and discounts" @./my-fastapi-shop
```

Extracts 3 entities + 2 has_many relationships, spawns architect → produces spec.json, spawns 3 implementer agents + test-author in parallel, generates 17 files including Alembic migration. Wirer attaches 3 routers to `main.py`. ~$0.45, ~3.5 minutes.

### Example 2 — Auth flow

```bash
/one-shot "Add user signup with email verification and password reset tokens" @./my-app
```

Detects `intent: auth`, spawns service-author with auth-specific invariants (bcrypt cost ≥12, JWT secret from env, verification tokens 24h, reset tokens 1h), generates real password hashing + token generation + email-send background tasks. Test-author writes tests matching the auth contract. ~$0.55, ~4 minutes.

### Example 3 — Cost-gated with spec review

```bash
/one-shot "Subscription billing with plans, recurring invoices, and proration on upgrade" @./my-saas --budget=0.60 --review
```

Stage 1.5 estimates ~$0.50 (within budget). Stage 2 architect produces spec.json. Stage 2.5 shows spec to user before any expensive agents fire. On approval, stages 3-7 proceed.

---

## Framework support

| Framework | Body hints | Service-author | Migration generator | Status |
|---|---|---|---|---|
| FastAPI | 35 hints | ✅ | Alembic | mature |
| Django + DRF | 18 hints | ✅ | django runbook | mature |
| Spring Boot 3 | 16 hints | ✅ | Flyway | working |
| NestJS / Express | 14 hints | ✅ | TypeORM stubs | working |
| Go (stdlib + Chi) | 12 hints | ✅ | sqlc / migrate | working |
| Node.js | 6 hints | ✅ | Prisma stubs | basic |

**Cross-framework**: every framework gets the common tier-1 contracts (pagination, idempotency, audit logging, outbox events, soft delete, file upload, retry/CB, optimistic locking, websockets, config-from-env, feature flags, multi-tenancy, webhooks).

Each framework also ships a working **harness example** under `examples/`:
- `examples/fastapi-payment-processor-harness/` — full `.claude/` stack (router, standards, agents, hooks, settings.json)
- `examples/django-order-service-harness/`
- `examples/spring-user-service-harness/`
- `examples/nodejs-realtime-api-harness/`
- `examples/go-product-service-harness/`

Each harness CLAUDE.md leads with "Default agent behaviour" — agents are invoked automatically after every code write, scripts are the fallback.

---

## Operations commands (post-generation)

| Command | What it does |
|---|---|
| `/rollback` | Restores from `.osp.bak` files written before any `--apply` mutation |
| `/dream` | Mines `.beads/failures.jsonl` for recurring patterns, updates curriculum advice |
| `/learnings` | Surfaces agent success rates, drift detection |
| `/docs-drift` | Detects when generated code's docstrings no longer match the spec |
| `/prune` | Finds zombie code (unreferenced after recent deletes) |
| `/ship-check` | Runs the 10-gate production-readiness check on demand |
| `/perf-audit` | OpenTelemetry trace analysis + N+1 detection |
| `/curate` | External agent/skill/MCP discovery via WebSearch |
| `/adr` | Architectural Decision Record writer (standalone) |
| `/dashboard` | Trend analysis + drift detection over rolling window |
| `/interview` | Pre-`/one-shot` problem clarification |
| `/refine` | Sharpens a vague feature request into a one-pager |
| `/explain` | Walks through a generated file and explains design decisions |
| `/context` | Surfaces what Claude knows about the current project |

---

## Observability

- **OpenTelemetry traces** on every agent spawn via `lib/telemetry.py` (validated end-to-end against `opentelemetry-sdk 1.40.0`)
- **Per-agent cost observations** in `.beads/cost_observations.jsonl`
- **N+1 detection** via `nplus1_detector.py` (SQLAlchemyInstrumentor span counts per endpoint)
- **Critic loop driver state** in `.beads/status.jsonl` — visible history of iteration counts, route_to buckets, escalation reasons
- **Compose stack** in `docs/observability/docker-compose.yml` for local Jaeger + Prometheus

---

## Self-improvement loop

The plugin records its own failures and learns from them:

```
generation fails → bead written to .beads/failures.jsonl
                      ↓
              /dream runs offline
                      ↓
       mines patterns + correlates with retry-success
                      ↓
     writes curriculum_advice.jsonl (data-driven)
                      ↓
       Stage 0 of next run loads + applies the advice
```

Wired and tested. Currently empty — needs real runs to populate. See [`scripts/dream_consolidator.py`](skills/one-shot-generator/scripts/dream_consolidator.py).

---

## Known gaps

Honest limitations as of v1.0.0:

| Gap | Detail |
|---|---|
| **Zero external users** | Plugin has never shipped code into a project by a user who wasn't the author. All quality claims are self-validated. |
| **Agentic eval coverage** | Replay evals cover architect only (6 scenarios). Implementer, reviewer, doubter, critic, handoff have no replay tests — recording infrastructure exists but recordings haven't been accumulated. |
| **No live E2E CI by default** | `.github/workflows/e2e.yml` runs full pipeline against a fixture, but gated on `ANTHROPIC_API_KEY` secret (skips on forks). The free-tier job runs every push and validates 14 replay evals across 7 agent types + harness wiring + curriculum seed. See [docs/CI_SETUP.md](docs/CI_SETUP.md) for how to enable the live job (~$0.30 / run). |
| **Cost calibration** | `~$0.10 architect / ~$0.50 feature` estimates come from 6 real runs. Directionally right, not statistically robust. |
| **Self-learning loop** | Shipped seed (`.claude/registry/curriculum_seed.jsonl`) ships 10 distilled session bugs as baseline advice. Runtime layer (`/dream` writes to `.beads/curriculum_advice.jsonl`) needs real `/one-shot` runs to populate. |
| **Experimental commands** | 9 commands marked `status: experimental` (browser-test, strangler, tour, templates, architecture, execute-plan, generate, sys-debug, tdd) — lightly tested. `/one-shot` is the production-grade primary command. |

See [docs/scorecard-v4.md](docs/scorecard-v4.md) for full scoring across 36+ dimensions.

---

## Documentation map

| File | Purpose |
|---|---|
| **[AUDIT_ME_FIRST.md](AUDIT_ME_FIRST.md)** | Orientation for reviewers — read first |
| [README.md](README.md) | This file — overview, quickstart, status |
| [CHANGELOG.md](CHANGELOG.md) | Full version history |
| [CLAUDE.md](CLAUDE.md) | Root router for Claude Code sessions |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues + fixes |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Code style, test policy, agent policy |
| [SECURITY.md](SECURITY.md) | Vulnerability disclosure, data handling |
| [PRIVACY.md](PRIVACY.md) | Privacy guarantees, data retention |
| [SUPPORT.md](SUPPORT.md) | Support channels, maintenance |
| [DIRECTORY_SUBMISSION_FORM.md](DIRECTORY_SUBMISSION_FORM.md) | Anthropic Directory submission package |
| [ANTHROPIC_COMPLIANCE_CHECKLIST.md](ANTHROPIC_COMPLIANCE_CHECKLIST.md) | Self-audit compliance matrix |
| [MARKETPLACE_SUBMISSION.md](MARKETPLACE_SUBMISSION.md) | Marketplace submission artifact |
| [docs/cookbook.md](docs/cookbook.md) | Worked examples |
| [docs/CI_SETUP.md](docs/CI_SETUP.md) | How to enable live E2E CI (Anthropic API key setup) |
| [docs/production-deployment.md](docs/production-deployment.md) | Operational guidance |
| [docs/scorecard-v4.md](docs/scorecard-v4.md) | Honest 0–10 scoring |
| [docs/tier35-agentic.md](docs/tier35-agentic.md) | Architecture narrative |
| [docs/observability/](docs/observability/) | OTel setup, dashboards |

---

## Testing

```bash
# Full suite (~3 minutes, no API key needed)
python -m pytest tests/ -q --ignore=tests/integration

# Skill-wiring tests (verify the mattpocock claims are real)
python -m pytest tests/test_mattpocock_skill_wiring.py -v

# Smoke test
bash .claude/scripts/smoke-test.sh

# Compliance audit (self-audit, not Anthropic-reviewed)
python skills/one-shot-generator/scripts/compliance_audit.py

# Replay evals (architect-only, no API key)
python tests/evals/agentic_evals.py --mode replay
```

---

## Anthropic Software Directory — compliance

Self-audited against the directory policy via `compliance_audit.py`.
Current state: **15 PASS · 0 WARN · 0 FAIL — OUR_CHECKLIST_GREEN** (self-audit only, not reviewed by Anthropic).

| Requirement (per directory policy) | How we satisfy it |
|---|---|
| Privacy disclosure | [PRIVACY.md](PRIVACY.md) — data-handling policy |
| Support channels + verified contact | [SUPPORT.md](SUPPORT.md) |
| Product documentation | This README + [docs/cookbook.md](docs/cookbook.md) + [docs/production-deployment.md](docs/production-deployment.md) |
| Troubleshooting guidance | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| No unauthorised Anthropic endorsement claim | `compliance_audit.py` greps all `.md` for forbidden phrasing |

Run the audit yourself: `python skills/one-shot-generator/scripts/compliance_audit.py`

---

## Security

See [SECURITY.md](SECURITY.md). Report security issues to: musman.mughal@taleemabad.com.

---

## Community + contribution

- **Issues**: https://github.com/usmanmughaltaleemabad/One-Shot-Plugin/issues
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md) for code style, tests, and PR checklist
- **Code of conduct**: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — Contributor Covenant 2.1

---

## License

MIT. See [LICENSE](LICENSE).

---

## Versions + cumulative history

**Current: v1.0.0** (2026-05-19) — first public release, label reset from internal v4.15.

Full release history (internal v0.x → v4.15 milestones included): see [CHANGELOG.md](CHANGELOG.md).

**Try it risk-free.** Launch the [Codespaces sandbox](.devcontainer/README.md) for a one-click demo against a broken FastAPI app — no local install required, GitHub's free tier covers it.

— Usman Mughal (musman.mughal@taleemabad.com)
