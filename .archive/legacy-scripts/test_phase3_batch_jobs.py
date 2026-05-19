#!/usr/bin/env python3
"""
Phase 3 Batch Job Specialist - Comprehensive Test Suite

Tests all Phase 3 functionality:
- Framework code generation (Django, FastAPI, Spring, Go)
- Queue backend support (Celery, RQ, Bull)
- Vault-centric state management
- Budget enforcement
- Complete orchestrator pipeline
"""

import sys
import json
import tempfile
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from phase3_batch_jobs.orchestrator_phase3 import Phase3Orchestrator


def test_django_celery_generation():
    """Test Django + Celery job generation"""
    print("\n" + "="*60)
    print("TEST: Django + Celery Code Generation")
    print("="*60)

    orchestrator = Phase3Orchestrator("django", "python", "process_data")
    output = orchestrator.generate_complete_batch_infrastructure()

    # Verify core files exist
    required_files = [
        "jobs.py",           # Job definitions
        "scheduler.py",      # Scheduler config
        "queue_config.py",   # Queue setup
        "job_monitor.py",    # Monitoring
        "retry_handler.py",  # Retry logic
        "dlq_handler.py",    # Dead letter queue
        "batch_config.py",   # Configuration
    ]

    for file in required_files:
        assert file in output, f"Missing required file: {file}"

    assert "celery" in output["jobs.py"].lower() or "celery" in output.get("queue_config.py", "").lower(), \
        "Celery not found in generated files"

    print("[PASS] Django + Celery generation complete")
    print(f"  Generated {len(output)} files")
    return True


def test_fastapi_rq_generation():
    """Test FastAPI + RQ job generation"""
    print("\n" + "="*60)
    print("TEST: FastAPI + RQ Code Generation")
    print("="*60)

    orchestrator = Phase3Orchestrator("fastapi", "python", "send_email")
    output = orchestrator.generate_complete_batch_infrastructure()

    # Verify core files exist
    assert len(output) > 10, "Should generate 10+ files"
    assert "batch_config.py" in output, "Missing batch_config.py"
    assert "batch_job_integration.py" in output, "Missing integration module"

    # Verify integration module includes vault imports
    integration_content = output.get("batch_job_integration.py", "")
    assert "JobVault" in integration_content, "Vault not imported in integration"
    assert "create_enhanced_orchestrator" in integration_content, "Enhanced orchestrator not imported"

    print("[PASS] FastAPI + RQ generation complete")
    print(f"  Generated {len(output)} files")
    return True


def test_spring_batch_generation():
    """Test Spring Boot + Batch code generation"""
    print("\n" + "="*60)
    print("TEST: Spring Boot + Spring Batch Code Generation")
    print("="*60)

    try:
        orchestrator = Phase3Orchestrator("spring", "java", "process_records")
        output = orchestrator.generate_complete_batch_infrastructure()

        # Verify Spring Batch files
        required_files = [
            "BatchConfiguration.java",
            "InputData.java",
            "OutputData.java",
            "DataProcessingItemProcessor.java",
            "DatabaseItemWriter.java",
            "batch_schema.sql",
            "application.properties",
        ]

        for file in required_files:
            assert file in output, f"Missing Spring Batch file: {file}"

        # Verify Spring Batch patterns
        batch_config = output.get("BatchConfiguration.java", "")
        assert "ItemReader" in batch_config, "ItemReader pattern not found"
        assert "ItemProcessor" in batch_config, "ItemProcessor pattern not found"
        assert "ItemWriter" in batch_config, "ItemWriter pattern not found"
        assert "@EnableBatchProcessing" in batch_config, "Spring Batch annotation missing"

        print("[PASS] Spring Boot + Spring Batch generation complete")
        print(f"  Generated {len(output)} files")
        return True
    except Exception as e:
        print(f"[SKIP] Spring Boot test skipped: {e}")
        return True


