## Stage 0 — Curriculum lookup (cheap, do this first)

Before any work, check whether this task has failed before:

```!
python "../one-shot-generator/scripts/beads_curriculum.py" "$ARGUMENTS" --json
```

If the curriculum returns hits with similarity ≥ 0.4, surface them to the
user inline ("**Heads up**: this looks like task X from <date> that failed
because Y. Here's the advice that came out of it: Z."). Then continue —
the curriculum hits *inform* the architect agent, they don't block.

---

## Stage 0.5 — External resource discovery (Tier 4)

Before committing to the local agent lineup, see whether any external
agents / skills / MCP servers in the registry would do better on this
task:

```!
python "../one-shot-generator/scripts/agent_discovery.py" "$ARGUMENTS" --json
```

The output includes a `recommendations` array. Two kinds matter:

  - **`route-override`**: the registry marks an external agent as
    `preferred_over_local: <local-name>`. When the route fires for that
    `<local-name>` later in the pipeline, **substitute** the external
    agent. Tell the user "I'm using <external> instead of <local> for
    this task because the registry says it fits better."

  - **`consider-using`**: an external resource has a strong score but
    doesn't replace a local agent. Surface it to the user as "you might
    also want to invoke X for this — say yes/skip." Default is skip so
    the pipeline doesn't fan out unnecessarily.

If discovery finds NO matches above threshold, log a curator suggestion:
"no strong match for this task in the registry — consider running
`/curate <task>` to find external agents that could help." Continue with
the local pipeline.

If discovery raises an exception (registry malformed, etc.), skip this
stage and proceed without it. Discovery is an enrichment, not a
blocker.

---

## Stage 0.7 — Legacy-safe gate (only if `--legacy-safe` was passed)

For massive / critical / legacy codebases, the default 17-files-and-a-migration
behaviour is too dangerous. `--legacy-safe` mode enforces a small blast
radius. **Run the guard FIRST**, before any agent fires:

```!
python "../one-shot-generator/scripts/legacy_guard.py" validate \
    --project <project-path> \
    --planned-files <list of files spec will touch> \
    --extra-flags=<comma-separated other flags, e.g. --apply,--review>
```

The guard enforces:

| Rule | Effect when violated |
|---|---|
| **Max 3 files generated per run** (vs 17+ in default mode) | BLOCK |
| `--apply` / `--no-doubt` / `--no-ship-check` forbidden | BLOCK |
| `--review` flag required (spec must be approved before code gen) | BLOCK |
| Git working tree must be clean at start (so `git diff` reads cleanly post-run) | BLOCK |
| `impact_analyzer.py` heat verdict ≠ `DO_NOT_TOUCH` for every target | BLOCK |
| `impact_analyzer.py` heat verdict ≠ `HOT` for every target | BLOCK (human review required) |

If the guard returns `verdict: BLOCKED`, **abort the run** and surface
the violations to the user. Do NOT proceed past Stage 0.7.

If `ALLOWED`, set internal flags:
- `apply_disabled = True` (Stage 6 wirer dry-run only)
- `migration_auto_apply = False` (Stage 6.5 emits `MIGRATION_RUNBOOK.md`, never runs `alembic upgrade`)
- `commit_per_file = True` (Stage 6 stages each generated file as a separate `git commit` for easier review)
- `consistency_strict = True` (Stage 5.7 runs with `--strict`)
- `security_strict = True` (Stage 5.7 security scan runs with `--strict`)

The remaining stages run as normal but inherit these flags.

**This stage exists because of Gemini's review of v4.10**: auto-generating
17 files + running migrations on a critical app is a massive risk
without community battle-testing. Until that battle-testing exists,
`--legacy-safe` is the answer for "I want the benefits of /one-shot
but I can't afford runaway behaviour on a critical codebase."

---

## Stage 1 — Deterministic scan + extraction

Run the scanner and the domain extractor. Both are pure-Python and produce
JSON. Capture their outputs:

```!
python "../one-shot-generator/scripts/extract_domain_model.py" "$ARGUMENTS" --json > /tmp/osp-domain.json && \
python "../one-shot-generator/scripts/codebase_graph.py" "$ARGUMENTS" --summary
```

Read `/tmp/osp-domain.json`. Note:
- `confidence` — if below 0.55 AND the user did not pass `--force`, ask
  exactly **one** clarifying question naming the extracted primary entity,
  then stop. Wait for their answer before continuing.
- `entities` + `relationships` — these feed the architect agent.

For the codebase graph, the `--summary` output shows existing entities and
imports. Hold both outputs in working memory; you'll pass them to the
architect.

---

## Stage 1.5 — Cost budget gate

If the user passed `--budget=USD`, generate a tentative `plan.json` and
check the cost estimate before spawning any agents:

```!
python "../one-shot-generator/scripts/compile_spec.py" --orchestrator-json /tmp/osp-orch.json --out /tmp/osp-spec.json && \
python "../one-shot-generator/scripts/scaffold_planner.py" --spec /tmp/osp-spec.json --out /tmp/osp-plan.json && \
python "../one-shot-generator/scripts/cost_budget.py" --plan /tmp/osp-plan.json --budget <USD> --json
```

If `within_budget` is `false`, **halt**. Present the estimate to the user
and ask whether to proceed anyway, raise the budget, or fall back to
`--templated`. Do not spawn agents on an over-budget run.

If no `--budget` flag was passed, continue without the gate.

---

## Stage 1.7 — Apply route-overrides from Stage 0.5 discovery

If Stage 0.5 surfaced any `route-override` recommendations, **record
which local agents get replaced for the rest of this run**. Concretely:

If discovery returned:
```json
{"type": "route-override", "external": "claude-code/pr-test-analyzer",
 "replaces_local": "critic", "reason": "..."}
```

…then at Stage 7 (Critic), instead of spawning the local `critic`
agent, spawn `subagent_type: "pr-review-toolkit:pr-test-analyzer"`
with an equivalent prompt. Tell the user inline:

> "Routing the critic stage to `pr-review-toolkit:pr-test-analyzer`
> because the registry marks it as a better fit for PR-style test
> coverage review on this task."

The route-override is **transient** — it only applies to this single
`/one-shot` invocation. To make it permanent, the user can manually
edit `.claude/registry/agents.json` to set the override.

If multiple overrides target the same local agent, prefer the one with
the highest discovery score.

---

## Stage 1.8 — Source-driven doc lookup (BEFORE architect)

> **Order matters.** This stage runs BEFORE the architect (Stage 2),
> not after. The architect needs the current framework's API
> conventions while designing the spec — not after. Otherwise the
> spec may bake in deprecated patterns (pre-0.95 FastAPI Depends,
> legacy SQLAlchemy Column, Spring Boot 2 javax.* package names) that
> the implementer then faithfully replicates.

Implementer + architect emit code from training data + body_hints. For
post-cutoff API drift (Pydantic v2 quirks, FastAPI 0.110+ Annotated
deps, Spring Boot 3 javax→jakarta rename, TypeORM 0.3 DataSource,
GORM v2 Session API, …) training data can be wrong. This stage
verifies against current official docs.

```!
python "../one-shot-generator/scripts/source_docs_fetcher.py" --project <project-path> > /tmp/osp-doc-plan.json
```

The script detects the framework + exact pinned version from the
project's manifest (requirements.txt / pom.xml / package.json / go.mod)
and emits a doc-lookup plan — one entry per topic the architect + each
implementer needs to verify, with the official-doc URL + anchor keywords.

For each entry in `lookups[]`, call WebFetch:

```text
WebFetch({
  url: <entry.url>,
  prompt: "Extract idiomatic example signatures involving:
           <comma-separated entry.anchor_keywords>.
           Return code examples only, under 40 lines total."
})
```

Bundle the responses into a `source_excerpts` field on **BOTH the
architect's prompt (Stage 2) AND each implementer's prompt (Stage 3)**.
They treat the excerpts as canonical truth, overriding anything in
body_hints that conflicts.

**Skip conditions**: `skip_reason: no_manifest_found` (greenfield project),
`framework_not_recognised`, or `version_pin_missing` (best-effort, no
version-gated lookups available). On skip, log a warning and proceed —
training data is the fallback.

Why this matters: lookups are cheap (~$0.005 each via WebFetch) and
catch a bug class our reviewer + critic can't catch (API drift inside
syntactically-correct code). Caught EARLY (before spec design), they
prevent the spec from baking in deprecated patterns.

