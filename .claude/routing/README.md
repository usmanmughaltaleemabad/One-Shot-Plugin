# Intent-Based Routing System

Quick reference for the intent-based routing implementation.

## Quick Start

```python
from routing import IntentRouter

router = IntentRouter()
decision = router.route("Build a payment checkout with Stripe")

print(f"Intent: {decision.intent.value}")
print(f"Agent: {decision.agent_name}")
print(f"Cost: ${decision.cost_estimate}")
```

## Files

| File | Purpose | Lines |
|------|---------|-------|
| `intent_detector.py` | Intent/complexity/risk detection | 400+ |
| `intent_router.py` | Routing decision logic | 250+ |
| `routing_matrix.py` | Specialist agents & routing table | 250+ |
| `__init__.py` | Public API exports | 20 |
| `integration_example.py` | Integration with Stage 0.5 | 100+ |

## Intent Types

1. **simple_crud** — Single-entity CRUD ($0.10-0.30, 5 min)
2. **complex_multi_entity** — Multi-entity systems ($0.50-1.50, 15-20 min)
3. **real_time_system** → RealTimeSpecialist ($0.50-1.80, 20-25 min)
4. **payment_system** → PaymentSpecialist ($0.60-2.50, 25-30 min)
5. **api_design** → APIDesigner ($0.35-1.20, 15-18 min)
6. **admin_panel** → AdminDashboard ($0.40-1.40, 20-25 min)
7. **integration** → IntegrationSpecialist ($0.45-1.60, 20-25 min)
8. **data_pipeline** → DataPipelineSpecialist ($0.40-1.30, 18-22 min)

## Complexity Scoring

```
score = (entities × 2.0) + (relationships × 3.0) + (features × 0.8) + adjustments

low:        0-3
medium:     3-7
high:       7-12
enterprise: 12+
```

## Risk Levels

```
experimental:       Safe, low-risk features
standard:           Normal production features
production_critical: Payments, real-time, or complex systems
```

## Key Features

- **Deterministic:** No ML, pure keyword matching + scoring
- **Auditable:** All decisions logged to routing_trace.py
- **Extensible:** Easy to add new intent types or agents
- **Cost-aware:** Estimates cost and duration for each routing
- **Learning:** Similarity search from past decisions

## Testing

```bash
python -m pytest tests/test_intent_routing.py -v
# 49 tests, 100% pass rate
```

## Integration

Call before architect agent in Stage 0.5:

```python
from routing import IntentRouter
from scripts.routing_trace import get_or_create_trace

router = IntentRouter()
decision = router.route(user_request)

trace = get_or_create_trace(session_id, project_root)
trace.log_decision(
    stage='PLAN.Stage0.5',
    layer='L1_ROUTER',
    decision='route_intent',
    context={...},
    consequence=f'Route to {decision.agent_name}'
)
```

## Documentation

See `docs/routing/intent-based-routing.md` for complete documentation.

## Examples

```python
# Simple CRUD request
router.route("Create a User model with CRUD")
# -> Intent: simple_crud, Agent: SimpleCRUD, Cost: $0.30

# Complex multi-entity
router.route("E-commerce with Product, Order, Review entities")
# -> Intent: complex_multi_entity, Agent: ComplexDomain, Cost: $1.50

# Payment system
router.route("Stripe checkout integration")
# -> Intent: payment_system, Agent: PaymentSpecialist, Cost: $2.50

# Real-time system
router.route("Real-time notifications with WebSocket")
# -> Intent: real_time_system, Agent: RealTimeSpecialist, Cost: $1.80
```

## API Reference

### IntentRouter

```python
router = IntentRouter(knowledge_store_path=Path)

# Route a request
decision = router.route(request: str) -> RoutingDecision

# Find similar past requests
similar = router.find_similar_requests(request, top_k=3) -> List[str]

# Apply routing rules
agent_name = router.apply_rules(intent, complexity, risk) -> str

# Estimate cost
cost = router.estimate_cost(agent_spec, tokens_estimate=5000) -> float
```

### IntentDetector

```python
detector = IntentDetector()

# Full detection
result = detector.full_detection(request) -> DetectionResult

# Individual detections
intent = detector.detect_intent(request) -> IntentType
complexity = detector.detect_complexity(request, intent) -> ComplexityLevel
risk = detector.detect_risk(intent, complexity) -> RiskLevel
```

### RoutingDecision

```python
@dataclass
class RoutingDecision:
    request: str
    intent: IntentType
    complexity: ComplexityLevel
    risk: RiskLevel
    agent_name: str
    cost_estimate: float
    duration_estimate: float
    confidence: float
    entities_detected: List[str]
    features_detected: List[str]
    special_handling: List[str]
    similar_past_requests: List[str]
```

## Specialist Agents

| Agent | Cost | Duration | Best For |
|-------|------|----------|----------|
| SimpleCRUD | $0.10-0.30 | 5 min | Simple CRUD |
| ComplexDomain | $0.50-1.50 | 15-20 min | Multi-entity |
| RealTimeSpecialist | $0.50-1.80 | 20-25 min | WebSocket, live |
| PaymentSpecialist | $0.60-2.50 | 25-30 min | Stripe, payments |
| APIDesigner | $0.35-1.20 | 15-18 min | REST/GraphQL |
| AdminDashboard | $0.40-1.40 | 20-25 min | Dashboards, reports |
| IntegrationSpecialist | $0.45-1.60 | 20-25 min | External APIs |
| DataPipelineSpecialist | $0.40-1.30 | 18-22 min | Batch jobs, workers |

## Performance

- Detection: <1ms (keyword matching)
- Routing: O(1) (dictionary lookup)
- Similarity search: O(n) where n = past decisions
- Memory: ~1KB per decision
