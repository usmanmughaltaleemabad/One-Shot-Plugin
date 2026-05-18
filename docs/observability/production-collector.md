---
type: runbook
last_verified: 2026-05-18
owner: claude
---

# Production OpenTelemetry Collector Deployment

The [local guide](README.md) runs Jaeger + Prometheus in Docker for
development. This guide covers the **production** topology: deploy an
OpenTelemetry Collector between the plugin (or any generated app) and
your real observability backend.

## Why a collector?

Direct OTLP export from app → vendor backend works in dev. In production
it doesn't because:

| Concern | Direct export | Via collector |
|---|---|---|
| **Backend outage** | spans dropped, app retries thrash | collector queues, retries with backoff |
| **Backend swap** (Honeycomb → Datadog) | redeploy every app | reconfigure one collector |
| **Sampling decisions** | scattered across apps | centralised, tail-based possible |
| **PII / secret scrubbing** | re-implement per app | one processor for the whole fleet |
| **Cardinality control** | metrics fan out unboundedly | drop / aggregate at the edge |
| **Multi-backend** (trace to Honeycomb, metrics to Prometheus) | apps know both endpoints | collector routes |

The collector is the seam that decouples instrumentation from backend choice.

## Topology

Three deployment patterns. Pick one based on scale.

### Pattern A — Sidecar collector (recommended for ≤ 50 services)

```
[app] --OTLP localhost:4317--> [collector sidecar] --OTLP TLS--> [backend]
```

Each pod runs a collector sidecar. App-to-collector is `localhost`
(no TLS needed). Collector-to-backend is the only egress hop. Simpler
to reason about; collector failure only affects its own pod.

### Pattern B — Agent + Gateway (recommended for 50-1000 services)

```
[app] --OTLP--> [collector agent (DaemonSet)] --OTLP--> [collector gateway (Deployment)] --OTLP--> [backend]
```

Per-node agents handle batching + initial sampling. A small fleet of
gateway pods handles tail-based sampling, cross-trace correlation, and
the egress to the vendor. Lets you do tail-based sampling (look at the
whole trace before deciding whether to keep it) which is impossible from
the app.

### Pattern C — Direct (recommended for < 10 services, dev/staging only)

```
[app] --OTLP TLS--> [backend]
```

Skip the collector. Acceptable only when backend SLA + retry policies in
the SDK are enough. Most teams outgrow this within 6 months.

## Minimal production config

A working collector config for **Pattern A (sidecar)** that:
- accepts OTLP traces + metrics + logs
- batches before export (saves money on vendors that bill per request)
- limits memory so a vendor outage doesn't OOM the pod
- enforces a queue + retry policy
- exports to Honeycomb (swap the exporter block for Datadog/Tempo/etc.)

```yaml
# /etc/otelcol/config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  # MUST come BEFORE batch in the pipeline — drops data when memory is tight
  # rather than letting the collector OOM.
  memory_limiter:
    check_interval: 1s
    limit_percentage: 80
    spike_limit_percentage: 25

  # Adds k8s.* attributes by talking to the API server. Powers blast-radius
  # queries ("show me errors from this deployment in this namespace").
  k8sattributes:
    auth_type: serviceAccount
    extract:
      metadata:
        - k8s.namespace.name
        - k8s.deployment.name
        - k8s.pod.name
        - k8s.node.name

  # Adds resource attrs (service.name, service.version, deployment.environment).
  resource:
    attributes:
      - key: deployment.environment
        value: ${env:OTEL_ENV}
        action: upsert

  # PII / secret scrubbing — drop any span attribute matching these keys.
  # Add team-specific patterns here.
  attributes/scrub:
    actions:
      - key: http.request.header.authorization
        action: delete
      - key: http.request.header.cookie
        action: delete
      - key: db.statement
        action: hash      # keep the shape, lose the values

  # Always batch before exporting — cuts vendor cost dramatically.
  batch:
    timeout: 5s
    send_batch_size: 8192
    send_batch_max_size: 10000

exporters:
  otlp/honeycomb:
    endpoint: api.honeycomb.io:443
    headers:
      x-honeycomb-team: ${env:HONEYCOMB_API_KEY}
    sending_queue:
      enabled: true
      num_consumers: 4
      queue_size: 5000
    retry_on_failure:
      enabled: true
      initial_interval: 5s
      max_interval: 30s
      max_elapsed_time: 300s

  # Always also enable the debug exporter at low verbosity so you can
  # confirm spans are flowing when you SSH into the box.
  debug:
    verbosity: basic
    sampling_initial: 2
    sampling_thereafter: 200

service:
  telemetry:
    logs:
      level: warn
    metrics:
      level: detailed
      address: 0.0.0.0:8888    # /metrics for Prometheus scraping
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, k8sattributes, resource, attributes/scrub, batch]
      exporters: [otlp/honeycomb, debug]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, k8sattributes, resource, batch]
      exporters: [otlp/honeycomb]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, k8sattributes, resource, attributes/scrub, batch]
      exporters: [otlp/honeycomb]
```