---

## Stage 2 — Architect agent

Spawn the architect agent via Task. Give it:
- The user's task (verbatim)
- The domain model JSON from Stage 1
- The codebase graph summary from Stage 1
- The curriculum hits from Stage 0 (if any)
- **The source_excerpts from Stage 1.8** (canonical framework patterns)

```text
Agent({
  description: "Architect: design spec.json for this feature",
  subagent_type: "general-purpose",
  prompt: """
    Read .claude/agents/architect.md for your full instructions.

    Task: <verbatim user task>

    Domain model (from extract_domain_model.py):
    <paste /tmp/osp-domain.json contents>

    Existing codebase (from codebase_graph.py --summary):
    <paste summary>

    Past failures matching this task (from beads_curriculum):
    <paste curriculum hits, or 'none'>

    Official-doc excerpts at the project's pinned framework version
    (from Stage 1.8 source-driven lookup — treat as canonical, override
    any conflicting training-data instinct):
    <paste WebFetch responses, or "(none — no manifest detected)">

    Produce spec.json following the architect.md schema. Write it to
    /tmp/osp-spec.json. Append a 2-3 sentence summary of your decisions
    (which entities are new vs reused, which relationships, the test
    contract you chose).
  """
})
```

After the architect returns, read `/tmp/osp-spec.json` to confirm it is
valid JSON with the expected shape (`entities`, `api_surface`,
`test_contract`, `wiring`). If malformed, re-spawn architect with the
error message.

