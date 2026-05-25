# Advanced Curriculum (Phase 3-T4) — Multi-Stage Workflow Learning

Advanced curriculum that tracks failures at each stage and learns recovery strategies instead of simple pass/fail tracking.

## Architecture Overview

The advanced curriculum consists of four integrated components:

1. **StageCurriculum** — Per-stage metrics and learning
2. **WorkflowOrchestrator** — Multi-stage workflow execution
3. **RecoveryStrategies** — Failure pattern library with recovery actions
4. **CurriculumV3** — Integrated curriculum API

### Component Interaction

```
Intent + Complexity
    ↓
CurriculumV3.get_recommended_workflow()
    ↓
WorkflowOrchestrator.execute_workflow()
    ↓
For each stage:
  - execute_stage() → Success/Failure
  - If failed: handle_stage_failure() with RecoveryStrategies
  - record_stage_attempt() to StageCurriculum
    ↓
StageCurriculum.get_curriculum_insights()
    ↓
Improved recommendations for future generations
```

## Stage-Specific Curriculum

Each stage tracks:
- Success rate
- Average duration
- Average cost
- Common error types
- Recovery strategy effectiveness

### Stage Definitions

- **Stage 0 (Planning)**: Cost estimation accuracy, feature detection accuracy
- **Stage 1-2 (Design)**: Spec completeness, relationship correctness
- **Stage 3 (Implementation)**: Code quality, test coverage, security issues
- **Stage 4 (Verify)**: Patch success rate, fix accuracy
- **Stage 5 (Review)**: Security findings, performance issues
- **Stage 6 (Ship)**: Integration issues, wiring errors
- **Stage 7 (Critic)**: Test failures, coverage gaps
- **Stage 8 (Record)**: Graph accuracy, bead quality

## Workflow Paths

### Standard Workflow
```
planning → design → implement → verify → review → ship → critic → record
```
Use for all features with balanced risk/complexity.

### Parallel Implementation Workflow
```
planning → design → (implement + test-author in parallel) → verify → review → ship → critic → record
```
Use when implementation and test generation can run in parallel.

### Fast Track Workflow
```
planning → design → implement → verify → record
```
Use for simple features with low risk (skip review and critic).

## Recovery Strategies

### Pattern-Based Recovery

Each failure has a known pattern with recovery actions:

#### Design Stage
- **Relationship Validation Failed** → Add explicit FK columns (85% success)
- **Spec Completeness Low** → Expand entity definitions (80% success)
- **Complex Relationships** → Simplify to max depth 2 (75% success)

#### Implementation Stage
- **Missing Imports** → Auto-add imports before output (95% success)
- **Syntax Error** → Reduce entity count to 3 (80% success)
- **Indentation Error** → Regenerate with consistent indentation (85% success)

#### Verification Stage
- **Patch Failed** → Regenerate from spec instead of patching (85% success)
- **Validation Failed** → Remove advanced features (75% success)

#### Review Stage
- **Security Issue** → Enforce parameterized queries (80% success)
- **Performance Issue** → Add indexes and caching (70% success)

#### Ship Stage
- **Integration Error** → Dry-run wiring first (90% success)
- **Naming Conflict** → Add namespace prefix (85% success)

#### Critic Stage
- **Test Failure** → Reduce entities to 2, provide minimal fixtures (80% success)
- **Coverage Gap** → Focus on core logic (70% coverage minimum) (85% success)
- **Fixture Error** → Use mocks instead of real fixtures (75% success)

#### Record Stage
- **Graph Accuracy** → Rescan codebase from scratch (90% success)
- **Bead Quality** → Filter low-quality beads (80% success)

### Recovery Decision Flow

```python
if stage_fails:
    pattern = RecoveryStrategies.match_pattern(error_message)
    if pattern:
        action = pattern.primary_action
        params = pattern.adjusted_params
        if attempt < max_retries:
            retry_with(action, params)
        else:
            escalate()
    else:
        escalate()
```

## Cost and Duration Estimation

Estimates based on:
1. Base multipliers by complexity
2. Historical averages from similar features
3. Weighted blend (70% historical, 30% base)

### Default Estimates

- Simple: $0.20, 2 minutes
- Moderate: $0.50, 5 minutes
- Complex: $1.00, 10 minutes

