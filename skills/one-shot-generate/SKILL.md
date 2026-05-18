---
name: one-shot-generate
description: |
  End-to-end agentic one-shot. Claude conducts a pipeline of deterministic
  scripts + specialist agents to take a natural-language feature request and
  produce verified, wired code in the user's existing codebase. Trigger words:
  "one-shot", "generate feature", "build feature", "add CRUD/API/endpoints",
  "add batch job", "scaffold". Accepts an optional ``--templated`` flag that
  falls back to the legacy Python-only pipeline (no Claude tokens) for users
  who need free, deterministic generation.
argument-hint: "[task description] [@path/to/project] [--apply] [--templated] [--budget=USD]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task
---

# One-Shot Generate — Agentic Pipeline

You are conducting the one-shot generation pipeline. The user has invoked
``/one-shot "their feature description" @/path/to/project``. Your job is to
run the seven-stage pipeline, spawning specialist agents at the right
points, and ship working code into their project.

The arguments are: `$ARGUMENTS`

---

## Flag handling — DO THIS FIRST, BEFORE ANY OTHER WORK

Parse `$ARGUMENTS` and look for these flags:

- `--templated` / `--legacy` / `--free` — route to the deterministic Python
  pipeline. Do this **immediately** as the very first branch — do not run
  the scanner, do not consult curriculum, do not spawn agents. Just:

  ```!
  python "./scripts/one_shot_orchestrator.py" "$ARGUMENTS"
  ```

  Then summarise the output for the user (which files were generated,
  what's in the wire plan, any warnings). Stop. The templated path is
  the legacy `one-shot-generator` skill's behaviour wrapped in this
  command for backward compatibility — it costs zero Claude tokens but
  produces lower-quality code than the agentic path.

- `--apply` — at the wire stage (Stage 6), actually mutate the user's
  project files. Default is dry-run.

- `--budget=USD` — if the cost estimate from Stage 1.5 exceeds this,
  halt and ask the user. Default: no budget gate.

- `--force` — bypass the clarification gate even when extraction
  confidence is below 0.55.

- `--review` — after the architect produces spec.json, **STOP** and
  show the user the spec (entities, relationships, API surface, test
  contract). Ask whether to proceed, edit, or abort. Only after they
  approve do the implementer/test-author agents fire. This protects
  against committing to an expensive multi-agent run that's
  misaligned with what the user actually wanted. See Stage 2.5 below.

If none of `--templated` / `--legacy` / `--free` are present, proceed
with the agentic pipeline below.

---

## Stage 0 — Curriculum lookup (cheap, do this first)

Before any work, check whether this task has failed before:

```!
python "./scripts/beads_curriculum.py" "$ARGUMENTS" --json
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
python "./scripts/agent_discovery.py" "$ARGUMENTS" --json
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

## Stage 1 — Deterministic scan + extraction

Run the scanner and the domain extractor. Both are pure-Python and produce
JSON. Capture their outputs:

```!
python "./scripts/extract_domain_model.py" "$ARGUMENTS" --json > /tmp/osp-domain.json && \
python "./scripts/codebase_graph.py" "$ARGUMENTS" --summary
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
python "./scripts/compile_spec.py" --orchestrator-json /tmp/osp-orch.json --out /tmp/osp-spec.json && \
python "./scripts/scaffold_planner.py" --spec /tmp/osp-spec.json --out /tmp/osp-plan.json && \
python "./scripts/cost_budget.py" --plan /tmp/osp-plan.json --budget <USD> --json
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

## Stage 2 — Architect agent

Spawn the architect agent via Task. Give it:
- The user's task (verbatim)
- The domain model JSON from Stage 1
- The codebase graph summary from Stage 1
- The curriculum hits from Stage 0 (if any)

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
python "./scripts/adr_writer.py" emit \
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

## Stage 2.3 — Source-driven doc lookup

Implementer agents emit code from training data + body_hints. For
post-cutoff API drift (Pydantic v2 quirks, FastAPI 0.110+ Annotated
deps, Spring Boot 3 javax→jakarta rename, TypeORM 0.3 DataSource,
GORM v2 Session API, …) training data can be wrong. This stage
verifies against current official docs.

```!
python "./scripts/source_docs_fetcher.py" --project <project-path> > /tmp/osp-doc-plan.json
```

The script detects the framework + exact pinned version from the
project's manifest (requirements.txt / pom.xml / package.json / go.mod)
and emits a doc-lookup plan — one entry per topic the implementer needs
to verify, with the official-doc URL + anchor keywords to look for.

For each entry in `lookups[]`, call WebFetch:

```text
WebFetch({
  url: <entry.url>,
  prompt: "Extract idiomatic example signatures involving:
           <comma-separated entry.anchor_keywords>.
           Return code examples only, under 40 lines total."
})
```

Bundle the responses into a `source_excerpts` field on each implementer
agent's prompt — they treat the excerpts as canonical truth, overriding
anything in body_hints that conflicts.

**Skip conditions**: `skip_reason: no_manifest_found` (greenfield project),
`framework_not_recognised`, or `version_pin_missing` (best-effort, no
version-gated lookups available). On skip, log a warning and proceed —
training data is the fallback.

Why this matters: lookups are cheap (~$0.005 each via WebFetch) and
catch a bug class our reviewer + critic can't catch (API drift inside
syntactically-correct code).

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
python "./scripts/incremental_planner.py" \
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

