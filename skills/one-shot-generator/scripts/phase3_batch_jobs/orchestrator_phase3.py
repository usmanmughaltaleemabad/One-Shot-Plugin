"""
Phase 3 Orchestrator - Batch Job Specialist Orchestration

Coordinates all Phase 3 modules to generate complete batch job infrastructure
"""

from typing import Dict, Any, List
import sys
import os

# Add core, generators, and handlers directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'generators'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'handlers'))

from job_generator import generate_job_code
from scheduler_generator import generate_scheduler
from queue_selector import generate_queue_selector
from job_monitor import generate_job_monitor
from result_handler import generate_result_handler
from retry_handler import generate_retry_handler
from dlq_handler import generate_dlq_handler
from job_router import generate_job_router
from worker_generator import generate_worker_code
from batch_logging import generate_batch_logging
from batch_metrics import generate_batch_metrics
from job_vault import JobVault, JobStatus, WorkLogEntry
from checkpoint_manager import CheckpointManager, ExponentialBackoffStrategy, CircuitBreakerStrategy
from budget_gate import BudgetGate, BudgetDecision
from enhanced_orchestrator import EnhancedOrchestrator, create_enhanced_orchestrator

# Generators (previously orphaned)
from cache_generator import generate_cache_generator
from database_generator import generate_database_models

# Handlers (previously orphaned)
from error_handler import generate_error_handler
from job_api_handler import generate_job_api_handler
from notification_handler import generate_notification_handler
from pipeline_handler import generate_pipeline_handler
from rate_limiting_handler import generate_rate_limiting_handler
from serialization_handler import generate_serialization_handler
from webhook_handler import generate_webhook_handler

# Framework-specific generators
try:
    from spring_batch_generator import generate_spring_batch
except ImportError:
    generate_spring_batch = None

try:
    from go_worker_generator import generate_go_worker
except ImportError:
    generate_go_worker = None

# Cloud backend generators (Phase 3.1)
try:
    from gcloud_tasks_generator import generate_gcloud_tasks
except ImportError:
    generate_gcloud_tasks = None

try:
    from aws_sqs_generator import generate_aws_sqs
except ImportError:
    generate_aws_sqs = None


