# Predictive Failure Detection

## Overview

The failure predictor is an embedding-based safety mechanism that detects risky feature requests before the agentic pipeline fires. It runs in **Stage 0.3** (after curriculum check) and emits **hard warnings** when a task is similar to past failures.

This document explains:
- How prediction works (embedding similarity to curriculum)
- Example hard warning in action
- How to disable warnings with `--force`
- Curriculum learning mechanics
- Mitigation options

## How It Works

The failure predictor compares your feature request against a curriculum of past failures. It:

1. **Loads the curriculum** — reads `.beads/curriculum.jsonl` (all past failures, reasons, mitigations)
2. **Embeds your task** — converts your feature request to a dense vector
3. **Searches for similar failures** — finds past failures with high embedding similarity
4. **Emits a hard warning** if similarity ≥ 0.8 (default threshold)

### Embedding Similarity

The predictor uses **OpenAI embeddings** (or fallback embeddings if configured) to compute semantic similarity. This means:

- "shopping cart with discounts" and "add discount logic to checkout" will match
- "REST API with pagination" and "build paginated endpoints" will match
- Typos and minor wording changes are handled gracefully
- Purely novel tasks (no past failures) return `[OK]`

### Threshold

The default threshold is **0.8**. A task triggers a hard warning if:

```
similarity_score >= 0.8
```

Lower threshold (e.g., 0.7) = more conservative, more warnings
Higher threshold (e.g., 0.9) = more lenient, fewer warnings

Users can adjust via the predictor CLI:
```bash
python failure_predictor.py "your task" --threshold 0.75
```

## Hard Warning Example

When a risky task is detected, the output looks like this:

```
===========================================================================
[!] HARD WARNING: Task Appears Risky Based on Curriculum Analysis
===========================================================================

Task Similarity: 87.0% match with past failures
Related Failure: bd-001

Why This Failed Before:
  FK column type mismatch: spec says int but migration generated String(255)

Mitigation from Curriculum:
  Check type: key in spec.json matches migration_generator.py type mapping

Recommended Action Items:
  1. Use --review flag to inspect generated spec before BUILD zone
  2. Consider --templated fallback for quick iteration
  3. Set --budget=0.50 to limit cost if trying experimental approach
  4. Review curriculum entry: .beads/curriculum.jsonl (search for bead_id)

===========================================================================
```

## Disabling Warnings: --force Flag

If you want to proceed despite a hard warning, pass `--force`:

```bash
/one-shot "shopping cart with discounts" @./project --force
```

The `--force` flag:
- **Bypasses the hard warning confirmation gate** in Stage 0.3
- **Does NOT bypass** the confidence gate in Stage 1 (extract_domain_model)
- **Does NOT bypass** cost budget gate in Stage 1.5 (if `--budget=USD` is set)

**When to use --force:**
- You know the past failure and have a fix
- You're willing to take the risk for experimental features
- You're running in CI/CD and can't interact with prompts

## Curriculum Learning Mechanics

Each time a task fails, it's recorded as a "bead" in `.beads/curriculum.jsonl`:

```jsonl
{"id": "bd-001", "task_text": "shopping cart with line items and discounts", "reason": "FK column type mismatch: spec says int but migration generated String(255)", "mitigation": "Check type: key in spec.json matches migration_generator.py type mapping", "timestamp": "2026-05-20T14:32:00Z"}
{"id": "bd-002", "task_text": "REST API with pagination endpoint", "reason": "Pagination envelope mismatch: test_contract expects 'next' key but router doesn't emit it", "mitigation": "Set test_contract.pagination='list' or add next/prev to router response", "timestamp": "2026-05-20T15:10:00Z"}
```

### How Beads Flow into Curriculum

1. Task fails → critic agent records the failure reason
2. Beads are logged in `.beads/curriculum.jsonl`
3. Next invocation: predictor loads curriculum and compares
4. If similar task: hard warning emitted
5. User can review mitigation and proceed (or not)

### Curriculum Refresh

