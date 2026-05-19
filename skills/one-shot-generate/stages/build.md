## Stage 3 — Implementer + test-author agents (PARALLEL)

**Mode selection:**
- Default: parallel mode (implementer × N + test-author all fire at once)
- `--tdd-strict`: route through the **tdd-cycle** skill instead. One
  entity at a time, strict RED → GREEN → REFACTOR per behavior:

  ```!
  @./../../tdd-cycle/SKILL.md
  ```

  Pass `--phase=red` first for each entity to generate failing tests,
  verify they fail, THEN generate minimal implementation (`--phase=green`),
  THEN refactor (`--phase=refactor`). Slower (~3x wall-clock), but
  prevents hollow test suites where tests just mirror the impl.

  When to use: high-stakes features (auth, payments, compliance) where
  test correctness matters more than generation speed.

Default-mode behavior continues below.

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
python "../one-shot-generator/scripts/generate_and_verify.py" --verify-dir /tmp/osp-out
```

If there are any error-severity diagnostics, run auto_patch:

```!
python "../one-shot-generator/scripts/auto_patch.py" --sandbox /tmp/osp-out \
    --diagnostics /tmp/osp-diags.json
```

Re-verify; if there are still errors after the patch attempt, hand them
back to the implementer agent for a second pass (max 2 retries).

---
