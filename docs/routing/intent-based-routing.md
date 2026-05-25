# Intent-Based Routing — Phase 3-T3

Intelligent request-to-agent routing based on feature request intent, complexity, and risk level.

## Overview

Instead of routing all feature requests through a single agent pipeline, intent-based routing dispatches requests to specialized agents optimized for different categories of features:

- **Simple CRUD** requests → lightweight SimpleCRUD agent ($0.10-0.30, 5 min)
- **Complex multi-entity systems** → full-featured ComplexDomain agent ($0.50-1.50, 20 min)
- **Real-time systems** → WebSocket/async specialist ($0.50-1.80, 25 min)
- **Payment systems** → security-hardened PaymentSpecialist ($0.60-2.50, 30 min)
- **API design** → APIDesigner specialist ($0.35-1.20, 18 min)
- **Admin panels** → AdminDashboard specialist ($0.40-1.40, 22 min)
- **Integrations** → IntegrationSpecialist ($0.45-1.60, 24 min)
- **Data pipelines** → DataPipelineSpecialist ($0.40-1.30, 20 min)

## Intent Types

### simple_crud
Single-entity CRUD systems with basic operations.

**Examples:**
- "Create a User model with create, read, update, delete"
- "Build a product list with add, edit, remove"
- "Simple blog post manager"

**Characteristics:**
- Single entity or very simple relationships
- Basic CRUD operations
- No complex business logic
- Low complexity score

### complex_multi_entity
Systems with multiple entities and complex relationships.

**Examples:**
- "E-commerce with User, Product, Order, Review entities"
- "Build a project management system with Users, Projects, Tasks, Comments"
- "Shopping cart with line items, discounts, and inventory"

**Characteristics:**
- 3+ entities
- Has_many/many-to-many relationships
- Complex business logic
- Medium to high complexity score

### real_time_system
WebSocket, streaming, or live-update systems.

**Examples:**
- "Real-time notification system using WebSocket"
- "Live chat application with instant messaging"
- "Collaborative document editor with live updates"

**Characteristics:**
- Keywords: real-time, WebSocket, live, streaming, push, broadcast
- Always routes to RealTimeSpecialist
- Requires performance review
- High risk by default

### payment_system
Payment processing with Stripe or similar.

**Examples:**
- "Checkout system with Stripe integration"
- "Subscription management with recurring billing"
- "Invoice generation and payment tracking"

**Characteristics:**
- Keywords: payment, Stripe, transaction, billing, subscription, checkout
- **Always routes to PaymentSpecialist** regardless of complexity/risk
- Requires security review AND compliance check
- PCI compliance handling
- Production-critical by default

### api_design
REST or GraphQL API endpoint design.

**Examples:**
- "Design REST API with authentication and serializers"
- "Build GraphQL schema for user queries"
- "API endpoint for bulk operations with pagination"

**Characteristics:**
- Keywords: API, endpoint, REST, GraphQL, schema, serializer
- Routes to APIDesigner specialist
- Schema validation required
- Versioning strategy planning

### admin_panel
Admin dashboards, reporting, and management interfaces.

**Examples:**
- "Create admin dashboard with analytics and reporting"
- "Build user management interface with bulk operations"
- "Admin panel with charts and data visualization"

**Characteristics:**
- Keywords: dashboard, admin, reporting, analytics, visualization
- Routes to AdminDashboard specialist
- Performance review required (query optimization)
- Pagination strategy planning

### integration
Third-party API and webhook integrations.

**Examples:**
- "GitHub integration with OAuth and webhooks"
- "Sync data with external CRM API"
- "Slack bot with incoming webhooks"

**Characteristics:**
- Keywords: integration, external, API, OAuth, webhook, sync
- Routes to IntegrationSpecialist
- Security review required
- OAuth flow and webhook signature validation
- Rate limiting handling

### data_pipeline
Batch processing, scheduled jobs, and async workers.

**Examples:**
- "Batch processing pipeline with cron jobs"
- "Background worker for sending emails"
- "Daily report generation using scheduled tasks"

**Characteristics:**
- Keywords: pipeline, batch, job, cron, background, worker, async
- Routes to DataPipelineSpecialist
- Performance review required
- Job scheduling and error recovery
- Idempotency guarantees

## Complexity Levels

Complexity is calculated from multiple signals:

```
complexity_score = (entity_count × 2.0) 
                 + (relationship_count × 3.0)
                 + (feature_count × 0.8)
                 + (api_endpoint_count × 0.5)
                 + intent_adjustments
```

### low
- **Score:** 0-3
- **Characteristics:** 1-2 entities, minimal relationships, few features
- **Example:** "Create a User model with CRUD"
- **Agent:** SimpleCRUD (if intent matches)