## Stage 3 — Implementer + test-author agents (PARALLEL)

For every entity in `spec.json` with `action: "create"`, spawn one
**implementer** agent. In the SAME message, spawn the **test-author**
agent once. These run in parallel — do not serialize them.

```text
[ implementer for entity 1 ] [ implementer for entity 2 ] ... [ test-author ]
```

Each agent invocation should:
- Reference `.claude/agents/{implementer,test-author}.md` for their full instructions.
- Pass the same `spec.json` to every agent so they share one source of truth.
- For implementer: pass the SPECIFIC entity/file it is responsible for.
- Write their outputs to `/tmp/osp-out/<path>` (each agent writes its own files).

The test-author MUST NOT read the implementer's output (separation of
concerns — this is the defence against the test/router contract drift
class of bug). It reads only `spec.json`.

After all agents return, sanity-check that every file in
`spec.api_surface` and every entity in `spec.entities` has corresponding
output in `/tmp/osp-out/`.

---

## Stage 4 — Verify + auto-patch (deterministic)

Run the static verifier against the generated output, then auto-patch any
known diagnostic classes:

```!
python "./scripts/generate_and_verify.py" --verify-dir /tmp/osp-out
```

If there are any error-severity diagnostics, run auto_patch:

```!
python "./scripts/auto_patch.py" --sandbox /tmp/osp-out \
    --diagnostics /tmp/osp-diags.json
```

Re-verify; if there are still errors after the patch attempt, hand them
back to the implementer agent for a second pass (max 2 retries).

---

## Stage 5 — Reviewer agent

Spawn the reviewer to gate on security/perf/style:

```text
Agent({
  description: "Reviewer: security + perf + style audit",
  subagent_type: "general-purpose",
  prompt: """
    Read .claude/agents/reviewer.md.
    Files to review: <list paths under /tmp/osp-out>
    Spec.json: <paste /tmp/osp-spec.json>
    Codebase graph imports: <paste>

    Emit REVIEW: PASS or REVIEW: REVISE per the agent spec.
    On REVISE, name the responsible agent (implementer / test-author)
    and the specific file:line:issue.
  """
})
```

If REVISE, route fixes back to the named agent and re-run reviewer (max 2
review iterations). If still red after 2, escalate to the user.

---

## Stage 5.5 — Doubt-driven adversarial pass (DEFAULT ON)

**Run this stage unless the user passed `--no-doubt`.** The reviewer
reads the spec, the implementer's reasoning, and previous review
history — that context makes it biased toward "this looks fine."
Stage 5.5 spawns a FRESH-CONTEXT **doubter** agent per artifact. The
doubter receives ONLY:
  1. The artifact's content (the generated file)
  2. The contract it must satisfy (entity attrs + test_contract + invariants)

It does NOT receive the spec.json's reasoning or the implementer/reviewer
notes. That information withholding is the point — it prevents
agreement bias and surfaces the bugs that "looks reasonable" reviews miss.

Initialise:
```!
python "./scripts/doubt_driver.py" init --sandbox <sandbox-dir>
```

For each artifact the implementer + reviewer produced:

```text
Agent({
  description: "Doubter: fresh-context adversarial review of <path>",
  subagent_type: "general-purpose",
  prompt: """
    Read .claude/agents/doubter.md.
    Artifact path: <path>
    Artifact content: <paste full file content>
    Contract: <paste ONLY entity + test_contract + invariants from spec.json>
    Emit findings + verdict per the agent spec.
  """
})
```

Capture the doubter's JSON output, then:
```!
python "./scripts/doubt_driver.py" record \
    --sandbox <sandbox-dir> \
    --artifact <path> \
    --verdict /tmp/osp-doubt-verdict.json
```

The driver returns one of three decisions:
  - `PROCEED` — no `contract_violation` or `actionable_gap` findings.
    Advance to Stage 6.
  - `LOOP_TO_IMPLEMENTER` — re-spawn the implementer with the
    `blocking_findings` list as the "why". After it rewrites the file,
    spawn the doubter again (round 2).
  - `ESCALATE` — max 2 doubt rounds OR same fingerprints across rounds
    (doubt theater). Stop, surface to user.

This stage is bounded: max 2 doubt rounds per artifact, max ~$0.04 per
round at sonnet pricing.

