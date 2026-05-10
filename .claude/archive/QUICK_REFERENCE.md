# Quick Reference — OneShot Integration Modules

## Module Imports

```python
# Job state management
from core.job_vault import JobVault, JobStatus, WorkLogEntry

# Resumable execution
from core.checkpoint_manager import (
    CheckpointManager, 
    ExponentialBackoffStrategy,
    CircuitBreakerStrategy
)

# Budget controls
from core.budget_gate import BudgetGate, BudgetDecision

# Orchestration
from core.enhanced_orchestrator import create_enhanced_orchestrator
```

## Job Vault Cheat Sheet

### Create & Get Job

```python
vault = JobVault("./job_vault")

# Create
vault.create_job("job-id-123", {"budget": 100.0}, "django", "python")

# Get manifest
manifest = vault.get_job_manifest("job-id-123")
```

### Work Log (Append-Only)

```python
# Log action
vault.append_work_log("job-123", WorkLogEntry(
    timestamp="2026-05-09T14:30:45Z",
    agent="my-agent",
    action="process_step",
    result="SUCCESS",
    checkpoint={"items_processed": 100},
    error=None
))

# Get work log
work_log_content = vault._read_markdown(
    Path("./job_vault/jobs/job-123/work_log.md")
)
```

### Checkpoints

```python
# Create checkpoint
vault.create_checkpoint("job-123", {
    "current_step": 5,
    "processed_count": 100,
    "next_id": 101
})

# Resume from checkpoint
state = vault.resume_from_checkpoint("job-123")
if state:
    print(f"Resuming: {state}")
```

### Results & Artifacts

```python
# Store result
vault.store_result("job-123", "output_files", {
    "models.py": "...",
    "views.py": "..."
})

# Get result
files = vault.get_result("job-123", "output_files")
```

### Decisions

```python
# Record strategic decision
vault.record_decision(
    "job-123",
    decision="Redis over RabbitMQ",
    rationale="Already deployed in infrastructure",
    alternatives_considered=["RabbitMQ", "SQS"],
    chosen_option="Redis",
    impact="Zero new dependencies, integrates with existing monitoring"
)
```

## Checkpoint Manager Cheat Sheet

### Resumption

```python
cm = CheckpointManager("./job_vault")

# Check if can resume
if cm.can_resume("job-123"):
    ctx = cm.get_resumption_context("job-123")
    # ctx = {
    #     "checkpoint_id": 1,
    #     "timestamp": "2026-05-09T14:30Z",
    #     "state": {...},
    #     "retry_count": 0
    # }
```

### Retry Strategy

```python
# Exponential backoff
strategy = ExponentialBackoffStrategy(
    base_delay=5,                    # Start 5s
    max_retries=3,                   # Max 3 attempts
    retriable_errors=["timeout", "resource_busy"]
)

# Check if should retry
if strategy.should_retry("timeout", retry_count=1):
    delay = strategy.get_delay(retry_count=1)  # 10s (5 * 2^1)
    time.sleep(delay)
    retry()

# Mark for retry
cm.mark_retry("job-123", "Timeout error")
```

### Circuit Breaker

```python
# Fail fast on cascade
breaker = CircuitBreakerStrategy(
    failure_threshold=5,      # Open after 5 failures
    success_threshold=2,      # Close after 2 successes
    timeout_seconds=60        # Wait 60s before retry
)

if breaker.should_retry(error, retry_count):
    delay = breaker.get_delay(retry_count)
```

## Budget Gate Cheat Sheet

### Check Budget

```python
gate = BudgetGate("./job_vault")

# Check if operation OK
decision, reason = gate.check_operation_cost(
    job_id="job-123",
    operation="generate_code",
    estimated_cost=25.50,
    approval_required_above=50.0  # Needs approval if > $50
)

if decision == BudgetDecision.APPROVED:
    execute_operation()
elif decision == BudgetDecision.NEEDS_APPROVAL:
    gate.require_approval(
        "job-123", "generate_code", reason, "human"
    )
    wait_for_approval()
elif decision == BudgetDecision.DENIED:
    print(f"Over budget: {reason}")
elif decision == BudgetDecision.PAUSED_BUDGET_LIMIT:
    gate.set_pause_on_budget_limit("job-123")
```

### Record Spending

```python
# Log operation cost
gate.record_operation(
    job_id="job-123",
    operation="generate_code",
    actual_cost=24.75,
    description="Generated 3 Django models"
)

# Get summary
summary = gate.get_job_spending_summary("job-123")
# {
#     "job_id": "job-123",
#     "budget": 100.0,
#     "total_spent": 24.75,
#     "daily_limit": 50.0,
#     "daily_spent": 24.75,
#     "spending_by_operation": {"generate_code": 24.75},
#     "transaction_count": 1,
#     "last_operation": {...}
# }
```

### Spending Reports

```python
# All spending
report = gate.get_spending_report()
print(f"Total: ${report['total_spent']:.2f} across {report['total_jobs']} jobs")

# By date range
report = gate.get_spending_report(
    start_date="2026-05-01T00:00:00Z",
    end_date="2026-05-09T23:59:59Z"
)
```

## Enhanced Orchestrator Cheat Sheet

### Basic Flow

