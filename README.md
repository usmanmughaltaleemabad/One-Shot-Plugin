# ONE SHOT PLUGIN (Claude Code Studio)

**Production agentic one-shot code generation for existing codebases.**

Type `/one-shot "shopping cart with line items and discounts" @./my-project` and Claude conducts a 9-stage pipeline through 10 specialist agents — architect → service-author → implementer×N + test-author (parallel) → reviewer → wirer → migration → critic — to ship verified, FK-aware, migration-emitting, cost-gated code into your project.

Multi-entity, relationship-aware. Real Alembic migrations. Real OpenAPI 3.1 docs. Real bcrypt + JWT auth helpers. Real service layer enforcing business invariants. Cost-tiered model routing (Haiku for file-writers, Sonnet for reasoners) keeps a typical generation at ~$0.50. Free `--templated` fallback for CI / cost-sensitive contexts.

## ⭐ v4.1.0 — Status

| Metric | Value |
|---|---|
| **Tests** | 143 / 143 green (11 suites, Py 3.14 / Windows) |
| **Agentic eval recordings** | 6 / 6 ≥ 0.93 (architect-* scenarios) |
| **Cost calibration anchor** | 6 real architect runs, mean 26,621 tokens / 60.4s / ~$0.10 |
| **Real OpenTelemetry** | validated end-to-end against opentelemetry-sdk 1.40.0 |
| **Scorecard average** | 8.3 / 10 (see [docs/scorecard-v4.md](docs/scorecard-v4.md)) |
| **Anthropic Directory** | submission form complete (see [DIRECTORY_SUBMISSION_FORM.md](DIRECTORY_SUBMISSION_FORM.md)) |
| **Looking for** | first 10 production testers — [launch announcement](docs/launch/discord-announcement.md) |

---

## 🚀 30-second start

```bash
# 1. Clone + install
git clone https://github.com/usmanmughaltaleemabad/One-Shot-Plugin
claude --plugin-dir ./One-Shot-Plugin/one-shot-prompting

# 2. Generate a feature (dry-run wire)
/one-shot "shopping cart with line items and discounts" @./your-fastapi-project

# 3. Review the spec + diff, then ship
/one-shot "..." @./your-project --apply
```

That's it. Claude takes over from here — scans your project, designs the spec, spawns the agents in parallel, runs tests, wires the routers, and writes the migration.

---

## What `/one-shot` actually does

Each invocation runs **9 stages** orchestrated by Claude:

```
Stage 0   curriculum + predictive failure scan        (free)
Stage 0.5 external agent discovery (registry)         (free)
Stage 1   scan codebase + extract domain model        (free)
Stage 1.5 cost-budget gate (halts if over --budget)   (free)
Stage 2   architect agent → spec.json                 ~$0.10
Stage 2.5 spec review (--review flag)                 (free, gates user approval)
Stage 2.7 service-author (when invariants exist)      ~$0.08
Stage 3   implementer × N + test-author (parallel)    ~$0.20
Stage 4   verify + auto-patch (4 deterministic rules) (free)
Stage 5   reviewer agent                              ~$0.09
Stage 6   wirer (mutates main.py with .osp.bak)       (free)
Stage 6.5 migration_generator (real Alembic revision) (free)
Stage 7   critic agent (runs pytest, ship-or-loop)    ~$0.03
Stage 8   record (graph refresh + beads on failure)   (free)
```

**Total: ~$0.30–0.80 per generation.** Free with `--templated`.

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
```

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

| Framework | Agentic body templates | Templated fallback | Scaffold paths |
|---|---|---|---|
| **FastAPI** | ✅ full (service_layer + auth + events + exceptions) | ✅ | ✅ |
| Django | ⚠️ partial (paths ready, body hints queued) | ✅ | ✅ |
| Spring Boot | ⚠️ partial | ✅ | ✅ |
| Go | ⚠️ partial | ✅ | ✅ |
| Node.js | ⚠️ partial | ✅ | ✅ |
| NestJS | ⚠️ partial | ✅ | ✅ |

Cross-language body hints are queued in [docs/path-to-10.md](docs/path-to-10.md) § Tier B.

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

## What the plugin does NOT do

Being honest about gaps:

- **Zero production users yet** — architecture is sound, 143 tests pass, but real-world validation is the unproven dimension. Looking for first 10 testers.
- **Live Task agents from subprocess** — the agentic pipeline requires a Claude Code session (the CLI cannot spawn `Task` tool calls). Headless / CI use goes through `--templated`.
- **Multi-iteration critic loop in production** — protocol documented in Stage 7 of SKILL.md, battle-tested via synthetic scenarios, untested at scale.
- **Cross-language agentic body emission** — FastAPI body templates are mature; Django / Spring / Go / NestJS use templated bodies.
- **Anthropic Directory listing** — submission form ready ([DIRECTORY_SUBMISSION_FORM.md](DIRECTORY_SUBMISSION_FORM.md)); review pending.
- **Community presence** — launch announcement ready ([docs/launch/](docs/launch/)); zero current users; first issue / first PR / first registry proposal all welcomed.

See [docs/scorecard-v4.md](docs/scorecard-v4.md) for the honest 0–10 across all 36 dimensions; [docs/path-to-10.md](docs/path-to-10.md) for the concrete roadmap to 10/10 per dimension.

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

### Anthropic Software Directory

This plugin is submitted for inclusion in the Anthropic Software Directory under the [Anthropic Software Directory Policy](https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms).

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

**Current: v4.1.0** (2026-05-18)

| Release | What |
|---|---|
| **v4.1** | Empirical calibration + community launch (4 architect runs, real OTel, directory form, community infra) |
| v4.0 | Production polish — OpenAPI gen, rate-limit + cache hints, deployment guide |
| v3.5 | Agentic restructure — skills > scripts, Claude > templates, 10 specialist agents |
| v3.x | Tier 2 + 3 + 4 — closed loop, curriculum, self-extending registry |
| v2.0 | Tier-1 foundations + harness |

Full history: [CHANGELOG.md](CHANGELOG.md).

**Looking for testers.** First 10 production runs unlock the next 1.5–2.0 points across each scorecard dimension. Drop a comment on a GitHub issue, send me a project path, and I'll personally help you `/one-shot` it.

— Usman Mughal (musman.mughal@taleemabad.com)
