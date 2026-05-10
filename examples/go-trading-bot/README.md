# Example: go-trading-bot

Low-latency Go service consuming `trade.executed` events from NATS,
applying a strategy, and emitting `order.submitted`. Demonstrates
goroutines + channels, structured logging with zap, and trading-domain
observability.

## Original prompt

```
/one-shot-prompting:one-shot-generator
Add a Go trading bot consumer for trade.executed events on NATS. Apply
a momentum strategy, emit order.submitted, observability for trading
domain (latency p99, fill rate, cost in basis points). @./
```

## Generated assumptions block (excerpt)

```
- Framework: net/http + nats-go (detected go.mod)
- Concurrency: goroutines + select on channels
- Logging: zap (detected in go.mod)
- Observability: prometheus client_golang + custom trading metrics
- Tests: stdlib testing + testify/assert
- Convention: gofmt + idiomatic err return values
```

## Files generated (7)

| File | Purpose | LOC |
|------|---------|-----|
| `cmd/bot/main.go` | entrypoint, wiring | 75 |
| `internal/strategy/momentum.go` | momentum logic | 90 |
| `internal/bus/nats.go` | NATS subscriber/publisher | 60 |
| `internal/metrics/trading.go` | Prometheus metrics | 45 |
| `internal/strategy/momentum_test.go` | unit tests | 110 |
| `Dockerfile` | distroless runtime | 25 |
| `Makefile` | build + test + lint | 30 |

## Run

```bash
make build
./bot --nats nats://localhost:4222
```
