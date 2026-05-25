---
type: reference
last_verified: 2026-05-18
owner: claude
---

# Anthropic Software Directory Submission — Form Data

This is the **fillable form data** for the directory submission. Each
section maps to a field in Anthropic's submission portal. Copy-paste
the relevant block, attach the linked artefact.

---

## 1. Basic information

| Field | Value |
|---|---|
| **Plugin name** | ONE SHOT PLUGIN (Claude Code Studio) |
| **Slug** | one-shot-prompting |
| **Version** | 1.0.0 |
| **Author** | Usman Mughal |
| **Author email** | musman.mughal@taleemabad.com |
| **GitHub** | https://github.com/usmanmughaltaleemabad/One-Shot-Plugin |
| **License** | MIT |
| **Category** | Code Generation / Developer Tools |

## 2. Short description (≤ 200 chars)

```
Production agentic one-shot code generation for existing codebases.
21-stage pipeline, 17 specialist agents, FK-aware migrations, real
service-layer with invariants. Cost-gated. Self-extending registry.
```

## 3. Long description (Markdown supported)

```markdown
**ONE SHOT PLUGIN** turns a natural-language feature request into
production-ready code in your existing project. Claude reads
`skills/one-shot-generate/SKILL.md` and orchestrates a 15-stage pipeline
through 17 specialist agents in `.claude/agents/`:

- **architect** designs the spec (entities, relationships, invariants)
- **service-author** writes business logic (not just CRUD)
- **implementer × N** + **test-author** work in parallel
- **reviewer** gates on security / perf / style
- **wirer** integrates into your main.py
- **critic** runs pytest, decides ship-or-loop
- **extractor**, **docs-author**, **rollback** handle edge cases

The plugin emits **real Alembic migrations**, **OpenAPI 3.1 docs**,
**bcrypt + JWT auth helpers**, and a **service layer that enforces
business invariants**. Cost-tiered model routing (Haiku for
file-writers, Sonnet for reasoners) keeps a typical generation at
~$0.50.

Self-extending: a registry of external agents/skills/MCPs grows via
WebSearch through the curator skill (with explicit user approval).
Agent ratings track per-agent success rates across sessions.

Two modes: **agentic** (Claude orchestrates via SKILL.md + agent Task
spawns, ~$0.30–0.80) or **templated** (free fallback, deterministic
Python path — no Claude tokens).

Supports FastAPI, Django, Spring Boot, Go, Node.js, NestJS.
```

## 4. Three working example prompts (required)

### Example 1 — Multi-entity CRUD with relationships

```bash
/one-shot "Build a shopping cart with line items and discounts" @./my-fastapi-shop
```

**What the plugin does**: extracts 3 entities + 2 has_many relationships,
spawns architect (~$0.10) → produces spec.json, spawns 3 implementer
agents in parallel + test-author, generates `shopping_cart/`,
`line_item/` (with `shopping_cart_id` FK), `discount/` directories
plus an Alembic revision. Wirer attaches the 3 routers to `main.py`.

**Expected output**: 17 files, 1 migration, ~$0.45 total cost,
~3.5 minutes wall-time.

### Example 2 — Auth flow with email verification

```bash
/one-shot "Add user signup with email verification and password reset tokens" @./my-app
```

**What the plugin does**: detects `intent: auth`, spawns
service-author with auth-specific invariants (bcrypt cost ≥12, JWT
secret from env, verification tokens 24h, reset tokens 1h), generates
real password hashing + token generation + email-send background
tasks. Test-author writes tests that match the auth contract.

**Expected output**: 19 files including `auth/service.py`,
`common/events.py`, real JWT helpers, ~$0.55, ~4 minutes.

### Example 3 — Cost-gated multi-entity feature

```bash
/one-shot "Subscription billing with plans, recurring invoices, and proration on upgrade" @./my-saas --budget=0.60 --review
```

