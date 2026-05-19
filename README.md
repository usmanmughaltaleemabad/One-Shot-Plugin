# ONE SHOT PLUGIN (Claude Code Studio)

**Production agentic one-shot code generation for existing codebases.**

Type `/one-shot "shopping cart with line items and discounts" @./my-project` and Claude conducts a 9-stage pipeline through 10 specialist agents — architect → service-author → implementer×N + test-author (parallel) → reviewer → wirer → migration → critic — to ship verified, FK-aware, migration-emitting, cost-gated code into your project.

Multi-entity, relationship-aware. Real Alembic migrations. Real OpenAPI 3.1 docs. Real bcrypt + JWT auth helpers. Real service layer enforcing business invariants. Cost-tiered model routing (Haiku for file-writers, Sonnet for reasoners) keeps a typical generation at ~$0.50. Free `--templated` fallback for CI / cost-sensitive contexts.

## ⭐ v4.14 — Status

| Metric | Value |
|---|---|
| **Tests** | 466 / 466 green (31 suites incl. integration harness, Py 3.14 / Windows) |
| **Agentic eval recordings** | 6 / 6 ≥ 0.93 (architect-* scenarios) |
| **Cost calibration anchor** | 6 real architect runs, mean 26,621 tokens / 60.4s / ~$0.10 |
| **Real OpenTelemetry** | validated end-to-end against opentelemetry-sdk 1.40.0 |
| **Scorecard average** | 8.3 / 10 (see [docs/scorecard-v4.md](docs/scorecard-v4.md)) |
| **Anthropic Directory** | submission prepared, not yet submitted (see [DIRECTORY_SUBMISSION_FORM.md](DIRECTORY_SUBMISSION_FORM.md)) |
| **Try it risk-free** | [GitHub Codespaces sandbox](.devcontainer/README.md) — one-click demo, free tier |
| **Directory compliance (self-audit)** | 15/15 PASS · 0 WARN · 0 FAIL ([`compliance_audit.py`](skills/one-shot-generator/scripts/compliance_audit.py)) — not reviewed by Anthropic |

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
│ architect → spec │ (all parallel)   │ doubter agent    │ Alembic migration│
│ source-doc fetch │                  │ (fresh-context)  │ critic runs tests│
│ ADR emission     │                  │                  │ record learnings │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┘
     ~$0.10              ~$0.20            ~$0.10            ~$0.05
```

**Total: ~$0.30–0.80 per multi-entity feature.** Free with `--templated`.

### Under the hood — 12 stages (only if you care)

<details>
<summary>Click to expand the full stage breakdown</summary>

```
PLAN
  Stage 0    curriculum + predictive failure scan      (free)
  Stage 0.5  external-agent registry discovery         (free)
  Stage 1    scan codebase + extract domain model      (free)
  Stage 1.5  cost-budget gate (halts if over --budget) (free)
  Stage 2    architect agent → spec.json + ADR         ~$0.10
  Stage 2.3  source-driven doc lookup (WebFetch official docs)
  Stage 2.5  spec review (--review flag)
  Stage 2.6  incremental slicing (--incremental flag)
  Stage 2.7  service-author (when invariants exist)    ~$0.08

BUILD
  Stage 3    implementer × N + test-author (parallel)  ~$0.20

VERIFY
  Stage 4    verify + auto-patch                       (free)
  Stage 5    reviewer agent                            ~$0.09
  Stage 5.5  doubt-driven adversarial pass (DEFAULT ON; --no-doubt)

SHIP
  Stage 6    ship-gates → wirer + 6.5 migration_generator
  Stage 7    critic (runs pytest; deterministic multi-iter loop, max 3)
  Stage 8    record (graph refresh + per-agent learnings)
```

Stages 5.5, 6, and 2 (ADR emission) are **default-on** — opt out with
`--no-doubt`, `--no-ship-check`, `--no-adr`.

</details>

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

### Five flags worth knowing

```bash
/one-shot "<feature>" @./project              # dry-run wire (default)
/one-shot "..." @./project --apply            # mutate main.py + run migrations
/one-shot "..." @./project --budget=0.30      # halt if estimated cost > $0.30
/one-shot "..." @./project --review           # gate on spec.json before agents fire
/one-shot "..." @./project --force            # bypass low-confidence clarification gate
/one-shot "..." @./project --templated        # zero-token fallback (free, lower quality)
/one-shot "..." @./project --incremental      # ship one entity per slice with green tests + git commit between
```

### `--incremental` mode (v4.8)

Default mode generates every entity in parallel — efficient when nothing
fails, all-or-nothing when something does. `--incremental` trades the
parallelism for **shippability**: entities ship one at a time in
FK-dependency order, with green tests and a git commit between each.

For `"shopping cart with line items and discounts"`:

```
Slice 1/3: ShoppingCart  → 5 files → tests green → git commit ✓
Slice 2/3: Discount      → 5 files → tests green → git commit ✓
Slice 3/3: LineItem      → 5 files → tests green → git commit ✓
```

If slice 3 fails, slices 1 + 2 are already committed and shippable.
`incremental_planner.py` topologically sorts entities by FK dependencies
(Kahn's algorithm, alphabetical tie-break for stability) and emits one
mini-spec per slice. **FK cycles abort with exit 2** — surface the
cycle members to the user; the relationships must be redesigned before
`--incremental` can work.

When to use: 3+ entities, you'd rather have partial shippable work than
risk all-or-nothing, codebase follows trunk-based development.

When NOT to use: 1-2 entities (parallel is faster, same blast radius),
circular FKs, dry-run mode (no commits = no value).

---

## 🏗️ Architecture

A proper Claude Code plugin — **skills + commands + agents as first-class units**; scripts as deterministic helpers the agents call.

```
commands/                            ← 20 slash commands
  one-shot.md                          ⭐ /one-shot — primary agentic
  rollback.md, docs-drift.md           rollback, doc drift detection
  autonomy.md, curate.md               autonomy levels, external curation
  (14 legacy commands)                 generate, plan, tdd, debug, ...

skills/                              ← Claude reads SKILL.md and acts
  one-shot-generate/SKILL.md           ⭐ 9-stage agentic playbook
  one-shot-generator/SKILL.md          legacy templated fallback
  curator/SKILL.md                     external-agent discovery via WebSearch
  write-plan, execute-plan, tdd-cycle, systematic-debug, verify-before-complete

.claude/agents/                      ← 10 specialists invocable via Task
  architect       (sonnet) — designs spec.json
  service-author  (sonnet) — business logic, invariants, transactions, events
  implementer     (haiku)  — writes ONE file per spawn (cost-optimised)
  test-author     (sonnet) — independent of implementer (defends contract)
  reviewer        (sonnet) — security / perf / style gate
  wirer           (haiku)  — integrates into main.py + .osp.bak safety
  critic          (sonnet) — runs pytest, decides ship-or-loop
  extractor       (sonnet) — fallback for ambiguous prose (confidence < 0.55)
  docs-author     (haiku)  — proposes doc updates on entity drift
  rollback        (haiku)  — undoes failed --apply, git-stash safety

.claude/registry/                    ← Self-extending capability marketplace
  agents.json    (8 known good external agents incl. pr-review-toolkit, Plan, Explore)
  skills.json    (1 entry, growing via curator)
  mcp_servers.json (4 entries: chrome-devtools, gmail, supabase, vercel)
  learnings.jsonl  (per-agent success-rate tracking)

