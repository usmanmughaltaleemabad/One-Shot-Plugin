---
type: runbook
last_verified: 2026-05-18
owner: claude
---

# Local Observability Stack

Run Jaeger + Prometheus locally so the plugin's OpenTelemetry spans land
somewhere visible.

> **For production:** see [production-collector.md](production-collector.md)
> — covers sidecar vs gateway topologies, memory_limiter, tail-based
> sampling, PII scrubbing, queue persistence, vendor-specific exporter
> snippets (Honeycomb / Grafana / Datadog / New Relic), and collector SLOs.

## 1. Start the stack

```bash
docker compose -f docs/observability/docker-compose.yml up -d
```

Verify:
- Jaeger UI: http://localhost:16686
- Prometheus: http://localhost:9090
- OTLP HTTP: http://localhost:4318 (where the plugin sends spans)
- OTLP gRPC: http://localhost:4317

## 2. Install otel-sdk in the plugin's venv

```bash
pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
```

## 3. Enable tracing in the plugin

```bash
export OSP_OTEL_ENABLED=1
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_SERVICE_NAME=one-shot-prompting
```

## 4. Generate traces

Run any plugin command — every `@traced` decorator hit emits a span.

```bash
python skills/one-shot-generator/scripts/one_shot_orchestrator.py \
    "shopping cart with line items, discounts" --project ./fastapi-shop
```

## 5. Inspect

Open http://localhost:16686, select service `one-shot-prompting`, and you'll see:
- `extract_domain_model` (with attrs: entities_count, confidence, intent)
- `scaffold_plan` (with framework attr)
- `verify_directory` (with sandbox attr)
- `auto_patch` (with sandbox attr)
- `auto_wire` (with framework + dry_run attrs)
- `critic_run_pytest` (with pattern attr)

## What to look for

| Trace pattern | Diagnosis |
|---|---|
| `verify_directory` > 2s | Too many files in sandbox, or syntax-check bottleneck |
| `critic_run_pytest` > 30s | pytest collecting too broadly; consider --pattern |
| `auto_patch` runs N times | Loop iterating — check for patch rule conflict |
| `extract_domain_model` confidence < 0.55 | Clarification gate should have fired |

## Tear down

```bash
docker compose -f docs/observability/docker-compose.yml down -v
```

## Production deploy

For production, replace `jaegertracing/all-in-one` with a managed
collector (Honeycomb, Datadog, Grafana Tempo). The plugin's OTLP
exporter accepts the standard `OTEL_EXPORTER_OTLP_ENDPOINT` env so
swapping is one-line.