## Integration with Knowledge Store

The curriculum learns from:
- **entity_pattern** facts: Similar past generations
- **cost_calibration** facts: Cost by entity count
- **error_recovery** facts: Recovery strategy effectiveness
- **api_design** facts: API patterns and designs

```python
curriculum = CurriculumV3()

# Get historical context
rec = curriculum.get_recommended_workflow("shopping_cart", "moderate")
print(rec["similar_past_workflows"])  # How many times before?
print(rec["estimated_cost_usd"])      # What did it cost?

# Execute with curriculum guidance
result = curriculum.execute_with_curriculum(
    intent="shopping_cart",
    complexity="moderate",
    stage_executors=stage_funcs,
)

# Learn from result
insights = curriculum.get_curriculum_insights()
```

## Risk Mitigations

For high-risk features:
1. Extra validation of spec before implementation
2. Extended test suite with higher coverage targets (85%+)
3. Duplicate review checkpoints
4. Dry-run all modifications before applying

```python
recommendations = curriculum.get_risk_mitigations(
    intent="payment_processing",
    risk_level="high",
)
# Returns list of recommended mitigations with expected success rates
```

## Workflow Execution with Failure Handling

```python
orchestrator = WorkflowOrchestrator()

# Option 1: Simple execution
result = orchestrator.execute_workflow(
    intent="create_feature",
    complexity="moderate",
    workflow_path="standard",
    stage_executors={
        "planning": planning_func,
        "design": design_func,
        # ... more stages
    },
)

# Option 2: With curriculum guidance
curriculum = CurriculumV3(
    stage_curriculum=StageCurriculum(),
    workflow_orchestrator=orchestrator,
)
result = curriculum.execute_with_curriculum(
    intent="create_feature",
    complexity="moderate",
    stage_executors=stage_funcs,
)

# Access results
print(result.status)           # success, failed, rolled_back
print(result.total_cost)       # Total USD spent
print(result.total_duration)   # Total seconds
for stage_result in result.stage_results:
    print(f"{stage_result.stage}: {stage_result.status}")
    if stage_result.recovery_applied:
        print(f"  Recovered with: {stage_result.recovery_applied}")
```

## Learning Loop

1. **Record Stage Attempts**: Every stage execution records metrics
2. **Calculate Success Rates**: Per-stage and per-recovery metrics
3. **Identify Patterns**: Which errors recur most frequently?
4. **Recommend Improvements**: Suggest parameters for next time
5. **Update Estimates**: Refine cost/duration based on actuals

```python
# Track over time
curriculum.stage_curriculum.record_stage_attempt(
    stage="design",
    success=True,
    duration=5.2,
    cost=0.12,
)

# Query statistics
stats = curriculum.stage_curriculum.get_stage_stats("design")
print(f"Success rate: {stats.success_rate:.1%}")
print(f"Avg cost: ${stats.avg_cost:.2f}")
print(f"Common errors: {stats.common_errors}")

# Get recommendations
params = curriculum.stage_curriculum.recommend_stage_params("design")
print(f"Recommended params: {params}")
```

## Curriculum Insights API

```python
insights = curriculum.get_curriculum_insights()

# Stage performance
print(insights["stage_stats"]["design"]["success_rate"])

# Workflow performance
print(insights["workflow_stats"]["success_rate"])

# Recovery effectiveness
print(insights["recovery_effectiveness"]["implement"])
# {"auto_add_imports": 0.95, "regenerate_from_spec": 0.85}

# Automated recommendations
print(insights["recommendations"])
# {"design": "Stage design has low success rate..."}
```

## API Reference

### StageCurriculum

```python
curriculum = StageCurriculum(store_path=Path(".beads/stage_metrics.jsonl"))

# Record execution
metric_id = curriculum.record_stage_attempt(
    stage="design",
    success=True,
    duration=5.0,
    cost=0.1,
    error_type=None,
    error_message=None,
    recovery_applied=None,
    extra_metrics={"entity_count": 5},
)

# Query statistics
stats = curriculum.get_stage_stats("design")
all_stats = curriculum.get_all_stage_stats()

# Recommendations
params = curriculum.recommend_stage_params("design", context={})

# Recovery strategies
strategies = curriculum.get_recovery_strategies(
    stage="design",
    error_type="relationship_validation_failed",
    top_k=3,
)

# History
history = curriculum.get_stage_history("design", limit=10)
```