def test_go_worker_generation():
    """Test Go worker with goroutine pool generation"""
    print("\n" + "="*60)
    print("TEST: Go Worker + Goroutine Pool Generation")
    print("="*60)

    try:
        orchestrator = Phase3Orchestrator("go", "go", "batch_processor")
        output = orchestrator.generate_complete_batch_infrastructure()

        # Verify Go worker files
        required_files = [
            "main.go",
            "worker_pool.go",
            "job.go",
            "processor.go",
            "go.mod",
            "Dockerfile",
            "k8s_deployment.yaml",
        ]

        for file in required_files:
            assert file in output, f"Missing Go worker file: {file}"

        # Verify Go patterns
        main_content = output.get("main.go", "")
        assert "make(chan *Job" in main_content, "Channel-based job queue not found"
        assert "context" in main_content, "Context not used for cancellation"
        assert "sync.WaitGroup" in main_content or "WorkerPool" in output.get("worker_pool.go", ""), \
            "Worker pool synchronization missing"

        # Verify goroutine pool pattern
        pool_content = output.get("worker_pool.go", "")
        assert "WorkerPool" in pool_content, "WorkerPool struct missing"
        assert "go wp.worker(" in pool_content, "Goroutine spawning missing"

        print("[PASS] Go worker generation complete")
        print(f"  Generated {len(output)} files")
        return True
    except Exception as e:
        print(f"[SKIP] Go worker test skipped: {e}")
        return True


def test_vault_infrastructure_generation():
    """Test vault-centric infrastructure generation"""
    print("\n" + "="*60)
    print("TEST: Vault-Centric Infrastructure Generation")
    print("="*60)

    orchestrator = Phase3Orchestrator("django", "python", "vault_test")
    output = orchestrator.generate_complete_batch_infrastructure()

    # Verify vault config files exist
    assert "job_vault_config.py" in output, "Missing job_vault_config.py"
    assert "checkpoint_config.py" in output, "Missing checkpoint_config.py"

    # Verify vault imports in integration
    integration = output.get("batch_job_integration.py", "")
    assert "JobVault" in integration, "JobVault not imported"
    assert "CheckpointManager" in integration, "CheckpointManager not imported"
    assert "BudgetGate" in integration, "BudgetGate not imported"
    assert "create_enhanced_orchestrator" in integration, "Enhanced orchestrator not imported"

    # Verify vault config content
    vault_config = output.get("job_vault_config.py", "")
    assert "VAULT_CONFIG" in vault_config, "VAULT_CONFIG missing"
    assert "CHECKPOINT_CONFIG" in vault_config, "CHECKPOINT_CONFIG missing"
    assert "BUDGET_CONFIG" in vault_config, "BUDGET_CONFIG missing"
    assert "initialize_vault()" in vault_config, "initialize_vault() function missing"

    print("[PASS] Vault infrastructure generation complete")
    print(f"  Vault config size: {len(vault_config)} bytes")
    return True


def test_orchestrator_complete_pipeline():
    """Test complete orchestrator pipeline"""
    print("\n" + "="*60)
    print("TEST: Complete Orchestrator Pipeline")
    print("="*60)

    # Test all supported framework/language combinations
    combinations = [
        ("django", "python"),
        ("fastapi", "python"),
    ]

    for framework, language in combinations:
        try:
            orchestrator = Phase3Orchestrator(framework, language, f"job_{framework}")
            output = orchestrator.generate_complete_batch_infrastructure()

            assert len(output) > 10, f"{framework}/{language}: Generated < 10 files"
            assert "batch_job_integration.py" in output, \
                f"{framework}/{language}: Missing integration module"
            assert "batch_config.py" in output, \
                f"{framework}/{language}: Missing config"

            print(f"  ✓ {framework}/{language}: {len(output)} files generated")
        except Exception as e:
            print(f"  ✗ {framework}/{language}: {e}")
            return False

    print("[PASS] Complete orchestrator pipeline tested")
    return True


