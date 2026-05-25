# Observability Dashboard Examples

## Query 1: Pipeline Latency by Stage

In Jaeger:
```
service.name = "one-shot-generate"
span.kind = "INTERNAL"
```

Look for these stages in the trace tree:
- curriculum_check: ~50ms
- extract_domain_model: ~80ms
- generate_spec (architect agent): ~10-15s (includes Claude API round-trip)
- write_code (implementer + test-author agents, parallel): ~45-60s (both agents run in parallel, total wall-time)
- verify_and_patch: ~1-2s
- security_review (reviewer agent): ~10-15s (includes Claude API round-trip)
- auto_wire_main: ~500ms
- run_tests (critic agent): ~10-15s (includes Claude API round-trip)
- record_beads: ~100ms

**Total expected: 90-120s (1.5-2 minutes) per full generation**

**Note:** Agent stages (architect, implementer, test-author, reviewer, critic) run via Claude Task API, which adds 5-20s per invocation for queuing and network latency, even for fast operations.

## Understanding Latencies

The pipeline has two types of stages:

1. **Deterministic Python stages** (curriculum_check, extract_domain_model, verify_and_patch, auto_wire_main, record_beads):
   - Fast (under 2s each)
   - Run locally

2. **Agent stages** (architect, implementer, test-author, reviewer, critic):
   - Slow (10-60s each, depending on parallelism)
   - Run via Claude Task API
   - Include API round-trip latency, not just compute time
   - Implementer and test-author run *in parallel* (not additive)

Critical path: curriculum → scan → **architect** → **[implementer + test-author parallel]** → **reviewer** → **critic**

The parallel write_code stage is the main contributor to total latency.

## Query 2: Critical Path & Error Detection

In Jaeger, filter for:
```
span.status = "ERROR" OR span.duration > 10000
```

This finds:
- Agent stages taking longer than expected (> 10s suggests API or network issues)
- Failed spans (agent errors, invalid output)

**If you find error spans:**
- Check the span logs for error messages
- If the error is in architecture or code generation, review the span's input/output logs
- If the error is network-related, check agent service health

## Query 3: Parallel Execution Efficiency

In Jaeger, look for the "write_code" stage and its child spans:

```
service = "one-shot-generate"
span.name = "write_code"
```

You should see 2 parallel child spans:
- One under service "implementer" (starting near the same timestamp)
- One under service "test-author" (starting near the same timestamp)

**Good parallelism:** Both child spans start and end at overlapping times.
**Poor parallelism:** One child span finishes before the other starts (indicates sequential execution instead of parallel).

View in Jaeger:
1. Open the "write_code" span in detail view
2. Look at the child spans' start times and durations
3. If durations overlap significantly (e.g., implementer 0-60s, test-author 0-60s), you have true parallelism
4. If one is 0-30s and the other is 30-60s, they're sequential (possible optimization needed)
