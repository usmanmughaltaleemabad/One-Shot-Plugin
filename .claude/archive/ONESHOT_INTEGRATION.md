# OneShot Integration Guide — Phase 3 Enhanced

This document shows how to integrate OneShot's powerful patterns into the Batch Job Specialist plugin.

## What's New

The Phase 3 core modules have been enhanced with **vault-centric architecture**, drawing directly from OneShot:

1. **Job Vault** (`job_vault.py`) - Persistent state store for jobs
2. **Checkpoint Manager** (`checkpoint_manager.py`) - Resumable execution
3. **Budget Gate** (`budget_gate.py`) - Spending controls & approvals
4. **Enhanced Orchestrator** (`enhanced_orchestrator.py`) - Stateful coordination

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Enhanced Orchestrator                  │
│  (stateful job coordination with vault-centric design)  │
└──────────┬──────────────────────────────────────────────┘
           │
     ┌─────┴──────────────────────────────┬─────────────────────────┐
     │                                    │                         │
┌────▼─────┐                    ┌─────────▼────┐         ┌──────────▼──────┐
│Job Vault  │                   │Checkpoint    │         │Budget Gate      │
│- State    │                   │Manager       │         │- Budget checks  │
│- Logs     │                   │- Resumption  │         │- Spending logs  │
│- Decisions│                   │- Retries     │         │- Approvals      │
└──────────┘                    └──────────────┘         └─────────────────┘
```

## Core Components

### 1. Job Vault — Persistent State Storage

Store all job state in a structured vault directory:

```
vault/
├── jobs/
│   ├── job-order-processor-001/
│   │   ├── manifest.json        (metadata, status, budget)
│   │   ├── work_log.md          (append-only activity log)
│   │   ├── decisions.md         (strategic decisions)
│   │   ├── checkpoints/
│   │   │   ├── checkpoint-001.json
│   │   │   └── checkpoint-002.json
│   │   └── results/
│   │       ├── job_result.json
│   │       └── generated_code.json
│   └── job-email-sender-002/...
├── config/
│   ├── budget.md                (spending limits)
│   ├── global_spending.json      (all transactions)
│   └── admin_log.json           (sensitive ops)
└── archive/                      (completed jobs)
```

**Usage:**

```python
from core.job_vault import JobVault

vault = JobVault("./job_vault")

# Create job
job_dir = vault.create_job(
    job_id="order-processor-001",
    job_config={
        "budget": 100.0,
        "daily_limit": 50.0,
        "max_retries": 3,
    },
    framework="django",
    language="python"
)

# Log activity (append-only)
from core.job_vault import WorkLogEntry
vault.append_work_log(
    "order-processor-001",
    WorkLogEntry(
        timestamp="2026-05-09T14:30:45Z",
        agent="queue-worker",
        action="process_task",
        result="SUCCESS",
        checkpoint={"processed_items": 100}
    )
)

# Create resumable checkpoint
vault.create_checkpoint(
    "order-processor-001",
    state={"last_processed_id": 100, "pending_count": 50}
)

# Record decision
vault.record_decision(
    "order-processor-001",
    decision="Use Redis for job queue",
    rationale="Celery requires broker, Redis is already deployed",
    alternatives_considered=["RabbitMQ", "SQS", "in-memory"],
    chosen_option="Redis + Celery",
    impact="Integrates with existing infrastructure"
)
```

### 2. Checkpoint Manager — Resumption & Retries

Resume jobs from failures without losing context:

```python
from core.checkpoint_manager import CheckpointManager

cm = CheckpointManager("./job_vault")

# Check if job can be resumed
if cm.can_resume("order-processor-001"):
    context = cm.get_resumption_context("order-processor-001")
    print(f"Resuming from checkpoint {context['checkpoint_id']}")
    print(f"Last state: {context['state']}")
    
    # Resume processing
    last_id = context['state']['last_processed_id']
    pending = context['state']['pending_count']

