## Stage 6 — Wire + (if --apply) execute

Run the wirer in dry-run mode first:

```!
python "../one-shot-generator/scripts/auto_wirer.py" --project <project-path> \
    --generated-dir /tmp/osp-out --dry-run
```

Present the wire plan to the user.

**Before `--apply` mutates anything, run the production-readiness gates**
(unless the user passed `--no-ship-check`):

```!
python "../one-shot-generator/scripts/ship_gates.py" --project <project-path>
```

If verdict is `BLOCKED`: halt the apply, surface the failing gates to
the user, ask whether to address or override with `--force`.
If verdict is `READY_WITH_WARN`: list the warnings, proceed.
If verdict is `READY`: proceed silently.

For `--apply`, run the wirer again without dry-run and copy generated
files into the project:

```!
python "../one-shot-generator/scripts/auto_wirer.py" --project <project-path> \
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
python "../one-shot-generator/scripts/migration_generator.py" \
    --spec /tmp/osp-spec.json \
    --out <project>/alembic/versions/
```

This produces `<timestamp>_<slug>.py` with `upgrade()` + `downgrade()`
bodies derived from spec.json's entities and relationships. The user
runs `alembic upgrade head` when ready. For Django projects, the
script emits `MIGRATION_RUNBOOK.md` (Django generates migrations via
introspection).

#### Why migration AFTER implementer code (not before)

A reasonable critique (Gemini, v4.11): shouldn't the schema be decided
BEFORE the implementer writes code, since the database structure
dictates how the code is written?

**For greenfield entities** (the dominant `/one-shot` use case): no.
Both the implementer's `models.py` AND the Alembic migration derive
from the **same source** — `spec.json`. The implementer writes models;
Alembic's `--autogenerate` then compares those models to the current
DB and emits the migration. spec.json is the single source of truth;
there's no possibility of code/migration drift because both are
projections of the same spec.

**For modifying existing entities** (add column to existing table):
the order matters more. Three sub-cases:

1. **Spec adds a column to an existing entity.** Stage 1 codebase
   scan already loaded the existing model. The architect's spec
   reflects the merged shape (existing + new fields). Implementer
   updates the model accordingly. Migration is emitted last and
   captures only the delta. **No drift risk.**

2. **Spec adds a column with a NOT NULL constraint + default.** The
   migration MUST include a `server_default` + backfill step, OR be
   split into two revisions (add nullable → backfill → set NOT NULL).
   Stage 6.5 inspects spec.json for new NOT NULL columns and surfaces
   this as a `MIGRATION_RUNBOOK.md` warning — never silently emits a
   migration that would lock prod or fail mid-deploy.

3. **Spec renames or drops an existing column.** Stage 6.5 refuses to
   auto-emit destructive migrations. It emits a `MIGRATION_RUNBOOK.md`
   with the manual two-step expand/contract pattern; the user runs
   the operations explicitly during a maintenance window.

**Bottom line**: the order works because spec.json drives both code
and DDL. The trade-off is only visible in case 2 / case 3, where Stage
6.5 deliberately produces a *runbook* rather than an auto-applied
migration. See [docs/cookbook.md](../docs/cookbook.md) §
"Modifying-existing-entity migrations" for worked examples.

---

## Stage 7 — Critic agent + multi-iteration loop

Before spawning the critic the first time, **initialise the loop state**
(this gives the deterministic driver something to track across iterations):

```!
python "../one-shot-generator/scripts/critic_loop_driver.py" init --sandbox <sandbox-dir>
```

After every critic spawn, **route the verdict through the driver** instead
of deciding the next step ad-hoc. The driver enforces the hard caps below
(max 3 iterations, max 5 min/iteration, escalate on new failure nodeids)
without you having to track state by hand:

```!
# Write the critic's JSON output to /tmp/osp-critic-verdict.json, then:
python "../one-shot-generator/scripts/critic_loop_driver.py" record \
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

    Use Bash to run:  python ../one-shot-generator/scripts/critic_runner.py --tests <dir> --route --json
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
