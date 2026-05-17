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

## Stage 7 — Critic agent

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

If LOOP, route the failures back to the responsible agents (the critic's
output names them). Loop max 3 times total. After 3 reds, escalate.

If SHIPPED, record success and present a summary to the user:
- Files created
- Files modified (wire)
- Test results
- Token cost estimate (if --budget was set)

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