### medium
- **Score:** 3-7
- **Characteristics:** 2-3 entities, some relationships, multiple features
- **Example:** "Blog system with User, Post, Comment entities"
- **Agent:** SimpleCRUD or ComplexDomain depending on intent

### high
- **Score:** 7-12
- **Characteristics:** 4+ entities, multiple relationships, rich features
- **Example:** "E-commerce with Product, Order, Review, Payment entities"
- **Agent:** Specialized agent (RealTime, Payment, etc.) or ComplexDomain

### enterprise
- **Score:** 12+
- **Characteristics:** 5+ entities, complex relationships, many features
- **Example:** "Multi-tenant SaaS platform with hierarchical relationships"
- **Agent:** Specialized agent or ComplexDomain with extended handling

## Risk Levels

Risk is determined by intent type and complexity:

```
risk_score = intent_base_score + complexity_adjustment
```

### experimental
- **Score:** 0-1.5
- **Characteristics:** Low-risk, simple feature, safe to ship fast
- **Example:** "Simple user CRUD"
- **Review:** Standard testing only

### standard
- **Score:** 1.5-3.5
- **Characteristics:** Normal production feature, moderate complexity
- **Example:** "Blog with User, Post, Comment"
- **Review:** Standard testing + code review

### production_critical
- **Score:** 3.5+
- **Characteristics:** High-risk: payments, real-time, or complex
- **Example:** "Stripe checkout", "Real-time notifications"
- **Review:** Security review, performance review, compliance check
- **Automatic flags:** Security review, possibly compliance check

## Specialist Agents

### SimpleCRUD
**When:** simple_crud + low/medium complexity + not high risk

- **Cost:** ~$0.10-0.30
- **Duration:** 5-10 min
- **Max iterations:** 2
- **Features:**
  - Lightweight reasoning
  - Fast execution
  - Single-entity focus

### ComplexDomain
**When:** complex_multi_entity, or complex_crud (high complexity)

- **Cost:** ~$0.50-1.50
- **Duration:** 15-20 min
- **Max iterations:** 5
- **Features:**
  - Full reasoning capability
  - Multi-entity handling
  - Relationship mapping
  - Schema derivation

### RealTimeSpecialist
**When:** real_time_system (always)

- **Cost:** ~$0.50-1.80
- **Duration:** 20-25 min
- **Max iterations:** 5
- **Special handling:**
  - async_validation
  - connection_pool_testing
- **Review required:** Performance review

### PaymentSpecialist
**When:** payment_system (always)

- **Cost:** ~$0.60-2.50
- **Duration:** 25-30 min
- **Max iterations:** 7
- **Special handling:**
  - pci_compliance_check
  - encryption_validation
  - token_handling
- **Review required:** Security review + Compliance check

### APIDesigner
**When:** api_design + medium/high complexity

- **Cost:** ~$0.35-1.20
- **Duration:** 15-20 min
- **Max iterations:** 4
- **Special handling:**
  - schema_validation
  - versioning_strategy

### AdminDashboard
**When:** admin_panel + medium/high complexity

- **Cost:** ~$0.40-1.40
- **Duration:** 20-25 min
- **Max iterations:** 4
- **Special handling:**
  - query_optimization
  - pagination_strategy
- **Review required:** Performance review

### IntegrationSpecialist
**When:** integration (all complexities)

- **Cost:** ~$0.45-1.60
- **Duration:** 20-25 min
- **Max iterations:** 5
- **Special handling:**
  - oauth_flow
  - webhook_signature_validation
  - rate_limiting
- **Review required:** Security review

### DataPipelineSpecialist
**When:** data_pipeline (all complexities)

- **Cost:** ~$0.40-1.30
- **Duration:** 18-22 min
- **Max iterations:** 4
- **Special handling:**
  - job_scheduling
  - error_recovery
  - idempotency
- **Review required:** Performance review

## Routing Matrix

Complete routing matrix: `(intent, complexity, risk) → agent`

Key patterns:

| Intent | Low | Medium | High | Enterprise |
|--------|-----|--------|------|------------|
| simple_crud | SimpleCRUD | SimpleCRUD→ComplexDomain | ComplexDomain | ComplexDomain |
| complex_multi_entity | ComplexDomain | ComplexDomain | ComplexDomain | ComplexDomain |
| real_time_system | RealTimeSpecialist | RealTimeSpecialist | RealTimeSpecialist | RealTimeSpecialist |
| **payment_system** | **PaymentSpecialist** | **PaymentSpecialist** | **PaymentSpecialist** | **PaymentSpecialist** |
| api_design | SimpleCRUD→APIDesigner | APIDesigner | APIDesigner | APIDesigner |
| admin_panel | SimpleCRUD→AdminDashboard | AdminDashboard | AdminDashboard | AdminDashboard |
| integration | IntegrationSpecialist | IntegrationSpecialist | IntegrationSpecialist | IntegrationSpecialist |
| data_pipeline | DataPipelineSpecialist | DataPipelineSpecialist | DataPipelineSpecialist | DataPipelineSpecialist |

