## Stage 8 — Record + finalize

On SHIPPED:
```!
python "../one-shot-generator/scripts/codebase_graph.py" <project-path> --rebuild
```
This refreshes the persistent graph so the next session knows about the
files you just added.

**Then — regardless of SHIPPED or ESCALATE — call `run_finalize.py`** so
every agent that ran picks up a row in `.claude/registry/learnings.jsonl`:

```!
python "../one-shot-generator/scripts/run_finalize.py" \
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
python "../one-shot-generator/scripts/beads_writer.py" --phase agentic \
    --task "$ARGUMENTS" --kind agent_loop_max_iters \
    --diagnostics /tmp/osp-final-diags.json
```

Future sessions will read this via the curriculum and avoid the same
trap.

---

## Stage 8.5 — Handoff document (on SHIPPED)

On SHIPPED, produce a compact handoff document for the user that strips
the verbose generation conversation but preserves every decision and
artifact. Invoke the **handoff** skill:

```!
@./../../handoff/SKILL.md
```

Pass `--from-last-output --format=markdown --audience=developer`. The
skill emits a runbook with: files generated/modified, migration to apply,
wire-up changes, test commands, env vars needed, rollback path. Typical
output is ~10% of the conversation size.

Write the handoff to `/tmp/osp-handoff.md` and reference it in the final
user-facing summary. This becomes the deployment checklist for the
generated feature.

Skip on ESCALATE (no handoff needed when the run didn't ship) or when
`--no-handoff` was passed.

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
python "../one-shot-generator/scripts/one_shot_orchestrator.py" "$ARGUMENTS" --json
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
