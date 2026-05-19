# Example: fastapi-rate-limiter

> [!NOTE]
> **This is an example *prompt*, not a runnable project.** The directory
> contains only this README — the file listing below describes what
> `/one-shot` would generate when run with the prompt against a real
> FastAPI codebase. To produce these files, run the prompt yourself.

FastAPI service with a sliding-window rate limiter on the message bus
side. Demonstrates async handlers, Redis storage, OpenTelemetry tracing,
and Prometheus metrics — all generated in one shot.

## Original prompt

```
/one-shot-prompting:one-shot-generator
Add a rate limiter for incoming `message.received` events: 10 msgs/min/user,
sliding window stored in Redis, drop excess and emit `rate.exceeded`,
include OTel + Prometheus, async, tests with pytest-asyncio. @./
```

## Generated assumptions block (excerpt)

```
- Framework: FastAPI 0.95 (detected main.py with FastAPI)
- Bus: aiokafka (detected aiokafka in requirements)
- Algorithm: sliding window log (best accuracy/cost tradeoff for 10/min)
- Storage: Redis ZSET keyed on user_id (TTL = 2 * window)
- Concurrency: async / await throughout
- Observability: opentelemetry-instrumentation-fastapi + prometheus_client
- Tests: pytest-asyncio + fakeredis
```

## Files generated (6)

| File | Purpose | LOC |
|------|---------|-----|
| `rate_limiter.py` | core RateLimiter class | 95 |
| `bus_glue.py` | wires limiter onto aiokafka consumer | 55 |
| `metrics.py` | Prometheus counters / histograms | 30 |
| `tests/test_rate_limiter.py` | unit + edge cases | 120 |
| `tests/test_bus_glue.py` | integration w/ fake bus | 70 |
| `README.md` | usage + tuning | 40 |

## How to reproduce

Run the prompt above against your own FastAPI project:

```bash
/one-shot-prompting:one-shot-generator "Add a rate limiter..." @./your-project
```

Then `uvicorn`, Redis, and `pytest` from the generated project root.