**What the plugin does**:
1. Stage 1.5 cost-budget gate: estimates total at ~$0.50 (within budget)
2. Stage 2 architect produces spec.json
3. **Stage 2.5 spec review**: presents spec to user before any
   expensive agents fire. User approves.
4. Stages 3-7 proceed normally.

**Expected output**: 4 entities (User, Plan, Subscription, Invoice),
4 events emitted on state transitions, full Alembic migration.

## 5. Demo recording script

A 90-second screencast script is at `docs/cookbook.md`. Three
worked examples with stage-by-stage trace output. Suitable for
embedding into the directory listing as a video.

## 6. Test evidence

| Metric | Value | Source |
|---|---|---|
| Total invocation tests | 515 / 515 green | `pytest tests/` |
| Cross-OS CI configured | Ubuntu × macOS × Windows × Py 3.10–3.12 | `.github/workflows/cross-os.yml` |
| Live + dry E2E CI | `e2e-dry` runs always; `e2e-live` requires `ANTHROPIC_API_KEY` | `.github/workflows/e2e.yml`, `docs/CI_SETUP.md` |
| Deterministic evals | 3 / 3 at 1.00 | `tests/evals/eval_runner.py` |
| Agentic replay evals | 14 / 14 across 7 agent types | `tests/evals/agentic_evals.py` |
| Skill-wiring tests | 17 / 17 enforce mattpocock integration | `tests/test_mattpocock_skill_wiring.py` |
| Curriculum seed | 10 distilled bugs ship with plugin | `.claude/registry/curriculum_seed.jsonl` |
| pass^k deterministic | 1.0 (zero variance) | `tests/evals/pass_k_runner.py` |
| Smoke tests | 8 / 8 | `.claude/scripts/smoke-test.sh` |
| Architect agent dry-runs | 6 logged | `.beads/cost_observations.jsonl` |
| Bandit SAST | optional gate available | `sast_runner.py` |

## 7. Compliance + safety

- ✅ MIT license
- ✅ SECURITY.md with disclosure process
- ✅ PRIVACY.md (data-handling policy)
- ✅ SUPPORT.md (channels + maintenance schedule)
- ✅ No external API calls in deterministic path
- ✅ All MCP integrations opt-in (curator never auto-installs)
- ✅ `.osp.bak` backups before any file mutation
- ✅ Cost-budget gate prevents runaway agentic spend
- ✅ Autonomy-level taxonomy from operator to observer
- ✅ Auto-rollback agent for failed generations

See `ANTHROPIC_COMPLIANCE_CHECKLIST.md` for the full compliance matrix.

## 8. Known limitations (honest)

- **Zero production users** — architecture is sound; community
  adoption is the unproven dimension
- **Agentic body generators are FastAPI-first** — Django/Spring/Go/
  NestJS scaffold paths exist but body hints are most mature for
  FastAPI
- **Live OTel collector deployment unverified** — local Jaeger
  compose works, production collector setup is user-side
- **Cost calibration based on 6 architect runs** — needs more
  empirical data across implementer + reviewer + critic stages

## 9. Roadmap (next 90 days)

1. **First 10 external users** — invite via Discord launch post
   (template in `docs/launch/`)
2. **Cross-language body generators reach parity** — Django + Spring
   first (most common after FastAPI)
3. **Real OTLP collector dashboards** — published Honeycomb / Grafana
   templates
4. **Eval pass^k on agentic runs** — needs 20+ live runs per scenario
5. **Marketplace listing → verified badge** — post-review milestone

## 10. Submission contact

- **Author**: Usman Mughal (musman.mughal@taleemabad.com)
- **GitHub**: https://github.com/usmanmughaltaleemabad/One-Shot-Plugin
- **Documentation**: https://github.com/usmanmughaltaleemabad/One-Shot-Plugin/blob/master/README.md

For technical questions during review, the maintainer commits to
< 48-hour response time on GitHub issues during the review window.

---

**Submission readiness**: ✅ all required fields complete.
**Submission portal**: https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy
