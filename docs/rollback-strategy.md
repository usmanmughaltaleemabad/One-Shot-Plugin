# Autonomous Rollback Strategy

## Overview

The one-shot-generate pipeline includes autonomous rollback capability to recover from consecutive failures without manual intervention. When N consecutive failures occur (default N=3), the system automatically rolls back to the last successful state using the `.osp.bak` backup mechanism.

This document explains the rollback mechanism, when it triggers, and how to control it.

---

## When Rollback Triggers

Rollback is triggered in **Stage 7.5** (after the critic verdict) when:

1. **Consecutive failure count** reaches the threshold (default: 3)
2. **User has not disabled rollback** (default: enabled)
3. **A valid `.osp.bak` backup directory exists** with one or more backup files

### Failure Counter

The failure counter is maintained in `.beads/failures_state.jsonl` and tracks:
- `consecutive_failures` — integer count of failures in a row
- `last_failing_spec` — hash of the spec that caused the last failure
- `last_failure_ts` — ISO 8601 timestamp of the last failure

A new failure increments the counter; a successful SHIPPED verdict resets it to 0.

---

## Backup Mechanism (.osp.bak)

The `.osp.bak` directory stores backup snapshots of generated code *before* execution:

```
.osp.bak/
  ├── <timestamp>_<entity>_models.py.osp.bak
  ├── <timestamp>_<entity>_router.py.osp.bak
  ├── <timestamp>_test_<entity>.py.osp.bak
  └── ...
```

### What Gets Backed Up

- Generated Python files (models, routers, handlers)
- Generated test files
- Generated migration files (Alembic/Django)
- Any files written by the agentic pipeline (Stages 3–5)

**Not backed up:**
- User modifications to existing code
- Configuration files
- `.env` or secrets
- Uncommitted changes in git

### Backup Creation

The backup directory is created automatically at the start of Stage 3 (BUILD phase). Each file is suffixed with `.osp.bak` to distinguish it from working files.

If rollback is triggered, the orchestrator:

1. **Stashes uncommitted git changes** to restore a clean state
2. **Applies each `.osp.bak` file** by restoring it to its original location
3. **Resets the failure counter** to 0

---

## Enabling / Disabling Rollback

### Default Behavior (Enabled)

By default, rollback is enabled with a threshold of 3 consecutive failures:

```bash
/one-shot "add shopping cart" @./project --apply
# Rollback enabled automatically; will trigger on 3 failures
```

### Explicitly Enable with Custom Threshold

To enable rollback with a specific threshold (example: 2 failures):

```bash
/one-shot "add shopping cart" @./project --apply --rollback
# Uses default threshold of 3
```

### Disable Rollback

To disable autonomous rollback and require manual recovery:

```bash
/one-shot "add shopping cart" @./project --apply --rollback=false
# Rollback disabled; failures escalate without recovery
```

---

## Rollback Workflow

### Success Path (SHIPPED)

```
Critic → SHIPPED verdict
  ↓
[AUTO-ROLLBACK] Check: 0 failures
  ↓
Reset failure counter to 0
  ↓
Present summary to user
```

### Loop Path (LOOP < 3 failures)

```
Critic → LOOP verdict, iteration 1–2
  ↓
[AUTO-ROLLBACK] Check: failures < 3
  ↓
Record failure for this spec
  ↓
Re-spawn implementer/test-author
  ↓
Back to critic
```

### Rollback Path (LOOP ≥ 3 failures)

```
Critic → LOOP verdict, iteration 3
  ↓
[AUTO-ROLLBACK] Check: failures >= 3 ✓
  ↓
Stash changes + Apply .osp.bak files
  ↓
Reset failure counter to 0
  ↓
Present escalation to user:
   "Rollback completed. Rolling back to last known good.
    Recommend: adjust spec, add constraints, or retry with --grill"
```

### Rollback Failure Path

If rollback itself fails (e.g., `.osp.bak` missing, git stash error):

```
[AUTO-ROLLBACK] Rollback failed: <error>
  ↓
Escalate immediately
  ↓
Present error to user with:
  - Reason for failure (e.g., "No .osp.bak directory found")
  - Sandbox path for manual recovery
  - Suggestion to inspect .beads/failures_state.jsonl
```

---

## Inspection & Debugging

### Check Current Failure State

```bash
python scripts/one-shot-generator/scripts/failure_detector.py --action status
```

Output:
```json
{
  "consecutive_failures": 2,
  "last_failing_spec": "abc123def456...",
  "last_failure_ts": "2025-05-20T14:32:18Z"
}
```