class Phase3Orchestrator:
    """Orchestrate Phase 3 batch job generation"""

    def __init__(self, framework: str, language: str, job_name: str = None, queue_type: str = None):
        self.framework = framework
        self.language = language
        self.job_name = job_name or "default_job"
        self.queue_type = queue_type or "celery"  # Default to celery
        self.output = {}

    def generate_complete_batch_infrastructure(self) -> Dict[str, str]:
        """Generate all batch job infrastructure"""
        print(f"[Phase3] Generating batch job infrastructure for {self.framework}/{self.language}")
        print(f"[Phase3] Queue type: {self.queue_type}")

        # Route to cloud backend generators if specified
        if self.queue_type == "gcloud_tasks":
            if generate_gcloud_tasks is None:
                raise ImportError("gcloud_tasks_generator not available")
            print(f"[Phase3] Routing to Google Cloud Tasks generator")
            return generate_gcloud_tasks(self.framework, self.language, self.job_name)

        if self.queue_type == "sqs":
            if generate_aws_sqs is None:
                raise ImportError("aws_sqs_generator not available")
            print(f"[Phase3] Routing to AWS SQS generator")
            return generate_aws_sqs(self.framework, self.language, self.job_name)

        # Route to framework-specific generators if needed
        if self.framework == "spring" and self.language == "java":
            if generate_spring_batch is None:
                raise ImportError("spring_batch_generator not available")
            print(f"[Phase3] Routing to Spring Batch generator")
            return generate_spring_batch(self.framework, self.language, self.job_name)

        if self.framework == "go" and self.language == "go":
            if generate_go_worker is None:
                raise ImportError("go_worker_generator not available")
            print(f"[Phase3] Routing to Go Worker generator")
            return generate_go_worker(self.framework, self.language, self.job_name)

        # Continue with standard Python/Node generators for Django, FastAPI, NestJS
        # 1. Core job definitions
        print("  → Generating job definitions...")
        self.output.update(generate_job_code(
            self.framework,
            self.language,
            self.job_name,
            "celery" if self.language == "python" else "bull"
        ))

        # 2. Queue setup and detection
        print("  → Generating queue configuration...")
        self.output.update(generate_queue_selector(self.framework, self.language))

        # 3. Job scheduling
        print("  → Generating job scheduling...")
        self.output.update(generate_scheduler(self.framework, self.language))

        # 4. Job monitoring
        print("  → Generating job monitoring...")
        self.output.update(generate_job_monitor(self.framework, self.language))

        # 5. Result handling
        print("  → Generating result handling...")
        self.output.update(generate_result_handler(self.framework, self.language))

        # 6. Retry logic
        print("  → Generating retry strategies...")
        self.output.update(generate_retry_handler(self.framework, self.language))

        # 7. Dead letter queue
        print("  → Generating dead letter queue handling...")
        self.output.update(generate_dlq_handler(self.framework, self.language))

        # 8. Job routing
        print("  → Generating job routing...")
        self.output.update(generate_job_router(self.framework, self.language))

        # 9. Worker code
        print("  → Generating worker processes...")
        self.output.update(generate_worker_code(self.framework, self.language))

        # 10. Logging
        print("  → Generating structured logging...")
        self.output.update(generate_batch_logging(self.framework, self.language))

        # 11. Metrics
        print("  → Generating metrics collection...")
        self.output.update(generate_batch_metrics(self.framework, self.language))

        # 12. Cache layer
        print("  → Generating caching infrastructure...")
        self.output.update(generate_cache_generator(self.framework, self.language))

        # 13. Database models
        print("  → Generating database models...")
        self.output.update(generate_database_models(self.framework, self.language))

        # 14. Error handling
        print("  → Generating error handling...")
        self.output.update(generate_error_handler(self.framework, self.language))

        # 15. Job REST API
        print("  → Generating REST API endpoints...")
        self.output.update(generate_job_api_handler(self.framework, self.language))

        # 16. Notifications
        print("  → Generating notification handlers...")
        self.output.update(generate_notification_handler(self.framework, self.language))

        # 17. Task pipelines
        print("  → Generating task pipelines...")
        self.output.update(generate_pipeline_handler(self.framework, self.language))

        # 18. Rate limiting
        print("  → Generating rate limiting...")
        self.output.update(generate_rate_limiting_handler(self.framework, self.language))

        # 19. Serialization
        print("  → Generating serialization...")
        self.output.update(generate_serialization_handler(self.framework, self.language))

        # 20. Webhooks
        print("  → Generating webhook handlers...")
        self.output.update(generate_webhook_handler(self.framework, self.language))

        # 21. Vault-centric infrastructure (OneShot-inspired)
        print("  → Generating vault-centric state management...")
        self.output.update(self._generate_vault_infrastructure())

        # 22. Integration module
        print("  → Generating integration module...")
        self.output.update(self._generate_integration_module())

        # 23. Configuration
        print("  → Generating configuration...")
        self.output.update(self._generate_config())

        # 24. README
        print("  → Generating documentation...")
        self.output.update(self._generate_readme())

        print(f"[Phase3] Generated {len(self.output)} files")
        return self.output

    def _generate_vault_infrastructure(self) -> Dict[str, str]:
        """Generate vault-centric state management (OneShot-inspired)"""
        if self.language == "python":
            return {
                "job_vault_config.py": f'''"""
Job Vault Configuration - OneShot-inspired vault for batch job state
"""

from job_vault import JobVault, JobStatus
from checkpoint_manager import CheckpointManager, ExponentialBackoffStrategy
from budget_gate import BudgetGate, BudgetDecision
from enhanced_orchestrator import create_enhanced_orchestrator

# Vault configuration
VAULT_CONFIG = {{
    "vault_dir": "./job_vault",
    "archive_after_days": 30,
    "max_concurrent_jobs": 100,
    "enable_audit_trail": True,
    "enable_checkpointing": True,
}}

# Checkpoint configuration
CHECKPOINT_CONFIG = {{
    "strategy": "exponential_backoff",
    "base_delay": 5,
    "max_retries": 3,
    "retriable_errors": ["timeout", "temporary_failure", "resource_busy"],
    "circuit_breaker": {{
        "failure_threshold": 5,
        "recovery_timeout": 300,
    }},
}}

# Budget configuration
BUDGET_CONFIG = {{
    "enable_budgeting": True,
    "monthly_budget": 10000,
    "per_job_budget": 500,
    "warning_threshold": 0.80,
    "tracking_currency": "USD",
}}

# Vault initialization
def initialize_vault():
    """Initialize vault with configuration"""
    orchestrator = create_enhanced_orchestrator(
        vault_dir=VAULT_CONFIG["vault_dir"],
        framework="{self.framework}",
        language="{self.language}"
    )
    return orchestrator

# Export vault instance
vault = initialize_vault()
''',
                "checkpoint_config.py": f'''"""
Checkpoint Configuration - Job resumption and failure recovery
"""

from checkpoint_manager import CheckpointManager, ExponentialBackoffStrategy, CircuitBreakerStrategy

# Checkpoint strategies
STRATEGIES = {{
    "exponential_backoff": ExponentialBackoffStrategy(
        base_delay=5,
        max_retries=3,
        retriable_errors=["timeout", "temporary_failure", "resource_busy"]
    ),
    "circuit_breaker": CircuitBreakerStrategy(
        failure_threshold=5,
        recovery_timeout=300,
    ),
}}

# Checkpoint manager
CHECKPOINT_MANAGER = CheckpointManager(vault_dir="./job_vault")

# Resumption configuration
RESUMPTION_CONFIG = {{
    "auto_resume": True,
    "resume_timeout": 3600,
    "preserve_state": True,
    "max_resume_attempts": 3,
}}
'''
            }
        else:
            return {
                "vault-config.js": f'''"""
Vault Configuration - OneShot-inspired vault for batch job state
"""

export const VAULT_CONFIG = {{
    vaultDir: "./job_vault",
    archiveAfterDays: 30,
    maxConcurrentJobs: 100,
    enableAuditTrail: true,
    enableCheckpointing: true,
}};

export const CHECKPOINT_CONFIG = {{
    strategy: "exponential_backoff",
    baseDelay: 5,
    maxRetries: 3,
    retriableErrors: ["timeout", "temporary_failure", "resource_busy"],
    circuitBreaker: {{
        failureThreshold: 5,
        recoveryTimeout: 300,
    }},
}};

export const BUDGET_CONFIG = {{
    enableBudgeting: true,
    monthlyBudget: 10000,
    perJobBudget: 500,
    warningThreshold: 0.8,
    trackingCurrency: "USD",
}};

export const RESUMPTION_CONFIG = {{
    autoResume: true,
    resumeTimeout: 3600,
    preserveState: true,
    maxResumeAttempts: 3,
}};
'''
            }

    def _generate_integration_module(self) -> Dict[str, str]:
        """Generate integration module with vault support"""
        if self.language == "python":
            return {
                "batch_job_integration.py": f'''"""
Batch Job Integration - Central integration point for all batch job features
Includes OneShot-inspired vault-centric state management
"""

from queue_selector import QueueDetector, generate_queue_selector
from job_generator import generate_job_code
from scheduler_generator import generate_scheduler
from job_monitor import generate_job_monitor
from result_handler import generate_result_handler
from retry_handler import generate_retry_handler
from dlq_handler import generate_dlq_handler
from job_router import generate_job_router
from worker_generator import generate_worker_code
from batch_logging import generate_batch_logging
from batch_metrics import generate_batch_metrics

# Vault components
from job_vault import JobVault, JobStatus
from checkpoint_manager import CheckpointManager
from budget_gate import BudgetGate
from enhanced_orchestrator import create_enhanced_orchestrator

class BatchJobIntegration:
    """Central integration for all batch job features with vault support"""

    def __init__(self, framework="{self.framework}", language="{self.language}"):
        self.framework = framework
        self.language = language
        self.queue_type = QueueDetector.detect_from_codebase(".")

        # Initialize vault-centric orchestrator
        self.vault_orchestrator = create_enhanced_orchestrator(
            vault_dir="./job_vault",
            framework=framework,
            language=language
        )

    def get_queue_config(self):
        """Get queue configuration"""
        return QueueDetector.get_queue_config(self.queue_type, self.framework)

    def create_job(self, job_id, job_name, config=None, *args, **kwargs):
        """Create and enqueue a job with vault tracking"""
        # Create job in vault
        self.vault_orchestrator.create_job(job_id, config or {{}})

        # Enqueue task
        from job_router import route_task
        return route_task(job_name, *args, **kwargs)

    def resume_job(self, job_id):
        """Resume job from checkpoint"""
        return self.vault_orchestrator.resume_job(job_id)

    def monitor_job(self, job_id):
        """Get job monitor instance with vault state"""
        from job_monitor import JobMonitor
        return JobMonitor(job_id)

    def get_metrics(self):
        """Get current metrics from vault and monitoring"""
        from batch_metrics import get_batch_metrics
        return get_batch_metrics()

    def check_budget(self, job_id, estimated_cost):
        """Check budget before executing job"""
        return self.vault_orchestrator.budget_gate.can_execute(job_id, estimated_cost)

    def get_vault(self):
        """Get vault instance for direct access"""
        return self.vault_orchestrator.vault

integration = BatchJobIntegration()
'''
            }
        else:
            return {
                "batch_job_integration.js": f'''"""
Batch Job Integration - Central integration point
"""

import {{ QueueDetector, generateQueueSelector }} from './queue_selector.js';
import {{ generateJobCode }} from './job_generator.js';
import {{ generateScheduler }} from './scheduler_generator.js';
import {{ generateJobMonitor }} from './job_monitor.js';
import {{ generateResultHandler }} from './result_handler.js';
import {{ generateRetryHandler }} from './retry_handler.js';
import {{ generateDLQHandler }} from './dlq_handler.js';
import {{ generateJobRouter }} from './job_router.js';
import {{ generateWorkerCode }} from './worker_generator.js';

export class BatchJobIntegration {{
    constructor(framework = "{self.framework}", language = "{self.language}") {{
        this.framework = framework;
        this.language = language;
    }}

    async createJob(jobName, data, options = {{}}) {{
        return await enqueueTask(jobName, data, options);
    }}

    async monitorJob(jobId) {{
        return new JobMonitor(jobId);
    }}

    async getStats() {{
        return await getRoutingStats();
    }}
}}

export const integration = new BatchJobIntegration();
'''
            }

    def _generate_config(self) -> Dict[str, str]:
        """Generate configuration files"""
        if self.language == "python":
            return {
                "batch_config.py": f'''"""
Batch Job Configuration
"""

# Queue configuration
QUEUE_CONFIG = {{
    "broker_url": "redis://localhost:6379/0",
    "result_backend": "redis://localhost:6379/0",
    "task_serializer": "json",
    "timezone": "UTC",
}}

# Job defaults
JOB_DEFAULTS = {{
    "max_retries": 3,
    "timeout": 3600,
    "soft_time_limit": 3000,
    "time_limit": 3600,
}}

# Worker configuration
WORKER_CONFIG = {{
    "concurrency": 4,
    "pool": "prefork",
    "max_tasks_per_child": 1000,
    "log_level": "INFO",
}}

# Queue routing
QUEUE_ROUTING = {{
    "default": {{"priority": 5, "max_workers": 4}},
    "high_priority": {{"priority": 10, "max_workers": 2}},
    "low_priority": {{"priority": 1, "max_workers": 8}},
    "long_running": {{"priority": 5, "max_workers": 2, "timeout": 3600}},
}}

# DLQ configuration
DLQ_CONFIG = {{
    "max_retry_attempts": 5,
    "retry_delay": 3600,
}}

# Monitoring
MONITORING_CONFIG = {{
    "enable_metrics": True,
    "metrics_port": 8000,
    "enable_logging": True,
    "log_level": "INFO",
}}
'''
            }
        else:
            return {
                "batch_config.js": f'''"""
Batch Job Configuration
"""

export const QUEUE_CONFIG = {{
    redis: {{
        host: "localhost",
        port: 6379,
        db: 0,
    }},
    defaultJobOptions: {{
        attempts: 3,
        backoff: {{
            type: "exponential",
            delay: 2000,
        }},
    }},
}};

export const WORKER_CONFIG = {{
    concurrency: 4,
    maxStalled: 2,
}};

export const QUEUE_ROUTING = {{
    default: {{ priority: 5, concurrency: 4 }},
    highPriority: {{ priority: 10, concurrency: 2 }},
    lowPriority: {{ priority: 1, concurrency: 8 }},
    longRunning: {{ priority: 5, concurrency: 2 }},
}};

export const DLQ_CONFIG = {{
    maxRetryAttempts: 5,
    retryDelay: 3600000, // 1 hour
}};

export const MONITORING_CONFIG = {{
    enableMetrics: true,
    enableLogging: true,
    logLevel: "info",
}};
'''
            }

    def _generate_readme(self) -> Dict[str, str]:
        """Generate README documentation"""
        return {
            "BATCH_JOBS_README.md": f'''# Batch Job Specialist - Phase 3

Auto-generated batch job infrastructure for {self.framework} ({self.language}).

## Features

- **Job Queue Management**: {self.language.title()} with {self._get_queue_system()}
- **Job Scheduling**: Cron-based and one-time job scheduling
- **Job Monitoring**: Real-time job status tracking and progress reporting
- **Result Persistence**: Results stored in Redis with TTL management
- **Retry Logic**: Exponential backoff with jitter
- **Dead Letter Queue**: Failed job tracking and analysis
- **Load Balancing**: Intelligent queue routing based on priority and load
- **Worker Management**: Graceful shutdown and multi-process workers
- **Structured Logging**: JSON logs with full traceability
- **Metrics**: Prometheus metrics for monitoring

## Quick Start

### Configuration

Edit `batch_config.py` to configure:
- Queue broker (Redis, etc.)
- Worker concurrency
- Job timeouts
- Retry policies

### Running Workers

```bash
python worker.py
```

Workers will process jobs from configured queues.

### Enqueuing Jobs

```python
from batch_job_integration import integration

# Simple job
task = integration.create_job('process_data', arg1, arg2)

# With monitoring
monitor = integration.monitor_job(task.id)
result = monitor.wait_for_completion(timeout=3600)
```

### Monitoring

```python
# Get job status
monitor = integration.monitor_job(job_id)
print(monitor.get_status())

# Get metrics
metrics = integration.get_metrics()
```

## Architecture

```
Job Enqueue → Queue Router → Worker → Result Handler
              ↓
         Dead Letter Queue (on failure)
         ↓
         Retry Handler
         ↓
         Metrics + Logging
```

## Generated Files

- `jobs.py` - Job definitions
- `scheduler.py` - Scheduled jobs
- `job_monitor.py` - Job monitoring
- `result_handler.py` - Result management
- `retry_handler.py` - Retry strategies
- `dlq_handler.py` - Dead letter queue
- `job_router.py` - Queue routing
- `worker.py` - Worker process
- `batch_logging.py` - Structured logging
- `batch_metrics.py` - Metrics collection
- `batch_config.py` - Configuration
- `batch_job_integration.py` - Central integration

## Configuration Options

See `batch_config.py` for all available configuration options.

## Monitoring & Debugging

### View Metrics
```
http://localhost:8000/metrics
```

### View Logs
```
tail -f logs/*.log
```

### Monitor Queue Status
```python
from job_router import get_routing_stats
stats = get_routing_stats()
print(stats)
```

## Production Deployment

1. Use a managed Redis instance (Redis Cloud, ElastiCache, etc.)
2. Configure multiple workers across different machines
3. Set up monitoring with Prometheus + Grafana
4. Enable structured logging to a central log aggregation service
5. Configure Dead Letter Queue monitoring and alerts

## Support

For issues or questions, check the generated code comments and configuration defaults.
'''
        }

    def _get_queue_system(self) -> str:
        """Get queue system for language"""
        if self.language == "python":
            return "Celery"
        else:
            return "Bull"