## Usage

### Python API

```python
from .claude.routing import IntentRouter, RoutingMatrix, IntentDetector

# Option 1: Full routing decision
router = IntentRouter()
decision = router.route("Build a payment checkout with Stripe")

print(f"Intent: {decision.intent}")
print(f"Complexity: {decision.complexity}")
print(f"Risk: {decision.risk}")
print(f"Agent: {decision.agent_name}")
print(f"Cost estimate: ${decision.cost_estimate}")
print(f"Duration: {decision.duration_estimate} min")
print(f"Special handling: {decision.special_handling}")

# Option 2: Intent detection only
detector = IntentDetector()
result = detector.full_detection("Build a User model with CRUD")

print(f"Intent: {result.intent}")
print(f"Complexity: {result.complexity}")
print(f"Confidence: {result.confidence}")
print(f"Entities: {result.entities_detected}")
print(f"Features: {result.features_detected}")

# Option 3: Direct routing matrix lookup
agent = RoutingMatrix.get_agent(
    intent=IntentType.simple_crud,
    complexity=ComplexityLevel.low,
    risk=RiskLevel.experimental
)
print(f"Agent: {agent.name}")
print(f"Cost: ${agent.max_cost_estimate}")
```

### Integration with Stage 0.5

Call intent routing before the architect agent:

```python
from .claude.routing import IntentRouter
from scripts.routing_trace import get_or_create_trace

router = IntentRouter()
decision = router.route(user_request)

# Log the routing decision
trace = get_or_create_trace(session_id, project_root)
trace.log_decision(
    stage='PLAN.Stage0.5',
    layer='L1_ROUTER',
    decision='route_intent',
    context={
        'intent': decision.intent.value,
        'complexity': decision.complexity.value,
        'risk': decision.risk.value,
        'agent': decision.agent_name,
        'confidence': decision.confidence,
    },
    consequence=f'Route to {decision.agent_name} agent'
)

# Emit routing decision fact to knowledge store
knowledge_store.emit_fact(
    content=f"Request: {decision.request[:100]}... → {decision.agent_name} (intent={decision.intent}, risk={decision.risk})",
    fact_type="routing_decision"
)
```

## Adding Custom Intent Types

To add a new intent type:

1. **Add to IntentType enum** in `intent_detector.py`:
   ```python
   class IntentType(str, Enum):
       my_new_intent = "my_new_intent"
   ```

2. **Add keywords** to IntentDetector.INTENT_KEYWORDS:
   ```python
   INTENT_KEYWORDS = {
       IntentType.my_new_intent: {
           "keywords": ["keyword1", "keyword2"],
           "weight": 1.0,
       },
   }
   ```

3. **Create agent spec** in `routing_matrix.py`:
   ```python
   AGENTS = {
       "my_agent": AgentSpec(
           name="MyAgent",
           description="...",
           cost_per_token=0.40,
           max_iterations=5,
           max_cost_estimate=1.50,
           duration_estimate_minutes=20,
       ),
   }
   ```

4. **Add routing entries** to MATRIX in `routing_matrix.py`:
   ```python
   MATRIX = {
       (IntentType.my_new_intent, ComplexityLevel.low, RiskLevel.experimental): "my_agent",
       (IntentType.my_new_intent, ComplexityLevel.medium, RiskLevel.standard): "my_agent",
       # ... etc
   }
   ```

5. **Add tests** in `tests/test_intent_routing.py`

## Similarity Search

The router maintains a JSONL file of past routing decisions (`.beads/routing_decisions.jsonl`). When routing a new request, it searches for similar past requests using keyword overlap.

This enables:
- Learning from past decisions
- Consistency for similar features
- Drift detection (if similar requests get different routes over time)

## Confidence Scoring

Confidence (0.0-1.0) indicates how certain the detector is about the classification:

```
confidence = avg(keyword_match_ratio, request_detail_ratio)
```

- **0.0-0.3:** Vague request, high uncertainty
- **0.3-0.6:** Moderate specificity
- **0.6-1.0:** Clear, detailed request with high confidence

Low-confidence routing may warrant human review or prompting for clarification.

## Testing

Run full test suite:

```bash
python -m pytest tests/test_intent_routing.py -v
```

Test coverage:
- 8+ intent types (detection)
- Complexity detection (entity/relationship counting)
- Risk detection (security/compliance)
- Routing matrix correctness
- Cost and duration estimates
- Similarity search
- Routing stability
- 49 total tests, all passing