# Determine retry strategy
from core.checkpoint_manager import ExponentialBackoffStrategy

strategy = ExponentialBackoffStrategy(
    base_delay=5,      # Start with 5 second delay
    max_retries=3,     # Max 3 attempts
    retriable_errors=["timeout", "temporary_failure"]
)

if strategy.should_retry("timeout", retry_count=0):
    delay = strategy.get_delay(retry_count=0)  # 5s
    print(f"Retrying in {delay}s...")
    
if strategy.should_retry("timeout", retry_count=3):
    print("Max retries exceeded, will not retry")
```

### 3. Budget Gate — Spending Controls

Enforce budget limits and require approvals for high-cost operations:

```python
from core.budget_gate import BudgetGate, BudgetDecision

budget_gate = BudgetGate("./job_vault")

# Check if operation is within budget
decision, reason = budget_gate.check_operation_cost(
    job_id="order-processor-001",
    operation="generate_code",
    estimated_cost=25.50,
    approval_required_above=50.0
)

if decision == BudgetDecision.APPROVED:
    print(f"✓ Operation approved: {reason}")
elif decision == BudgetDecision.NEEDS_APPROVAL:
    print(f"⚠ Awaiting approval: {reason}")
    budget_gate.require_approval(
        job_id="order-processor-001",
        operation="generate_code",
        reason=reason,
        approver="human"
    )
elif decision == BudgetDecision.DENIED:
    print(f"✗ Operation denied: {reason}")
elif decision == BudgetDecision.PAUSED_BUDGET_LIMIT:
    print(f"⏸ Job paused: {reason}")
    budget_gate.set_pause_on_budget_limit("order-processor-001")

# Record spending
budget_gate.record_operation(
    job_id="order-processor-001",
    operation="generate_code",
    actual_cost=24.75,
    description="Generated 3 Django models with 15 fields"
)

# Get spending summary
summary = budget_gate.get_job_spending_summary("order-processor-001")
print(f"Spent: ${summary['total_spent']:.2f} / ${summary['budget']}")
print(f"Daily: ${summary['daily_spent']:.2f} / ${summary['daily_limit']}")
```

### 4. Enhanced Orchestrator — Stateful Coordination

Use the orchestrator to manage job lifecycle:

```python
from core.enhanced_orchestrator import create_enhanced_orchestrator

orchestrator = create_enhanced_orchestrator(
    framework="django",
    language="python",
    vault_dir="./job_vault"
)

# Create job
job_dir = orchestrator.create_job(
    job_id="order-processor-001",
    job_config={
        "budget": 100.0,
        "daily_limit": 50.0,
        "framework": "django",
        "language": "python",
    }
)

# Try to resume from previous run
resumption = orchestrator.resume_job("order-processor-001")
if resumption:
    print(f"Resumed from checkpoint {resumption['checkpoint_id']}")
else:
    print("Starting fresh")

# Execute with budget check
success, result = orchestrator.execute_with_budget_check(
    job_id="order-processor-001",
    operation="generate_code",
    estimated_cost=25.50,
    executor_func=my_code_generation_function,
    arg1="value1",
    arg2="value2"
)

if success:
    # Create checkpoint after successful operation
    orchestrator.create_checkpoint(
        "order-processor-001",
        state={
            "last_generated_file": result["filename"],
            "total_generated": 3,
        }
    )

# Handle failures gracefully
try:
    # ... operation fails ...
    raise TimeoutError("Code generation timed out")
except TimeoutError as e:
    failure_summary = orchestrator.handle_failure(
        "order-processor-001",
        error=str(e),
        should_retry=True
    )
    
    if failure_summary['status'] == 'will_retry':
        print(f"Retrying in {failure_summary['delay_seconds']}s")
    else:
        print(f"Terminal failure: {failure_summary}")