### Check if Rollback Would Trigger

```bash
python scripts/one-shot-generator/scripts/failure_detector.py --action should-trigger --threshold 3
```

Output:
```
Consecutive failures: 2 / Threshold: 3
Trigger rollback: false
```

### Manually Trigger Rollback (Force)

```bash
python scripts/rollback.py --force --repo-root /path/to/project
```

### Reset Failure Counter

```bash
python scripts/one-shot-generator/scripts/failure_detector.py --action reset
```

---

## Common Scenarios

### Scenario 1: Code generation keeps looping (3+ failures)

**Symptom:** Critic routes to implementer/test-author repeatedly; same tests fail.

**What happens:**
1. Iteration 1 fails → record_failure() → consecutive_failures=1
2. Iteration 2 fails (different error) → record_failure() → consecutive_failures=2
3. Iteration 3 fails → record_failure() → consecutive_failures=3 → **Rollback triggers**

**Result:** `.osp.bak` files are restored, project returns to pre-generation state, failure counter reset to 0.

**Next steps:**
- Review the escalation summary (which tests are failing)
- Adjust the feature description or spec constraints
- Retry with `--grill` (interactive clarification)

### Scenario 2: Rollback disabled, want manual control

**Setup:**
```bash
/one-shot "add shopping cart" @./project --apply --rollback=false
```

**What happens:** If 3+ failures occur, pipeline escalates without rollback. User can then:
- Manually inspect `.osp.bak` files
- Manually restore desired state
- Decide whether to retry or adjust approach

---

## Advanced Configuration

### Custom Threshold

To use a different threshold, modify the threshold parameter in Stage 7.5 of `stages/ship.md`:

```python
if should_trigger_rollback(threshold=5):  # Changed from 3 to 5
    print("[AUTO-ROLLBACK] 5 consecutive failures detected...")
    execute_rollback()
```

Then redeploy the plugin.

### Conditional Rollback

To rollback only on specific failure types, extend `failure_detector.py`:

```python
def should_trigger_rollback_for(failure_class: str, threshold: int = 3) -> bool:
    """Rollback only for logic errors, not syntax errors."""
    state = load_failure_state()
    if state["last_failing_spec"] is None:
        return False
    # Check if last N failures are all of the same class
    # (requires extending failures_state.jsonl schema)
    return state["consecutive_failures"] >= threshold
```

---

## Guarantees & Limitations

### Guarantees

- **Atomic rollback:** All `.osp.bak` files are restored or none are (git stash ensures clean state).
- **Failure tracking:** Consecutive count persists across sessions (stored in `.beads/failures_state.jsonl`).
- **No data loss:** User code prior to generation is never touched; only generated files are restored.

### Limitations

- **Generated code only:** Rollback restores generated files, not manual edits to existing code.
- **No migration rollback:** If a migration was applied during Stage 6, rollback does NOT undo it. User must manually `alembic downgrade` or `python manage.py migrate <prev>`.
- **`.osp.bak` must exist:** Rollback requires backups created at START of Stage 3. If backups are deleted, rollback is not possible.
- **No spec rollback:** Rollback restores files, not `spec.json`. If the spec itself is wrong, user must fix it and retry.

---

## Troubleshooting

### ".osp.bak directory not found"

**Cause:** Backups were not created or were deleted.

**Fix:**
1. Check if `.osp.bak/` exists: `ls -la .osp.bak/`
2. If missing, backups were never created. Re-run with a fresh project state.
3. If deleted manually, rollback is not possible. User must either:
   - Manually restore from git history
   - Adjust the feature request and retry

### "Failed to stash changes"

**Cause:** Uncommitted changes could not be stashed (e.g., git not initialized).

**Fix:**
1. Ensure project is a git repository: `git init` if needed
2. Commit or remove conflicting changes manually
3. Retry with `--apply`

### "Rollback succeeded but tests still fail"

**Cause:** Rollback restored files, but the underlying spec or architecture is flawed.

**Fix:**
1. Inspect the escalation summary for which tests fail
2. Review the feature description for ambiguities
3. Retry with `--grill` for interactive clarification before generation

---

## References

- **Failure detector:** `skills/one-shot-generator/scripts/failure_detector.py`
- **Rollback orchestrator:** `scripts/rollback.py`
- **Backup mechanism:** `scripts/git_safety.py`
- **Critic loop driver:** `skills/one-shot-generator/scripts/critic_loop_driver.py`
- **Pipeline stages:** `skills/one-shot-generate/stages/`
