# Span Propagation Through Pipeline

This document outlines the OpenTelemetry (OTel) span architecture for the one-shot-generate pipeline, tracking execution across all 9 pipeline stages (0–8).

## Overview

The one-shot generation pipeline executes as a deterministic sequence of stages, each producing outputs that feed into the next. OTel spans are emitted for each stage to enable:

- **Latency tracing**: Identify which stages consume the most wall-clock time
- **Error attribution**: Track failures to their originating stage
- **Cost accounting**: Correlate stages with API calls and token usage
- **Decision introspection**: Debug routing and approval gates

## Pipeline Stages and Span Names

| Stage | Name | Span Name | Entry Point | Role |
|-------|------|-----------|-------------|------|
| **0** | Curriculum lookup | `curriculum_check` | `beads_curriculum.py` | Check if task has failed before; surface learnings |
| **1** | Deterministic scan | `extract_domain_model` | `extract_domain_model.py` | Scan codebase; extract entities + relationships |
| **2** | Architect agent | `generate_spec` | Architect (Task, Sonnet) | Design data model + schema; emit spec.json |
| **3** | Implementer + Test-Author | `write_code` | Implementer + Test-Author (Task, Haiku+Sonnet parallel) | Generate implementation files and tests |
| **4** | Verify + Auto-patch | `verify_and_patch` | Auto-patch (4 Python rules) | Syntax check; apply 4 common bug-fix rules |
| **5** | Reviewer agent | `security_review` | Reviewer (Task, Sonnet) | Security scan; style + perf review |
| **6** | Wire main.py | `auto_wire_main` | Wirer (Python) | Insert generated entities into main.py / urls.py |
| **7** | Critic agent | `run_tests` | Critic (Task, Sonnet; up to 3 loops) | Run pytest; emit SHIPPED / ESCALATED verdict |
| **8** | Record beads | `record_beads` | Beads store (Python) | Update curriculum graph; log learnings |

## Trace Context Propagation

### Within SKILL.md (Single-Process)

All stages run in a single Python process (the SKILL dispatcher). Spans nest hierarchically:

```
one-shot-generate (root span)
├─ curriculum_check
├─ extract_domain_model
├─ generate_spec (→ Task: architect agent)
│  └─ (child spans inside Task)
├─ write_code (→ Task: implementer + test-author parallel)
│  ├─ (child spans inside implementer Task)
│  └─ (child spans inside test-author Task)
├─ verify_and_patch
├─ security_review (→ Task: reviewer agent)
│  └─ (child spans inside Task)
├─ auto_wire_main
├─ run_tests (→ Task: critic agent, up to 3 loops)
│  └─ (child spans inside Task)
└─ record_beads
```

Each stage span:
- **Opens** when the stage dispatcher calls the stage function
- **Sets attributes**: stage name, parameters (if any), start timestamp
- **Closes** when the stage completes or raises an exception
- **Records exception** if the stage fails (for root-cause visibility)

### Across Task Invocations (Multi-Process)

When a stage spawns an external agent via the Task tool (e.g., Architect in Stage 2, Critic in Stage 7), trace context flows via environment variable:

1. **SKILL.md** captures the current span context before invoking Task:
   ```python
   ctx = capture_context()
   os.environ["OTEL_TRACE_CONTEXT"] = serialize_context(ctx)
   ```

2. **Task/agent process** reads `OTEL_TRACE_CONTEXT` on startup and continues the trace:
   ```python
   ctx = os.environ.get("OTEL_TRACE_CONTEXT")
   if ctx:
       restore_context(deserialize_context(ctx))
   ```

3. **Agent span** nests under the stage span, showing that the agent's work was triggered by that stage

This enables end-to-end tracing even though agents run in separate processes.

## Span Attributes

Each span includes:

| Attribute | Type | Example | Set By |
|-----------|------|---------|--------|
| `stage` | string | `"extract_domain_model"` | Stage wrapper |
| `status` | enum | `"success"` \| `"error"` | Stage wrapper (on completion) |
| `entity_count` | int | `3` | Domain extractor (Stage 1) |
| `entity_names` | string (CSV) | `"User,Order,LineItem"` | Domain extractor (Stage 1) |
| `spec_json_size` | int | `4851` (bytes) | Architect (Stage 2) |
| `files_generated` | int | `5` | Implementer (Stage 3) |
| `tests_passing` | bool | `true` | Critic (Stage 7) |
| `test_duration_ms` | int | `1240` | Critic (Stage 7) |
| `cost_usd` | float | `0.34` | Cost tracker (all stages) |

## Jaeger Integration

Spans are exported to a Jaeger agent running on `localhost:6831` (via OpenTelemetry's `JaegerExporter`).

### Running Jaeger locally for development:

```bash
docker run \
  --name jaeger \
  -p 6831:6831/udp \
  -p 16686:16686 \
  jaegertracing/all-in-one:latest
```

Then view traces at http://localhost:16686.

### In production:

Deploy the Jaeger collector as a sidecar or in-cluster service; point the exporter to it via `JAEGER_AGENT_HOST` and `JAEGER_AGENT_PORT`.

## Error Handling

If a stage raises an exception:

1. The span captures the exception via `span.record_exception(e)`
2. The status attribute is set to `"error"`
3. The span closes with the error recorded
4. Execution either continues (if the pipeline tolerates the failure) or halts, propagating the exception up

This ensures that even failed stages are visible in Jaeger for debugging.

## Cost Tracking

Each stage that spawns an Agent (via Task) should log its estimated cost as a span attribute:

```python
with tracer.start_as_current_span("stage_name") as span:
    span.set_attribute("stage", "stage_name")
    span.set_attribute("cost_usd", 0.12)  # estimated or actual
    # ... run stage ...
```

The root trace can then sum all child span costs to emit a total cost summary to the user.

## Observability Best Practices

1. **Always initialize the tracer** at SKILL invocation start (`init_tracer("one-shot-generate")`)
2. **Wrap all stage calls** with `@trace_stage(stage_name)` or explicit `with tracer.start_as_current_span(...)`
3. **Propagate context to Tasks** by capturing and restoring span context across process boundaries
4. **Set meaningful attributes** on each span (entity count, file count, test results, cost)
5. **Never swallow exceptions** — record them and re-raise to preserve error visibility

## Testing Span Emission

Run the test suite to verify span propagation:

```bash
pytest tests/test_observability_traces.py -v
```

This validates:
- All 9 stages emit spans
- Span nesting is correct
- Exception recording works
- Jaeger export succeeds (if agent is running)