# Record decisions
orchestrator.record_decision(
    job_id="order-processor-001",
    decision="Generate Django models first, then views",
    rationale="Models are dependencies for views",
    alternatives=["Generate views first", "Generate in parallel"],
    chosen="Models first",
    impact="Ensures proper import dependencies"
)

# Complete job
orchestrator.complete_job(
    "order-processor-001",
    result={
        "status": "success",
        "files_generated": 5,
        "total_cost": 28.75,
    }
)

# Get full audit trail
audit = orchestrator.get_job_audit_trail("order-processor-001")
print(f"Work log:\n{audit['work_log']}")
print(f"Decisions:\n{audit['decisions']}")
```

## Integration with Phase 3 Generators

The enhanced components integrate seamlessly with existing Phase 3 generators:

```python
from orchestrator_phase3 import Phase3Orchestrator
from core.enhanced_orchestrator import create_enhanced_orchestrator

# Create enhanced orchestrator
enhanced_orch = create_enhanced_orchestrator("django", "python")

# Create job
job_dir = enhanced_orch.create_job("django-app-001", {
    "budget": 500.0,
    "daily_limit": 200.0,
})

# Use Phase 3 for code generation
phase3 = Phase3Orchestrator("django", "python", "process_orders")

# Execute Phase 3 with budget control
success, generated_files = enhanced_orch.execute_with_budget_check(
    job_id="django-app-001",
    operation="phase3_generation",
    estimated_cost=75.0,
    executor_func=phase3.generate_complete_batch_infrastructure
)

if success:
    # Store generated files as result
    enhanced_orch.vault.store_result(
        "django-app-001",
        "generated_files",
        generated_files
    )
    
    # Create checkpoint
    enhanced_orch.create_checkpoint(
        "django-app-001",
        state={
            "generated_file_count": len(generated_files),
            "modules": list(generated_files.keys()),
        }
    )
```

## Key Benefits

### 1. **Resumable Execution**
- Jobs can be resumed from checkpoints if they fail
- No need to restart from scratch
- Saves time and cost

### 2. **Full Auditability**
- Every action logged with timestamps
- Complete decision trail
- Spending transparency

### 3. **Budget Safety**
- Enforce spending limits per job, daily, monthly
- Require approval for high-cost operations
- Pause jobs when limits reached

### 4. **Intelligent Retries**
- Exponential backoff with jitter
- Circuit breaker pattern
- Configurable retriable errors

### 5. **Stateful Coordination**
- Jobs maintain state across sessions
- No context loss on failures
- Clear status transitions

## Migration Path

To integrate into your existing Phase 3 code:

1. **Create vault** for each job run
2. **Wrap Phase 3 orchestrator** with enhanced orchestrator
3. **Add checkpoints** at key decision points
4. **Log all operations** to work_log
5. **Track spending** through budget_gate

## File Structure

```
phase3_batch_jobs/
├── core/
│   ├── job_vault.py                 ← NEW: State storage
│   ├── checkpoint_manager.py        ← NEW: Resumption
│   ├── budget_gate.py              ← NEW: Spending controls
│   ├── enhanced_orchestrator.py    ← NEW: Stateful coordination
│   ├── batch_logging.py            (existing)
│   ├── batch_metrics.py            (existing)
│   └── ...
├── orchestrator_phase3.py           (existing)
├── phase3_runner.py                 (existing)
└── ONESHOT_INTEGRATION.md           ← this file
```

## Next Steps

1. **Test resumption** - Create job, checkpoint, restart, resume
2. **Test budget controls** - Try operations at budget limit
3. **Test audit trail** - Verify all operations are logged
4. **Integrate with handlers** - Use in Phase 3 handlers/integration generators
5. **Add monitoring** - Expose metrics for job status, spending

## See Also

- OneShot SYSTEM.md: https://github.com/oneshot-repo/OneShot/blob/main/SYSTEM.md
- Phase 3 README: `BATCH_JOBS_README.md`
- Budget configuration: `batch_config.py`