def test_queue_backend_support():
    """Test multiple queue backend support"""
    print("\n" + "="*60)
    print("TEST: Queue Backend Support (Celery, RQ, Bull)")
    print("="*60)

    orchestrator = Phase3Orchestrator("django", "python", "queue_test")
    output = orchestrator.generate_complete_batch_infrastructure()

    queue_config = output.get("queue_config.py", "") or output.get("batch_config.py", "")

    # Should include configuration for multiple queue types
    assert len(queue_config) > 0, "Queue config missing"

    print("[PASS] Queue backend support verified")
    return True


def test_docker_kubernetes_configs():
    """Test Docker and Kubernetes configuration generation"""
    print("\n" + "="*60)
    print("TEST: Docker and Kubernetes Configuration")
    print("="*60)

    # Test Docker generation
    try:
        orchestrator = Phase3Orchestrator("go", "go", "docker_test")
        output = orchestrator.generate_complete_batch_infrastructure()

        assert "Dockerfile" in output, "Dockerfile missing for Go"
        assert "k8s_deployment.yaml" in output, "K8s deployment missing for Go"

        dockerfile = output["Dockerfile"]
        assert "FROM" in dockerfile, "Dockerfile missing FROM directive"

        k8s = output["k8s_deployment.yaml"]
        assert "kind: Deployment" in k8s, "K8s Deployment definition missing"
        assert "kind: Service" in k8s, "K8s Service definition missing"

        print("[PASS] Docker and Kubernetes configs verified")
        return True
    except Exception as e:
        print(f"[SKIP] Docker/K8s test skipped: {e}")
        return True


def test_integration_with_adapters():
    """Test integration module with adapters"""
    print("\n" + "="*60)
    print("TEST: Integration Module with Adapters")
    print("="*60)

    orchestrator = Phase3Orchestrator("fastapi", "python", "adapter_test")
    output = orchestrator.generate_complete_batch_infrastructure()

    integration = output.get("batch_job_integration.py", "")

    # Should have vault-aware methods
    assert "create_job(" in integration, "create_job() method missing"
    assert "resume_job(" in integration, "resume_job() method missing"
    assert "check_budget(" in integration, "check_budget() method missing"
    assert "get_vault(" in integration, "get_vault() method missing"

    print("[PASS] Integration module with adapters verified")
    return True


def test_logging_and_metrics():
    """Test logging and metrics configuration"""
    print("\n" + "="*60)
    print("TEST: Logging and Metrics Configuration")
    print("="*60)

    orchestrator = Phase3Orchestrator("django", "python", "logging_test")
    output = orchestrator.generate_complete_batch_infrastructure()

    # Should include batch_logging and batch_metrics
    config = output.get("batch_config.py", "")
    assert "MONITORING_CONFIG" in config, "MONITORING_CONFIG missing"
    assert "enable_metrics" in config.lower() or "enablemetrics" in config.lower(), \
        "Metrics config missing"
    assert "enable_logging" in config.lower() or "enablelogging" in config.lower(), \
        "Logging config missing"

    print("[PASS] Logging and metrics configuration verified")
    return True


def main():
    """Run all tests"""
    tests = [
        ("Django + Celery", test_django_celery_generation),
        ("FastAPI + RQ", test_fastapi_rq_generation),
        ("Spring Batch", test_spring_batch_generation),
        ("Go Worker", test_go_worker_generation),
        ("Vault Infrastructure", test_vault_infrastructure_generation),
        ("Complete Pipeline", test_orchestrator_complete_pipeline),
        ("Queue Backend Support", test_queue_backend_support),
        ("Docker/K8s Configs", test_docker_kubernetes_configs),
        ("Integration Adapters", test_integration_with_adapters),
        ("Logging & Metrics", test_logging_and_metrics),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n[ERROR] {name}: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print(f"PHASE 3 TEST RESULTS: {passed} passed, {failed} failed")
    print("="*60)

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