skills/one-shot-generator/scripts/   ← 25+ deterministic tools
  Pipeline:     extract_domain_model, codebase_graph, codebase_diff,
                generate_and_verify, auto_patch, auto_wirer,
                critic_runner, live_critic, scaffold_planner, body_hints
  Generation:   migration_generator, openapi_doc_generator, spec_driven_generator
  Learning:     beads_writer, beads_curriculum, predictive_failure,
                self_improvement_proposer, auto_rule_extractor, promote_rule,
                learnings_hub
  Operations:   cost_budget, sast_runner, perf_profiler, autonomy_level,
                prompt_versioner, agentic_session_driver, agent_discovery
```

**Tier docs** for the full architectural narrative:
- [docs/tier35-agentic.md](docs/tier35-agentic.md) — the agentic restructure
- [docs/tier4-self-extending.md](docs/tier4-self-extending.md) — registry + curator
- [docs/tier5-observability.md](docs/tier5-observability.md) — eval harness + OTel
- [docs/path-to-10.md](docs/path-to-10.md) — concrete roadmap to 10/10 per dimension

---

## Three worked examples

### Example 1 — Multi-entity feature

```bash
/one-shot "Build a shopping cart with line items and discounts" @./my-fastapi-shop
```

Extracts 3 entities + 2 `has_many` relationships. Architect produces spec.json with `total = sum(line_items × quantity) - sum(discounts)` invariant. Service-author writes the business logic. Implementer×3 + test-author run in parallel. Wirer attaches 3 routers + emits Alembic revision.

**Output**: 17 files, 1 migration, ~$0.45, ~3.5 minutes.

### Example 2 — Auth flow

```bash
/one-shot "Add user signup with email verification and password reset tokens" @./my-app
```

Detects `intent: auth` → service-author writes bcrypt + JWT helpers. Test-author asserts 401 because `test_contract.auth='jwt'`. Background-task hint generates verification-email scheduling.

**Output**: 19 files (User + EmailVerification + PasswordResetToken + auth/service.py + common/events.py), real JWT helpers, 24h verification TTL + 1h reset TTL invariants.

### Example 3 — Cost-gated with spec review

```bash
/one-shot "Subscription billing with plans, invoices, and proration on upgrade" @./my-saas --budget=0.60 --review
```

1. Stage 1.5: cost-budget gate estimates ~$0.50 (within budget) ✓
2. Stage 2: architect produces spec.json
3. Stage 2.5: **stops, shows you the spec** before any expensive agent fires
4. You approve → stages 3-7 proceed
5. 4 entities, 4 events (`subscription.created`, `plan_changed`, `invoice.generated`, `cancelled`), full migration

See [docs/cookbook.md](docs/cookbook.md) for full traces with stage-by-stage output.

---

## Framework support

As of **v4.3**, all six frameworks have full parity — each ships the same
8-hint shape (init/model/schema/service/router/auth/background/test) plus
framework-specific extras AND the Tier-1 production-concerns set
(soft delete + file upload, plus 9 cross-framework contracts: pagination,
idempotency keys, audit log, email templates, outbox pattern, health checks,
RBAC, API versioning, data migrations).

Total catalogue: **101 hints** (10 × FastAPI, 13 × Django, 10 × Spring,
10 × NestJS, 10 × Go, 10 × Node.js, 38 × common).

**v4.7 — integration tightening + remaining Osmani absorptions**:

- **`/adr`** — standalone slash command for ADR creation outside `/one-shot`
- **`/dashboard`** — trend analysis + drift detection over a rolling window (flags `degrading` agents when recent success rate drops > 15 points vs prior window). Backed by new `learnings_hub.py dashboard` subcommand.
- **Stage 2.3 + 5.5 + ship-check + ADR emission now DEFAULT ON in `/one-shot`** — no longer opt-in. Doc lookup runs every architect, doubter runs after every reviewer, ADR lands alongside spec.json, ship-gates run before any `--apply`. Opt-out via `--no-doubt`, `--no-adr`, `--no-ship-check`.
- **4 new cross-cutting hints**: `performance_optimization`, `error_recovery`, `debugging_strategy`, `git_workflow` (absorbed from Osmani's debugging-and-error-recovery + performance-optimization + git-workflow-and-versioning skills).

**v4.6 — absorbed from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills)**:

- **Stage 2.3 (source-driven)** — [source_docs_fetcher.py](skills/one-shot-generator/scripts/source_docs_fetcher.py) detects the project's pinned framework version (FastAPI / Django / Spring / NestJS / Go / Node) and emits a doc-lookup plan; the orchestrator WebFetches each official-doc URL and inlines excerpts into implementer prompts. Catches API drift bugs (Pydantic v2, Spring Boot 3 jakarta, TypeORM v0.3 DataSource) that training data misses.
- **Stage 5.5 (doubt-driven)** — fresh-context [doubter agent](.claude/agents/doubter.md) reviews each artifact with ONLY the contract (no spec reasoning, no implementer notes). The withholding prevents agreement bias. [doubt_driver.py](skills/one-shot-generator/scripts/doubt_driver.py) enforces max 2 rounds + theater detection.
- **`/ship-check`** — [ship_gates.py](skills/one-shot-generator/scripts/ship_gates.py) runs 10 production-readiness gates before `--apply`: tests_pass, no_secrets, no_TODO, migration_reversible, env_documented, health_endpoint, openapi_doc, feature_flag, rollback_path, canary_plan.
- **ADR emission** — [adr_writer.py](skills/one-shot-generator/scripts/adr_writer.py) writes sequentially-numbered MADR records to `docs/adr/` capturing the *why* alongside spec.json's *what*.
- **`/refine`** — pre-`/one-shot` step that produces a sharpened one-pager (Problem / Recommended direction / MVP scope / **NOT doing** / Key assumptions) from a vague feature request.
- **6 new cross-cutting contracts** under `common` — `adr_record`, `source_verification`, `ci_cd_pipeline`, `api_design`, `deprecation_policy`, `frontend_ui_concerns`.

v4.4 added 8 Tier-2 production contracts (webhooks send/receive,
multi-tenancy, feature flags, optimistic locking, retry+circuit breaker,
configuration management, websocket endpoints) PLUS a deterministic
**critic loop driver** that owns the Stage 7 hard caps (max 3 iterations,
5 min/iteration, escalate on regression).

v4.5 added 6 Tier-3 specialised contracts (GraphQL resolver, gRPC service,
saga orchestrator, dead-letter queue, GDPR export/delete, i18n) plus a
**production OpenTelemetry collector deployment guide**
([docs/observability/production-collector.md](docs/observability/production-collector.md))
and end-to-end wiring of the cross-agent learnings hub
(every `/one-shot` run now records per-agent outcomes via `run_finalize.py`;
inspect via the new `/learnings top-agents` slash command).

| Framework | Body hints | Scaffold paths | Migration tool |
|---|---|---|---|
| **FastAPI** | ✅ 10 hints (service layer + bcrypt/JWT auth + BackgroundTasks + soft_delete + file_upload) | ✅ | Alembic |
| **Django** | ✅ 13 hints (service layer + simplejwt + Celery + soft_delete + file_upload) | ✅ | `manage.py makemigrations` |
| **Spring Boot** | ✅ 10 hints (service + Spring Security/JWT + @Async/@Scheduled + @SQLDelete + MultipartFile) | ✅ | Flyway or Liquibase |
| **NestJS** | ✅ 10 hints (service + Passport+bcrypt + BullMQ + @DeleteDateColumn + FileInterceptor) | ✅ | TypeORM migration:generate |
| **Go** | ✅ 10 hints (service + DTOs + bcrypt/golang-jwt + goroutine workers + gorm.DeletedAt + r.FormFile) | ✅ | golang-migrate |
| **Node.js** | ✅ 10 hints (Express + Sequelize + Joi + bcrypt/JWT + BullMQ + Jest + paranoid + multer) | ✅ | sequelize-cli migration |

### Tier-1 production concerns (cross-framework, under `common` namespace)

Every implementer agent has access to these contracts regardless of host framework:

| Contract | What it guarantees |
|---|---|
| **pagination_contract** | Offset + keyset (cursor) strategies with `max_limit` enforcement |
| **idempotency_keys** | Stripe-style `Idempotency-Key` header replay protection (24h TTL, hash-based) |
| **audit_log** | Append-only `who/what/when/old/new` trail, redact secrets, never DELETE |
| **email_template** | Jinja2/Handlebars HTML + plain-text fallback; never SMTP in request handler |
| **outbox_pattern** | Atomic business-write + event-row in same tx; poller publishes to broker |
| **health_check_contract** | `/livez` (no deps) vs `/readyz` (DB+broker+cache) — distinct semantics |
| **rbac_contract** | Centralised role/permission guards; `'{resource}:{action}'` strings |
| **api_versioning_contract** | URL-path versioning, shared service layer, Sunset+Deprecation headers |
| **data_migration** | Reversible + batched + idempotent; separate revision from schema change |

All frameworks emit business-logic-bearing services with invariant enforcement,
real auth helpers (never plain-text passwords), retryable background-task patterns
matched to the ecosystem (Celery / @Async / BullMQ / Asynq), and the production
concerns above. Coverage verified by
[tests/test_framework_parity.py](tests/test_framework_parity.py) (22 tests) +
[tests/test_tier1_production_concerns.py](tests/test_tier1_production_concerns.py) (25 tests).

---

## Operations commands (post-generation)

```bash
/rollback                                  # undo last --apply (git stash + restore .osp.bak)
/docs-drift                                # propose README + docstring updates after entity drift
/autonomy get-level                        # current autonomy level (operator → observer)
/autonomy suggest-next                     # promotion suggestion based on session history
/curate "lighthouse audit"                 # discover new external agents/MCPs via WebSearch
```

### Autonomy scale

Five levels mapped from [Anthropic's autonomy framework](https://www.anthropic.com/news/measuring-agent-autonomy):

| Level | Gates relaxed | Recommended after |
|---|---|---|
| **operator** | nothing — every action explicit | first 5 sessions |
| **collaborator** | dry-run auto-approved | 5+ clean sessions |
| **consultant** | `--apply` auto-approved (non-migration) | 20+ clean sessions |
| **approver** | migrations auto-approved | 50+ clean sessions |
| **observer** | full autonomy (opt-in only) | explicit only |

---

## Observability

Every deterministic hot-path is `@traced` for OpenTelemetry. Spans go nowhere by default (no-op fallback). Enable with:

```bash
export OSP_OTEL_ENABLED=1
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
pip install opentelemetry-sdk