def orchestrate_phase3(framework: str, language: str, job_name: str = None, queue_type: str = None) -> Dict[str, str]:
    """
    Orchestrate Phase 3 generation.

    Args:
        framework: django, fastapi, spring, go
        language: python, javascript, go, java
        job_name: name of the job
        queue_type: celery, rq, bull, gcloud_tasks, sqs (Phase 3.1)

    Returns: dict of {filename: code_content}
    """
    orchestrator = Phase3Orchestrator(framework, language, job_name, queue_type)
    return orchestrator.generate_complete_batch_infrastructure()


def orchestrate_phase3_enhanced(
    framework: str,
    language: str,
    job_name: str = None,
    vault_dir: str = "./job_vault",
    job_config: Dict[str, Any] = None,
    queue_type: str = None
) -> Dict[str, str]:
    """
    Phase 3 generation with OneShot vault + checkpoints + budget gate.

    Uses the enhanced orchestrator for stateful coordination with:
    - Persistent job state storage
    - Resumable execution from checkpoints
    - Budget enforcement and spending tracking
    - Complete audit trail of all operations

    Args:
        framework: django, fastapi, spring, go
        language: python, javascript, go, java
        job_name: name of the job
        vault_dir: directory for job vault
        job_config: job configuration (budget, timeouts, etc.)
        queue_type: celery, rq, bull, gcloud_tasks, sqs (Phase 3.1)

    Returns: dict of {filename: code_content}
    """
    orch = create_enhanced_orchestrator(framework, language, vault_dir)
    job_id = f"phase3-{framework}-{job_name or 'default'}"

    # Create job in vault
    orch.create_job(
        job_id,
        job_config or {"budget": 1000.0, "daily_limit": 500.0}
    )

    # Try resuming from checkpoint
    ctx = orch.resume_job(job_id)
    if ctx:
        print(f"[Enhanced] Resuming from checkpoint {ctx['checkpoint_id']}")

    # Execute Phase 3 generation with budget check
    success, files = orch.execute_with_budget_check(
        job_id=job_id,
        operation="phase3_generation",
        estimated_cost=0.0,
        executor_func=orchestrate_phase3,
        framework=framework,
        language=language,
        job_name=job_name
    )

    if success and files:
        # Create checkpoint
        orch.create_checkpoint(
            job_id,
            state={"files_generated": list(files.keys())}
        )

        # Complete job
        orch.complete_job(
            job_id,
            result={"status": "success", "files_count": len(files)}
        )

        print(f"[Enhanced] Job completed with audit trail")

    return files or {}