---

## Stage 6 — Wire + (if --apply) execute

Run the wirer in dry-run mode first:

```!
python "./scripts/auto_wirer.py" --project <project-path> \
    --generated-dir /tmp/osp-out --dry-run
```

Present the wire plan to the user.

**Before `--apply` mutates anything, run the production-readiness gates**
(unless the user passed `--no-ship-check`):

```!
python "./scripts/ship_gates.py" --project <project-path>
```

If verdict is `BLOCKED`: halt the apply, surface the failing gates to
the user, ask whether to address or override with `--force`.
If verdict is `READY_WITH_WARN`: list the warnings, proceed.
If verdict is `READY`: proceed silently.

For `--apply`, run the wirer again without dry-run and copy generated
files into the project:

```!
python "./scripts/auto_wirer.py" --project <project-path> \
    --generated-dir /tmp/osp-out
```

For SQLAlchemy/Django projects, optionally run migrations:
- Django: `python manage.py makemigrations && python manage.py migrate`
- Alembic: `alembic revision --autogenerate -m "<feature>"`

Ask the user before running migrations — they're high-side-effect.

### Stage 6.5 — Auto-generate Alembic revision

Instead of "ask the user before running migrations", emit a concrete
revision file the user can inspect and apply:

```!
python "./scripts/migration_generator.py" \
    --spec /tmp/osp-spec.json \
    --out <project>/alembic/versions/
```

This produces `<timestamp>_<slug>.py` with `upgrade()` + `downgrade()`
bodies derived from spec.json's entities and relationships. The user
runs `alembic upgrade head` when ready. For Django projects, the
script emits `MIGRATION_RUNBOOK.md` (Django generates migrations via
introspection).

---

## Stage 7 — Critic agent + multi-iteration loop

Before spawning the critic the first time, **initialise the loop state**
(this gives the deterministic driver something to track across iterations):

```!
python "./scripts/critic_loop_driver.py" init --sandbox <sandbox-dir>
```

After every critic spawn, **route the verdict through the driver** instead
of deciding the next step ad-hoc. The driver enforces the hard caps below
(max 3 iterations, max 5 min/iteration, escalate on new failure nodeids)
without you having to track state by hand:

```!
# Write the critic's JSON output to /tmp/osp-critic-verdict.json, then:
python "./scripts/critic_loop_driver.py" record \
    --sandbox <sandbox-dir> \
    --verdict /tmp/osp-critic-verdict.json
```

The driver returns one of three decisions:
  - `SHIPPED` — present success summary to the user, jump to Stage 8.
  - `LOOP_CONTINUE` — spawn the agents listed in `routes_by_agent` (one
    Task per bucket, NOT one per failure), re-verify, then call the
    critic again. Loop.
  - `ESCALATE` — stop. Use the `escalation_summary` field verbatim in
    the user-facing message, then write a bead and exit. Common reasons:
    `max_iterations_exceeded`, `iteration_timeout`, `regression_new_failures`.

The original critic spawn:

```text
Agent({
  description: "Critic: run tests, decide ship vs loop",
  subagent_type: "general-purpose",
  prompt: """
    Read .claude/agents/critic.md.
    Generated tests: <paths>
    Spec.json: <paste>

    Use Bash to run:  python ./scripts/critic_runner.py --tests <dir> --route --json
    Emit VERDICT: SHIPPED or VERDICT: LOOP per the agent spec.
  """
})
```

### Loop iteration protocol

The critic's response is either `SHIPPED` (done) or `LOOP` with structured
routes per failing test. When you get a `LOOP` verdict, do the following:

**Step A — Parse routes.** The critic emits a JSON-ish block like:
```json
{
  "verdict": "LOOP",
  "iteration": 1,
  "routes": [
    {"nodeid": "tests/test_cart.py::test_create",
     "route_to": "implementer", "reason": "missing validate_cart() method",
     "file": "cart/router.py", "traceback": "..."},
    {"nodeid": "tests/test_cart.py::test_unauthorized",
     "route_to": "test-author", "reason": "test asserts 401 but spec says auth: none"}
  ]
}
```

**Step B — Group routes by agent.** Bucket the failures by `route_to`.
Each bucket becomes ONE re-spawn (NOT one per failure).