# Start a local Jaeger + Prometheus stack
docker compose -f docs/observability/docker-compose.yml up -d

# Now any /one-shot invocation emits real spans
/one-shot "<feature>" @./project
```

Open http://localhost:16686 for Jaeger UI. See [docs/observability/](docs/observability/) for the full setup.

---

## Self-improvement

The plugin learns across sessions:

- **`.beads/failures.jsonl`** — every failed generation logged with structured diagnostics
- **`predictive_failure.py`** — TF-IDF cosine over past beads surfaces similar failures BEFORE the next attempt (severity: info / warning / critical at 0.3 / 0.5 / 0.75 similarity)
- **`auto_rule_extractor.py`** — scans git history of fixes to generated files, extracts deterministic patch rules (P5/P6/...)
- **`learnings_hub.py`** — per-agent success-rate tracking with recency decay; surfaces top agents via `top-agents` subcommand
- **`self_improvement_proposer.py`** — analyses recurring failure patterns (≥3 occurrences), emits markdown proposals for SKILL.md changes

---

## Honest limitations

Two things the plugin cannot close from this seat — both wait on external signal:

- **Anthropic Directory listing** — submission form prepared ([DIRECTORY_SUBMISSION_FORM.md](DIRECTORY_SUBMISSION_FORM.md)) but not yet submitted; no Anthropic review has occurred.
- **Marketplace adoption** — [`compliance_audit.py`](skills/one-shot-generator/scripts/compliance_audit.py) is a SELF-audit reporting 15/15 PASS against the directory policy; it is not an Anthropic endorsement.

For the full 0-10 honest scoring across 36 dimensions, see [docs/scorecard-v4.md](docs/scorecard-v4.md); for the roadmap, [docs/path-to-10.md](docs/path-to-10.md).

---

## Documentation map

| Topic | File |
|---|---|
| **Quick start** | this README |
| **3 worked examples** | [docs/cookbook.md](docs/cookbook.md) |
| **Production deployment** | [docs/production-deployment.md](docs/production-deployment.md) |
| **Honest scorecard (0-10 × 36 dimensions)** | [docs/scorecard-v4.md](docs/scorecard-v4.md) |
| **Path to 10/10 per dimension** | [docs/path-to-10.md](docs/path-to-10.md) |
| **Architecture narrative** | [docs/tier35-agentic.md](docs/tier35-agentic.md) |
| **Observability setup** | [docs/observability/](docs/observability/) |
| **Marketplace submission** | [MARKETPLACE_SUBMISSION.md](MARKETPLACE_SUBMISSION.md) |
| **Anthropic Directory submission form** | [DIRECTORY_SUBMISSION_FORM.md](DIRECTORY_SUBMISSION_FORM.md) |
| **Launch materials** | [docs/launch/discord-announcement.md](docs/launch/discord-announcement.md) |
| **Validation findings (8 real bugs caught)** | [VALIDATION_REPORT.md](VALIDATION_REPORT.md) |
| **CHANGELOG** | [CHANGELOG.md](CHANGELOG.md) |
| **Implementation status** | [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) |
| **Compliance checklist** | [ANTHROPIC_COMPLIANCE_CHECKLIST.md](ANTHROPIC_COMPLIANCE_CHECKLIST.md) |
| **Per-tier reference** | docs/tier1-pipeline.md … tier5-observability.md |

---

## Testing

```bash
# Smoke
bash .claude/scripts/smoke-test.sh                   # 8/8 checks