The curriculum is **never cleared automatically**. It grows over time as you accumulate beads.

To inspect the curriculum:
```bash
cat .beads/curriculum.jsonl | jq .
```

To remove a specific bead (if you've fixed the underlying issue):
```bash
grep -v "bd-001" .beads/curriculum.jsonl > /tmp/new.jsonl && mv /tmp/new.jsonl .beads/curriculum.jsonl
```

## Mitigation Options

When you hit a hard warning, you have 4 options:

### Option 1: Use --review (Recommended for First-Time Risks)

```bash
/one-shot "shopping cart with discounts" @./project --review
```

- Generates the spec, but **pauses** before agents fire
- You can inspect `spec.json` and see if the fix addresses the past failure
- Then confirm to proceed or bail out

### Option 2: Use --templated (Fallback to Deterministic)

```bash
/one-shot "shopping cart with discounts" @./project --templated
```

- Uses the legacy Python-only pipeline (no Claude tokens)
- Deterministic, no agentic agents
- Lower quality, but faster and cheaper
- Useful if you want to quickly validate the domain model

### Option 3: Set --budget=0.50 (Cost Cap)

```bash
/one-shot "shopping cart with discounts" @./project --budget=0.50
```

- Limits the cost to $0.50 max
- If the estimated cost exceeds budget, Stage 1.5 halts and asks
- Reduces blast radius if something goes wrong

### Option 4: Use --force (Accept the Risk)

```bash
/one-shot "shopping cart with discounts" @./project --force
```

- Acknowledge the warning and proceed
- Use this when you **know** the fix and are confident

## Stage 0.3 in the Pipeline

Stage 0.3 executes **after curriculum lookup** but **before extraction**:

```
Stage 0: Curriculum check (informational)
        ↓
Stage 0.3: Predictive failure check (gating)
        ↓
Stage 0.5: External resource discovery
        ↓
Stage 0.7: Legacy-safe gate (if --legacy-safe)
        ↓
Stage 1: Scan & extract domain model
```

Key points:
- **Stage 0** is informational (curriculum hits inform architect)
- **Stage 0.3** is gating (hard warning blocks unless --force)
- **Stage 0.5** is advisory (route-overrides apply to later stages)
- **Stage 0.7** is blocking (legacy-safe rules enforce constraints)

## Integration with OTel Tracing

Stage 0.3 emits an OTel span:

```python
with tracer.start_as_current_span("predictive_check") as span:
    span.set_attribute("stage", "predictive_check")
    span.set_attribute("will_fail", prediction.will_fail)
    span.set_attribute("similarity", prediction.similarity)
    span.set_attribute("bead_id", prediction.bead_id)
```

View in Jaeger:
```
http://localhost:16686
Search: service='one-shot-generate' operation='predictive_check'
```

## FAQ

**Q: What if embeddings fail (e.g., API down)?**

A: The predictor gracefully skips. You get `[OK]` and the pipeline continues.

**Q: Can I train the predictor?**

A: No. The predictor is a *read-only* system. It learns from beads automatically as they accumulate.

**Q: What if the curriculum is empty?**

A: You get `[OK]`. No past failures = no warnings.

**Q: Can I use a custom embedding model?**

A: Yes. Edit `scripts/curriculum_v2.py` and set `EMBEDDING_MODEL` to your choice.

**Q: How often should I review the curriculum?**

A: Periodically (e.g., monthly), especially if:
- You've fixed a systemic issue
- A bead's mitigation is no longer relevant
- You want to prune "solved" failures

**Q: Does --force also bypass cost budget?**

A: No. `--force` bypasses the predictive warning gate *only*. The cost budget gate (Stage 1.5) is independent.

## See Also

- `failure_predictor.py` — CLI tool, main logic
- `curriculum_v2.py` — curriculum loading and embedding
- `.beads/curriculum.jsonl` — raw curriculum data
- `stages/plan.md` Stage 0.3 — the execution stage
- `SKILL.md` — PLAN phase documentation