```python
orch = create_enhanced_orchestrator("django", "python", "./job_vault")

# 1. Create job
orch.create_job("job-123", {"budget": 100.0, "daily_limit": 50.0})

# 2. Resume if possible
if ctx := orch.resume_job("job-123"):
    print(f"Resuming from {ctx['checkpoint_id']}")

# 3. Execute with budget
success, result = orch.execute_with_budget_check(
    "job-123",
    operation="generate_models",
    estimated_cost=25.50,
    executor_func=generate_models,
    model_count=5
)

# 4. Create checkpoint
if success:
    orch.create_checkpoint("job-123", {"models": 5})

# 5. Handle failures
except Exception as e:
    failure = orch.handle_failure(
        "job-123",
        error=str(e),
        should_retry=True
    )

# 6. Record decisions
orch.record_decision(
    "job-123",
    decision="Generate models before views",
    rationale="Models are dependencies",
    alternatives=["Generate in parallel"],
    chosen="Sequential",
    impact="Ensures imports work"
)

# 7. Complete
orch.complete_job("job-123", {"status": "success", "files": 5})

# 8. Audit trail
audit = orch.get_job_audit_trail("job-123")
print(f"Work log:\n{audit['work_log']}")
print(f"Spending:\n{audit['spending']}")
```

### Job Status Updates

```python
# Get current status
manifest = orch.vault.get_job_manifest("job-123")
print(manifest["status"])  # created, queued, in_progress, checkpointed, completed, failed

# Update status
orch.vault.update_job_status("job-123", JobStatus.IN_PROGRESS, "Processing...")
```

### Listing & Monitoring

```python
# List all jobs
for job_summary in orch.list_jobs():
    print(f"{job_summary['job_id']}: {job_summary['status']} (${job_summary['total_cost']})")

# Get job details
summary = orch.vault.get_job_summary("job-123")
# {
#     "job_id": "job-123",
#     "status": "completed",
#     "created_at": "2026-05-09T14:00:00Z",
#     "last_update": "2026-05-09T14:45:00Z",
#     "checkpoints": 3,
#     "retry_count": 1,
#     "total_cost": 28.75
# }
```

## Common Patterns

### Pattern 1: Safe Execution with Checkpoint

```python
def safe_execute_with_checkpoint(
    job_id, operation, cost, func
):
    orch = create_enhanced_orchestrator()
    
    # Resume if possible
    orch.resume_job(job_id)
    
    # Execute with budget
    success, result = orch.execute_with_budget_check(
        job_id, operation, cost, func
    )
    
    # Always checkpoint on success
    if success:
        orch.create_checkpoint(job_id, {
            "completed_steps": ...,
            "results": result
        })
    
    return success, result
```

### Pattern 2: Graceful Failure Handling

```python
def execute_with_retry(job_id, operation, func):
    cm = CheckpointManager()
    
    try:
        return func()
    except Exception as e:
        failure = cm.create_failure_summary(job_id)
        
        if cm.should_retry(job_id, max_retries=3):
            cm.mark_retry(job_id, str(e))
            delay = cm.checkpoint_manager.retry_strategy.get_delay(
                failure["retry_count"]
            )
            print(f"Retrying in {delay}s...")
            time.sleep(delay)
            return execute_with_retry(job_id, operation, func)
        else:
            raise
```

### Pattern 3: Multi-Step Orchestration

```python
def orchestrate_workflow(job_config):
    orch = create_enhanced_orchestrator()
    job_id = f"workflow-{uuid.uuid4()}"
    
    orch.create_job(job_id, job_config)
    
    # Step 1: Generate models
    orch.execute_with_budget_check(
        job_id, "generate_models", 25.0, generate_models
    )
    orch.create_checkpoint(job_id, {"step": 1})
    
    # Step 2: Generate views
    orch.execute_with_budget_check(
        job_id, "generate_views", 25.0, generate_views
    )
    orch.create_checkpoint(job_id, {"step": 2})
    
    # Step 3: Generate serializers
    orch.execute_with_budget_check(
        job_id, "generate_serializers", 20.0, generate_serializers
    )
    orch.create_checkpoint(job_id, {"step": 3})
    
    orch.complete_job(job_id, {"status": "success"})
    return orch.get_job_audit_trail(job_id)
```

## Vault Structure Reference

```
job_vault/
├── jobs/
│   └── job-{id}/
│       ├── manifest.json          # Status, config, budget
│       ├── work_log.md            # Activity log
│       ├── decisions.md           # Decision records
│       ├── checkpoints/
│       │   ├── checkpoint-001.json
│       │   └── checkpoint-002.json
│       └── results/
│           ├── output_files.json
│           └── metrics.json
└── config/
    ├── global_spending.json       # All transactions
    ├── approvals.json            # Pending approvals
    └── admin_log.json            # Admin actions
```

## Error Handling

```python
# Check before resuming
if cm.validate_checkpoint_consistency("job-123"):
    # Safe to resume
    ctx = cm.get_resumption_context("job-123")
else:
    # Checkpoint corrupted
    print("Checkpoint validation failed, starting fresh")
    orch.create_job("job-123", {...})
```

## Testing

```python
# Test vault persistence
vault = JobVault("/tmp/test_vault")
vault.create_job("test-job", {})
manifest = vault.get_job_manifest("test-job")
assert manifest["job_id"] == "test-job"

# Test checkpoint resumption
vault.create_checkpoint("test-job", {"step": 5})
state = vault.resume_from_checkpoint("test-job")
assert state["step"] == 5

# Test budget enforcement
gate = BudgetGate("/tmp/test_vault")
decision, _ = gate.check_operation_cost(
    "test-job", "op", 50.0, approval_required_above=50.0
)
assert decision == BudgetDecision.NEEDS_APPROVAL
```

---

**Need help?** See `ONESHOT_INTEGRATION.md` for detailed examples and patterns.
