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

## Stage 6 — Wire + (if --apply) execute

Run the wirer in dry-run mode first:

```!
python "./scripts/auto_wirer.py" --project <project-path> \
    --generated-dir /tmp/osp-out --dry-run
```

Present the wire plan to the user. If they invoked with `--apply`, run
again without `--dry-run` and copy generated files into the project:

```!
python "./scripts/auto_wirer.py" --project <project-path> \
    --generated-dir /tmp/osp-out
```

For SQLAlchemy/Django projects, optionally run migrations:
- Django: `python manage.py makemigrations && python manage.py migrate`
- Alembic: `alembic revision --autogenerate -m "<feature>"`

Ask the user before running migrations — they're high-side-effect.

---

## Stage 7 — Critic agent + multi-iteration loop

Spawn the critic to actually run the generated tests:

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

On any failure that escalated to the user, record a bead:
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