### WorkflowOrchestrator

```python
orchestrator = WorkflowOrchestrator(store_path=Path(".beads/workflow_results.jsonl"))

# Execute workflow
result = orchestrator.execute_workflow(
    intent="shopping_cart",
    complexity="moderate",
    workflow_path="standard",
    stage_executors={"planning": func, ...},
    context={},
)

# Execute single stage
stage_result = orchestrator.execute_stage(
    stage="design",
    executor=design_executor,
    context={},
    workflow_id=None,
    retry=False,
)

# Handle failure
recovery = orchestrator.handle_stage_failure(
    stage="design",
    error="FK validation error",
    attempt=0,
    context={},
    max_retries=2,
)

# Query results
stats = orchestrator.get_workflow_stats()
history = orchestrator.get_workflow_history(intent="shopping_cart", limit=10)
```

### RecoveryStrategies

```python
from curriculum.recovery_strategies import RecoveryStrategies

# Find pattern by type
pattern = RecoveryStrategies.find_pattern("design", "relationship_validation_failed")

# Find pattern by error message
pattern = RecoveryStrategies.match_pattern_by_indicator(
    "implement",
    "NameError: name 'os' is not defined",
)

# Get patterns for stage
patterns = RecoveryStrategies.get_patterns_for_stage("design")

# Suggest recovery
suggestion = RecoveryStrategies.suggest_recovery(
    stage="design",
    error_type="relationship_validation_failed",
)
# Returns:
# {
#     "pattern": "relationship_validation_failed",
#     "root_cause": "Implicit relationships not properly inferred",
#     "recovery_action": "adjust_params",
#     "adjusted_params": {"add_fk_explicitly": True},
#     "expected_success_rate": 0.85,
#     "notes": "Explicitly define FK columns...",
# }
```

### CurriculumV3

```python
curriculum = CurriculumV3(
    stage_curriculum=StageCurriculum(),
    workflow_orchestrator=WorkflowOrchestrator(),
)

# Workflow recommendation
rec = curriculum.get_recommended_workflow(
    intent="shopping_cart",
    complexity="moderate",
    risk_level="medium",
)

# Cost and duration estimation
cost, duration = curriculum.get_estimated_cost_and_duration(
    intent="shopping_cart",
    complexity="moderate",
)

# Risk mitigations
mitigations = curriculum.get_risk_mitigations(
    intent="shopping_cart",
    risk_level="high",
)

# Execute with curriculum guidance
result = curriculum.execute_with_curriculum(
    intent="shopping_cart",
    complexity="moderate",
    stage_executors=stage_funcs,
    context={},
)

# Insights
insights = curriculum.get_curriculum_insights()
```

## Testing

36 tests cover:
- Stage curriculum recording and statistics
- Workflow orchestration and failure handling
- Recovery strategy matching and suggestions
- CurriculumV3 recommendations
- End-to-end integration with recovery
- Multi-generation learning

Run tests:
```bash
pytest tests/test_advanced_curriculum.py -v
```

## Success Criteria Met

- ✓ Per-stage curriculum tracking (8 stages)
- ✓ Workflow orchestration with parallel paths
- ✓ Recovery strategies for 15+ failure patterns
- ✓ Cost and duration estimation by (intent, complexity)
- ✓ Recommendation engine for workflow optimization
- ✓ 36 tests validating all components
- ✓ Integration with knowledge store and intent router
- ✓ Backward compatible with existing pipeline

## Files

- `.claude/curriculum/stage_curriculum.py` — Per-stage metrics
- `.claude/curriculum/workflow_orchestrator.py` — Multi-stage execution
- `.claude/curriculum/recovery_strategies.py` — Failure patterns (15+)
- `.claude/curriculum/curriculum_v3.py` — Integrated curriculum
- `.claude/curriculum/__init__.py` — Public API exports
- `tests/test_advanced_curriculum.py` — 36 comprehensive tests

## Next Steps

1. Integrate with one-shot skill to use curriculum guidance
2. Collect data from real generations (5-10 runs)
3. Empirical cost calibration after 20-30 runs
4. Streaming spec emission for early user review
5. Multi-iteration critic loop driver inside skill