### Pipeline ordering matters

`memory_limiter → enrichment processors → scrubbing → batch → exporter`.
- `memory_limiter` first so it can shed load before any work is done.
- Enrichment (k8sattributes, resource) before scrubbing so the scrubber
  can act on the enriched attrs if needed.
- `batch` last in the processor chain so exporters always see batches.

## Sampling strategy

Three options, pick one per pipeline.

### Head-based (cheapest, cardinality-blind)

Apply at the SDK in the app (`OTEL_TRACES_SAMPLER=parentbased_traceidratio`,
`OTEL_TRACES_SAMPLER_ARG=0.1` keeps 10%). Simple, but you can't decide
based on what happens in the trace.

### Tail-based (correct, more expensive)

Run in the gateway collector with `tail_sampling` processor. Decide
*after* seeing the whole trace whether to keep it. Required if you want
"always keep error traces, sample 1% of successes".

```yaml
processors:
  tail_sampling:
    decision_wait: 10s
    num_traces: 50000
    policies:
      - name: errors
        type: status_code
        status_code: { status_codes: [ERROR] }
      - name: slow
        type: latency
        latency: { threshold_ms: 1000 }
      - name: probabilistic-success
        type: probabilistic
        probabilistic: { sampling_percentage: 1 }
```

### Service-specific

Different pipelines per service via routing connector. Worth it only
when one service dominates volume.

## Kubernetes manifests

### Sidecar (Pattern A)

```yaml
# Inject this container alongside every app container.
- name: otel-collector
  image: otel/opentelemetry-collector-contrib:0.95.0
  args: ["--config=/conf/config.yaml"]
  resources:
    requests: { cpu: 100m, memory: 256Mi }
    limits:   { cpu: 500m, memory: 512Mi }
  ports:
    - containerPort: 4317   # OTLP gRPC
    - containerPort: 4318   # OTLP HTTP
    - containerPort: 8888   # collector self-metrics
  volumeMounts:
    - { name: otel-config, mountPath: /conf }
  env:
    - { name: OTEL_ENV,         value: production }
    - { name: HONEYCOMB_API_KEY, valueFrom: { secretKeyRef: { name: honeycomb, key: api-key } } }
  livenessProbe:
    httpGet: { path: /, port: 13133 }
  readinessProbe:
    httpGet: { path: /, port: 13133 }
```

App container env:
```yaml
- { name: OTEL_EXPORTER_OTLP_ENDPOINT, value: http://localhost:4318 }
- { name: OTEL_SERVICE_NAME,           value: ${MY_SERVICE_NAME} }
```

### Gateway (Pattern B)

Deploy 3 replicas of the gateway as a regular Deployment behind a
ClusterIP service. Agent DaemonSet exports to that service. Gateway
runs the same config but with the tail-sampling processor enabled.

## SLOs for the collector itself

The collector is now in your hot path. Monitor it like any service:

| Signal | Source | Alert when |
|---|---|---|
| **Refused spans** (memory_limiter triggered) | `otelcol_processor_refused_spans` | > 1% over 5m |
| **Export failure rate** | `otelcol_exporter_send_failed_spans` | > 0.1% over 5m |
| **Queue saturation** | `otelcol_exporter_queue_size / queue_capacity` | > 0.8 sustained |
| **CPU pressure** | container CPU throttling | any throttling |
| **Backend latency** | `otelcol_exporter_sent_spans` rate stalls | RPS drops > 50% over 2m |

## Common pitfalls

- **No memory limit on the collector.** Vendor outage → queue fills →
  OOM kill → spans lost forever. `memory_limiter` is non-negotiable.

- **Forgetting the resource processor.** Backends rely on
  `service.name` + `service.version` + `deployment.environment` to
  partition data. Missing these means traces land in "unknown service"
  and you can't filter.

- **Batching disabled.** Vendors typically bill per-request OR per-event;
  unbatched 1-span requests cost 100x what batched 8k-span requests do.

- **Trusting client-side sampling alone.** A bug in the app SDK can flood
  the collector. Put a hard rate-limit / memory_limiter at the collector
  even with head-based sampling enabled.

- **No TLS to the backend.** OTLP carries production telemetry — auth
  tokens, request paths, sometimes PII. Use TLS, validate certs, rotate
  API keys.

- **Single collector replica in production.** The collector itself needs
  HA: ≥ 3 replicas behind a service, anti-affinity across nodes.

- **No queue persistence.** Default queue is in-memory; restart loses
  in-flight spans. For high-value telemetry add a file-backed queue:
  `sending_queue.storage: file_storage`.

## Backend-specific snippets

### Honeycomb

```yaml
exporters:
  otlp:
    endpoint: api.honeycomb.io:443
    headers: { x-honeycomb-team: ${env:HONEYCOMB_API_KEY} }
```

### Grafana Tempo + Mimir + Loki

```yaml
exporters:
  otlp/tempo:
    endpoint: tempo:4317
    tls: { insecure: true }
  prometheusremotewrite/mimir:
    endpoint: http://mimir:9090/api/v1/push
  otlphttp/loki:
    endpoint: http://loki:3100/otlp
```

### Datadog

```yaml
exporters:
  datadog:
    api:
      site: datadoghq.com
      key: ${env:DD_API_KEY}
```

### New Relic

```yaml
exporters:
  otlp/newrelic:
    endpoint: otlp.nr-data.net:4317
    headers: { api-key: ${env:NR_LICENSE_KEY} }
```

## Verifying the deployment

After applying:

```bash
# 1. Spans flowing?
kubectl logs deploy/otel-gateway -c otel-collector | grep "TracesExporter"

# 2. Self-metrics OK?
curl -s http://otel-collector:8888/metrics | grep -E 'otelcol_(processor_refused|exporter_send_failed)'

# 3. Backend received the spans?  (vendor-specific — Honeycomb example:)
curl -H "X-Honeycomb-Team: $HONEYCOMB_API_KEY" \
     "https://api.honeycomb.io/1/datasets/<dataset>/query" \
     -d '{"time_range":300,"granularity":60,"calculations":[{"op":"COUNT"}]}'

# 4. Plugin-side env wired?
env | grep OTEL_
```

## Pointer for `/one-shot`-generated apps

When the plugin emits a feature via `/one-shot`, the deterministic
hot-paths (extract_domain_model, scaffold_planner, generate_and_verify,
auto_patch, critic_runner) already emit `@traced` spans via
`lib/telemetry.py`. To capture them in the production collector:

```bash
export OSP_OTEL_ENABLED=1
export OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
export OTEL_SERVICE_NAME=one-shot-prompting
export OTEL_RESOURCE_ATTRIBUTES="deployment.environment=production,service.version=$(cat .claude-plugin/plugin.json | jq -r .version)"
```

For generated apps that use the `common/logging_setup` + tracing hints
from the body_hints catalogue, the same env vars wire them up
automatically — no per-app collector config needed.

## See also

- [Local stack (Jaeger + Prometheus)](README.md)
- [OpenTelemetry Collector docs](https://opentelemetry.io/docs/collector/)
- [docs/scorecard-v4.md](../scorecard-v4.md) — observability dimension