**Emit an ADR alongside spec.json** capturing the WHY (run unless the
user passed `--no-adr`). The architect's response should include 2-3
sentences of decision reasoning — feed those into `adr_writer.py`:

```!
python "../one-shot-generator/scripts/adr_writer.py" emit \
    --project <project-path> \
    --title "<short title derived from the feature request>" \
    --status accepted \
    --context "<one paragraph: what problem are we solving?>" \
    --decision "<one paragraph: what did the architect choose?>" \
    --consequences "<one paragraph from architect's reasoning>" \
    --alternatives "<bullet list of options considered, if any>"
```

The ADR lands in `<project>/docs/adr/{NNNN}-{kebab-title}.md`. Future
sessions reading the codebase will pick it up alongside spec.json so
the design constraints survive memory churn.

---

## Stage 2.3 — Source-driven doc lookup (DEPRECATED — moved to Stage 1.8)

> **As of v4.11, this stage was moved to [Stage 1.8](#stage-18--source-driven-doc-lookup-before-architect)
> so the architect benefits from the doc excerpts too** (per Gemini
> review — the architect was previously designing specs without seeing
> current API conventions, baking in deprecated patterns the implementer
> faithfully replicated). This anchor stays for backward compatibility
> with bookmarks / external references.

The source_excerpts from Stage 1.8 are bundled into BOTH the architect's
prompt (Stage 2) AND each implementer's prompt (Stage 3).

---

## Stage 2.5 — Spec review gate (only if `--review` was passed)

If the user passed `--review`, stop here and emit the spec.json
back to them in a human-readable summary:

```
SPEC REVIEW — <feature name>
─────────────────────────────────────────────────
ENTITIES TO CREATE
  • <pascal> (snake_name)
    fields: <list>
    invariants: <list>
RELATIONSHIPS
  • <from> ── <kind> ──▶ <to>
API SURFACE
  • <METHOD> <path>  ← <handler>
TEST CONTRACT
  auth: <value>     pagination: <value>     errors: <value>
WIRING
  • <target file>: <action>
COST ESTIMATE (from cost_budget.py)
  $<usd> across <n> agent invocations
─────────────────────────────────────────────────
Proceed?  [y]es / [e]dit / [a]bort
```

If the user replies:
  - **y / yes**: continue to Stage 3.
  - **e / edit** + their description of changes: re-spawn the architect
    with the original inputs PLUS their edits as additional context.
    Re-emit the spec for another review pass (max 3 review rounds).
  - **a / abort**: stop. Record a bead noting that a spec was reviewed
    and rejected pre-implementation so the curriculum can warn next time.

If the user did not pass `--review`, skip this stage entirely.

---

## Stage 2.6 — Incremental slicing (only if `--incremental` was passed)

Default mode generates every entity in parallel — efficient but
all-or-nothing. `--incremental` mode trades parallelism for shippability:
entities ship one at a time in FK-dependency order, with green tests
and a git commit between each. If slice 3 fails, slices 1 + 2 are
already shipped and the user has a working partial feature.

Run the planner once on the full spec:

```!
mkdir -p /tmp/osp-slices
python "../one-shot-generator/scripts/incremental_planner.py" \
    --spec /tmp/osp-spec.json \
    --out-dir /tmp/osp-slices
```

The planner topologically sorts entities by FK dependencies (parents
before children) and writes one mini-spec per slice. If an FK cycle is
detected, exit code 2 — surface this to the user with the cycle members
listed; the user must redesign the relationships before --incremental
can work.

For each slice in `slices[]` (in order):

```text
For slice N of M (entity = <Pascal>, snake = <snake>):
  1. Set /tmp/osp-spec.json = slices[N].sliced_spec_path
  2. Re-run Stages 2.3 (source docs) through 7 (critic) on this slice only.
     Skip Stage 2.7 if this entity has no invariants.
  3. Stage 5.5 doubt-driven runs as usual (DEFAULT ON).
  4. Stage 6 wirer runs with --apply IF the parent /one-shot run had --apply.
  5. Stage 6.5 emits the Alembic / Django migration for this entity only.
  6. After critic returns SHIPPED:
     - run `git add -A && git commit -m "<slices[N].commit_subject>"` inside the project
     - run a tight ship-gates sweep: pytest + no_secrets + migration_reversible
       (full /ship-check is too expensive per-slice; reserve for the FINAL slice)
  7. If critic ESCALATEs on this slice:
     - DO NOT proceed to slice N+1
     - Surface: "Slice N (<entity>) failed; slices 1..N-1 are committed
       and shippable. Sandbox: <path>."
     - The user can either fix the slice manually and `git commit --amend`,
       OR roll back this slice's changes with `git reset --hard HEAD~0`
       (the prior commit) and re-run /one-shot from this slice only.
```

After the FINAL slice ships, run `/ship-check` ONCE in full mode on the
project. That's the deploy-readiness gate that covers the whole feature.

When to use `--incremental`:
- Feature has 3+ entities AND you'd rather get partial shippable work than risk all-or-nothing
- The codebase already follows trunk-based development with small PRs
- You're nervous about a particular invariant and want to validate the foundation entity before building dependents

When NOT to use it:
- Feature has 1-2 entities — parallel is faster, same blast radius
- Entities have circular FKs (planner exits 2 — break the cycle first)
- The user is running in `--no-apply` dry-run mode — slicing buys nothing without intermediate commits

---

## Stage 2.7 — Service-author agent (when business logic exists)

If `spec.entities[*].invariants` is non-empty OR `spec.intent` is `auth`,
spawn the **service-author** agent BEFORE the implementer fan-out.
The service layer is where business logic lives — without this stage,
generated code is bare CRUD scaffolding.

```text
Agent({
  description: "Service-author: write business logic per spec invariants",
  subagent_type: "general-purpose",
  prompt: """
    Read .claude/agents/service-author.md.
    Spec.json: <paste>
    Codebase graph imports: <paste>

    Produce {entity}/service.py for every entity with action='create'.
    Also produce common/events.py + common/exceptions.py if absent.
    Enforce every invariant from spec.entities[*].invariants in the
    service layer (NOT the router, NOT the model).
  """
})
```

This stage turns scaffolding into a production feature. The implementer
in Stage 3 builds routers that DELEGATE to the service.

If `spec.entities[*].invariants` is empty AND `spec.intent` is not
`auth`, skip this stage.

---