# Full suite
python -m pytest tests/                              # 143/143

# Deterministic evals
python tests/evals/eval_runner.py                    # 3/3 at 1.00

# Agentic replay evals (no Claude tokens required)
python tests/evals/agentic_evals.py                  # 6/6 at ≥0.93

# pass^k (production-style)
python tests/evals/pass_k_runner.py --mode deterministic-replay --k 5
```

Cross-OS CI matrix ready in [.github/workflows/cross-os.yml](.github/workflows/cross-os.yml) — Ubuntu × macOS × Windows × Py 3.10/3.11/3.12.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for code style, test policy, and PR checklist. The plugin welcomes:

1. **Bug reports** with structured templates (`.github/ISSUE_TEMPLATE/bug_report.yml`)
2. **Real-world `/one-shot` recordings** to feed the agentic eval harness
3. **Cross-language body hints** in `body_hints.py`
4. **Eval fixtures** under `tests/evals/fixtures/`
5. **External agent / MCP proposals** via the `agent_registry_proposal` issue template

[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — Contributor Covenant 2.1.

---

## Security

See [SECURITY.md](SECURITY.md) for vulnerability disclosure.

Key safety properties:

- Plugin processes code **locally** — no external APIs in the deterministic path
- All MCP integrations are opt-in — curator never auto-installs
- `.osp.bak` backups before ANY file mutation; `--apply` is opt-in
- Cost-budget gate (`--budget=USD`) prevents runaway agentic spend
- `auto_patch` and `auto_rule_extractor` are **propose-only**; never auto-mutate
- Stdlib-only by default; optional dependencies have graceful no-op fallbacks

---

## Support & Maintenance

```bash
/one-shot --help                       # Built-in help + examples
/support                               # Support channels + response times
```

### Community + contribution

- **Bug reports**: Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.yml)
- **Feature requests**: [Feature request template](.github/ISSUE_TEMPLATE/feature_request.yml)
- **Agent proposals**: [Agent registry proposal template](.github/ISSUE_TEMPLATE/agent_registry_proposal.yml)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md) for code style, tests, and PR checklist
- **Code of conduct**: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — Contributor Covenant 2.1

### Anthropic Software Directory — compliance

Audited continuously against the directory policy via `compliance_audit.py`.
Current state: **15 PASS · 0 WARN · 0 FAIL → READY_FOR_DIRECTORY**.

| Requirement (per directory policy) | How we satisfy it |
|---|---|
| Privacy disclosure | [PRIVACY.md](PRIVACY.md) — data-handling policy |
| Support channels + verified contact | [SUPPORT.md](SUPPORT.md) — channels + maintenance schedule |
| Product documentation | [README.md](README.md), [docs/cookbook.md](docs/cookbook.md), [docs/production-deployment.md](docs/production-deployment.md) |
| Troubleshooting guidance | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Vulnerability disclosure | [SECURITY.md](SECURITY.md) |
| Open-source license | [LICENSE](LICENSE) (MIT) |
| Release history | [CHANGELOG.md](CHANGELOG.md) |
| ≥ 3 working example prompts | [docs/cookbook.md](docs/cookbook.md) + [DIRECTORY_SUBMISSION_FORM.md](DIRECTORY_SUBMISSION_FORM.md) |
| Testing account + sample data | [.devcontainer/](.devcontainer/) — free Codespaces sandbox |
| Graceful error handling | every script returns structured JSON skip/error on missing deps |
| Token usage proportional to task | `cost_budget.py` + `cost_calibrator.py` (self-recalibrating) |
| Tool names ≤ 64 chars | longest slash command: `check-consistency` (17 chars) |
| Tool annotations (read-only / destructive) | every command's frontmatter declares both |
| Plugin manifest fields | [plugin.json](.claude-plugin/plugin.json) — name, version, author, license, description |
| No unauthorised Anthropic endorsement claim | `compliance_audit.py` greps all `.md` for forbidden phrasing |

Run the audit yourself: `python skills/one-shot-generator/scripts/compliance_audit.py`

**Submission contact:**

| Field | Value |
|---|---|
| **Author** | Usman Mughal |
| **Email** | musman.mughal@taleemabad.com |
| **GitHub** | [usmanmughaltaleemabad/One-Shot-Plugin](https://github.com/usmanmughaltaleemabad/One-Shot-Plugin) |
| **Response commitment** | < 48 hours on GitHub issues during review |
| **Documentation** | [Complete README](README.md) + [Directory submission form](DIRECTORY_SUBMISSION_FORM.md) |

---

## License

MIT. See [LICENSE](LICENSE).

---

## Versions + cumulative history

**Current: v4.14** (2026-05-18)

| Release | What |
|---|---|
| **v4.14** | All 5 deferred items shipped: (1) **anti-rationalization gate** catches reviewer rubber-stamping (8-question matrix the agent must fill before PASS, then we verify against actual code evidence — if the agent claimed "no mock" but `Mock()` is in the code, escalate); (2) **Anthropic prompt caching anchors** on `live_api_runner` system prompts cut input-token billing by ~75% across the multi-agent run; (3) **mutation testing** in critic kills hollow test suites by applying small bugs + re-running tests; (4) **AST context pruning** (`context_pruner.py`) uses stdlib `ast` to trace import graph from entry point, shrinks monorepo scope to 5-15% of total files; (5) **OTel-based N+1 detection** asserts DB span counts per test — list endpoints with > 3 queries flagged as N+1. |
| v4.13 | Five new features closing real Day-2 maintenance + ergonomics gaps: (1) `--resume` state machine; (2) `/prune` zombie-code detector; (3) `--explain` flag; (4) cycle-breaking in `--incremental`; (5) hybrid lint runner. Plus Codespaces sandbox. |
| v4.12 | Two new safety gates closing real Gemini-flagged risks: (1) Stage 5.7 cross-agent consistency + deterministic SAST deep scan catches subtle drift the per-agent reviews miss; (2) Stage 0.7 `--legacy-safe` mode for critical codebases — caps generation at 3 files, blocks `--apply`, requires `--review`, refuses to mutate any file with `DO_NOT_TOUCH` heat verdict from the new `impact_analyzer.py`. `.archive/` now in `.gitignore`. |
| v4.11 | Three fixes from Gemini's external code review: (1) source-doc lookup moved from Stage 2.3 → Stage 1.8 so the architect designs the spec with current API conventions, not stale training data; (2) Stage 6.5 migration-ordering trade-off documented for the three sub-cases (greenfield, add NOT NULL, rename/drop); (3) new `approval_gate.py` + `--require-approval-webhook` flag close the HITL gap for autonomous CI runs. |
| v4.10 | 4 new slash commands (`/perf-audit`, `/interview`, `/browser-test`, `/context`) closing the last visible feature gaps vs [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills). README restructured into 4-phase mental model (PLAN/BUILD/VERIFY/SHIP). New `docs/standalone-usage.md` documents what runs without Claude Code. |
| v4.9 | Headless SDK mode (`agentic_session_driver --mode live-api` calls Anthropic SDK directly — no Claude Code session needed) + critic-loop stress tests + `cost_calibrator.py` (self-recalibrates `PER_AGENT_TOKEN_ESTIMATES` from `.beads/cost_observations.jsonl`). Closes three of the "honest gaps" technically. |
| v4.8 | `--incremental` slicing — ship entities one at a time with green tests + git commit between (Kahn's topo sort, FK-cycle detection) |
| v4.7 | Integration tightening — Stage 5.5 doubt, Stage 6 ship-check, Stage 2 ADR are DEFAULT ON. /adr + /dashboard slash commands. 4 hints (perf, error_recovery, debug, git_workflow). |
| v4.6 | Absorbed [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) — Stage 2.3 source-driven, Stage 5.5 doubt-driven, /ship-check, ADR writer, /refine, 6 common hints. |
| v4.5 | Tier-3 specialised hints (GraphQL, gRPC, saga, DLQ, GDPR, i18n) + production OTel guide + cross-agent learning hub wired end-to-end. |
| v4.4 | Tier-2 production concerns (webhooks, multi-tenancy, feature flags, optimistic locking, retry/CB, websockets, config) + multi-iteration critic loop driver. |
| v4.3 | Tier-1 production concerns (pagination, idempotency, audit, outbox, soft delete, file upload, ...). |
| v4.2 | Full framework parity — Django/Spring/NestJS/Go/Node.js match FastAPI's 8-hint baseline. |
| v4.1 | Empirical calibration + community launch infra. |
| v4.0 | Production polish — OpenAPI gen, rate-limit + cache hints, deployment guide. |
| v3.5 | Agentic restructure — skills > scripts, Claude > templates, 10 specialist agents. |
| v3.x | Tier 2 + 3 + 4 — closed loop, curriculum, self-extending registry. |
| v2.0 | Tier-1 foundations + harness. |

Full history: [CHANGELOG.md](CHANGELOG.md).

**Try it risk-free.** Launch the [Codespaces sandbox](.devcontainer/README.md) for a one-click demo against a broken FastAPI app — no local install required, GitHub's free tier covers it.

— Usman Mughal (musman.mughal@taleemabad.com)