**Step C — Re-spawn the right agent with the route as context.**

  - For **implementer** routes: pass the original spec.json, the file
    they need to fix, and the failure list. The implementer rewrites
    just that file. Critical: include the diagnostic text verbatim so
    the implementer knows WHY it's being re-run.

    ```text
    Agent({
      description: "Implementer: regenerate cart/router.py to fix critic findings",
      subagent_type: "general-purpose",
      prompt: """
        Read .claude/agents/implementer.md.
        You are regenerating ONE file: cart/router.py
        Spec.json: <paste>
        Codebase imports: <paste>

        The critic just rejected your previous output. Here is why:
        Failure 1: <route 1 reason + traceback>
        Failure 2: <route 2 reason + traceback>
        ...

        Produce the corrected file content. Do NOT touch other files.
      """
    })
    ```

  - For **test-author** routes: pass the spec.json (with any contract
    adjustments the critic requested), the failing test list, and the
    rule "regenerate test_X.py to match the spec only." The
    test-author still does NOT read the implementer's output.

  - For **architect** routes: the spec itself was wrong. Re-spawn the
    architect with the critic's reasoning to produce a v2 of spec.json.
    Then restart from Stage 3 (re-run implementers + test-author against
    the new spec).

  - For **reviewer** routes: a security/perf finding slipped past. The
    reviewer's output identifies the file; route it to the implementer
    with the reviewer's note as the "why."

**Step D — Re-verify after re-spawn.** Re-run Stage 4 (verify +
auto-patch) on the changed files, then jump back into the critic at
Stage 7 with the updated sandbox.

**Step E — Stop conditions.** Hard caps:
  - **Max 3 critic iterations total.** Count each LOOP→re-spawn→re-verify
    cycle as one iteration. On iteration 4 entry, do not re-spawn —
    escalate.
  - **Max 5 minutes per iteration.** If the implementer takes longer,
    abort the iteration and escalate.
  - **No new failure classes.** If iteration N introduces failure types
    that iteration N-1 didn't have, that's regression — escalate
    immediately rather than continuing to loop.

**Step F — Escalation.** When stopping without SHIPPED:
  1. Write a structured failure bead via `beads_writer.py` with the full
     route history.
  2. Present to the user: which tests still fail, which agent owns the
     remaining failure, the sandbox path so they can inspect.
  3. Do NOT silently patch over a failure by deleting tests or skipping
     them. That's a separate explicit user action.

### Successful SHIPPED path

If the critic returns SHIPPED, present a summary to the user:
- Files created (count + paths)
- Files modified (wire actions)
- Test results (passed / total)
- Iterations consumed (1 = clean shot; 2-3 = needed loops)
- Token cost estimate (if `--budget` was set) vs actual if tracked
- Any auto-patches applied (info diagnostics from Stage 4)

---

## Stage 8 — Record + finalize

On SHIPPED:
```!
python "./scripts/codebase_graph.py" <project-path> --rebuild
```
This refreshes the persistent graph so the next session knows about the
files you just added.

**Then — regardless of SHIPPED or ESCALATE — call `run_finalize.py`** so
every agent that ran picks up a row in `.claude/registry/learnings.jsonl`:

```!
python "./scripts/run_finalize.py" \
    --sandbox <sandbox-dir> \
    --agents architect,implementer,test-author,reviewer,wirer,critic \
    --task-keywords "$ARGUMENTS" \
    --repo-root .
```

run_finalize reads the critic loop driver's final state and derives
per-agent outcomes: SHIPPED → everyone succeeded; ESCALATE → agents
whose route_to bucket still has open failures are recorded as `failed`,
the rest as `succeeded` (their work wasn't what broke). The
`/learnings top-agents` slash command surfaces those ratings so drift
in a local agent's success rate is visible before the next big run.

On any failure that escalated to the user, ALSO record a bead:
```!
python "./scripts/beads_writer.py" --phase agentic \
    --task "$ARGUMENTS" --kind agent_loop_max_iters \
    --diagnostics /tmp/osp-final-diags.json
```

Future sessions will read this via the curriculum and avoid the same
trap.

---

## Hard rules

1. **Always spawn agents in parallel where possible.** Implementer agents
   for different files are independent — they all run in one Task batch.
2. **Test-author reads spec.json only**, never the implementer's output.
   This separation is non-negotiable.
3. **Max 3 critic-loop iterations.** No silent infinite loops.
4. **Wire is dry-run by default.** Only mutate the user's project with
   explicit `--apply`.
5. **Curriculum first.** Always consult `beads_curriculum` before
   generation — the cost is a few milliseconds and the saved heartache is
   significant.

---

## Failure escape hatch

If you cannot complete any stage (e.g. the architect agent times out, the
critic refuses to verdict), do NOT try to substitute your own
implementation for the agent's. Fall back to the templated path:

```!
python "./scripts/one_shot_orchestrator.py" "$ARGUMENTS" --json
```

…and present the result to the user with a note explaining what failed.
The templated path is lower quality but always works.

---

## Why this skill is structured this way

We tried generating code via Python regex templates first (175+ scripts
under `scripts/`). It produced mediocre code that needed constant
patching. The agentic path lets Claude (you) reason about the user's
actual code, not just a template. Deterministic services stay in Python
where they belong (scan, verify, patch, wire, run tests, record). Code
generation moves to Claude where the quality difference shows.
