---
type: reference
last_verified: 2026-05-18
owner: claude
---

# Aspirational Phase 4-5 Stubs (archived 2026-05-18)

These nine scripts were thin (<60 LOC) placeholders that produced a small
hardcoded string snippet via templating. The Tier 3.5 restructure moved
code generation from Python templates into Claude (the model) via the
agentic skill flow — see `docs/tier35-agentic.md`.

Archived rather than deleted so the design intent is preserved as a
reference for what each Phase 5 module should ultimately cover. The
replacement is: feed the *spec.json* to the **implementer** agent and let
Claude write code that's actually consistent with the user's codebase.

| File | What it was trying to do |
|---|---|
| phase5_advanced_caching.py | Cache key patterns, TTL tuning |
| phase5_blockchain_consensus.py | PoW/PoS consensus skeleton |
| phase5_content_delivery.py | CDN integration + cache headers |
| phase5_data_residency.py | GDPR data residency enforcement |
| phase5_edge_computing.py | Edge function deployment patterns |
| phase5_fraud_detection.py | Anomaly scoring stub |
| phase5_graphql_caching.py | Apollo persisted queries / cache |
| phase5_iot_patterns.py | MQTT / device-state patterns |
| phase5_request_deduplication.py | Idempotency-key handling |

If you need any of these capabilities, the new path is:

```bash
/one-shot "add CDN integration with edge caching" --project ./my-app
```

Which spawns the architect agent → spec.json → implementer agents →
verified, wired code. Better than a 30-line template, and adapted to the
user's actual project.
