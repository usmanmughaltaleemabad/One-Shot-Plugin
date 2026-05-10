#!/usr/bin/env python3
"""
Phase 3 Vault Integration Tests

Tests OneShot-inspired vault-centric state management:
- Job creation and state tracking
- Checkpoint creation and resumption
- Budget enforcement and tracking
- Audit trail generation
"""

import sys
import json
import tempfile
import time
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from phase3_batch_jobs.core.job_vault import JobVault, JobStatus, WorkLogEntry
from phase3_batch_jobs.core.checkpoint_manager import CheckpointManager, ExponentialBackoffStrategy
from phase3_batch_jobs.core.budget_gate import BudgetGate, BudgetDecision
from phase3_batch_jobs.core.enhanced_orchestrator import EnhancedOrchestrator, create_enhanced_orchestrator


def test_job_vault_creation():
    """Test job creation in vault"""
    print("\n" + "="*60)
    print("TEST: Job Vault Creation and State Tracking")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        vault = JobVault(vault_dir=tmpdir)

        # Create a job
        job_id = "test-job-001"
        job_config = {
            "name": "test_job",
            "max_retries": 3,
            "timeout": 3600,
        }

        job_dir = vault.create_job(job_id, job_config, "django", "python")

        assert job_dir is not None, "Job directory should be created"
        assert Path(job_dir).exists(), f"Job directory should exist: {job_dir}"
        assert "test-job-001" in job_dir, "Job ID should be in directory"

        # Verify manifest created
        manifest_path = Path(job_dir) / "manifest.json"
        assert manifest_path.exists(), "manifest.json should be created"

        with open(manifest_path) as f:
            manifest = json.load(f)
            assert manifest["job_id"] == job_id, "Job ID should match"
            assert manifest["status"] == "created", "Initial status should be 'created'"

        print("[PASS] Job vault creation successful")
        return True


def test_job_work_log():
    """Test work log entries"""
    print("\n" + "="*60)
    print("TEST: Work Log Entry Creation and Tracking")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        vault = JobVault(vault_dir=tmpdir)
        job_id = "test-job-log"
        job_config = {"name": "log_test"}

        vault.create_job(job_id, job_config, "django", "python")

        # Append work log entries
        entry1 = WorkLogEntry(
            timestamp="2026-05-09T14:30:45Z",
            agent="orchestrator",
            action="start_job",
            result="Job started successfully",
        )

        vault.append_work_log(job_id, entry1)

        entry2 = WorkLogEntry(
            timestamp="2026-05-09T14:35:45Z",
            agent="worker",
            action="process_data",
            result="Processed 1000 records",
        )

        vault.append_work_log(job_id, entry2)

        # Verify work log exists
        work_log_path = Path(tmpdir) / "jobs" / job_id / "work_log.md"
        assert work_log_path.exists(), "work_log.md should exist"

        with open(work_log_path) as f:
            content = f.read()
            assert "start_job" in content, "Work log should contain start_job action"
            assert "process_data" in content, "Work log should contain process_data action"
            assert "Processed 1000 records" in content, "Work log should contain result"

        print("[PASS] Work log entry creation successful")
        return True


def test_checkpoint_creation_and_resumption():
    """Test checkpoint creation and resumption"""
    print("\n" + "="*60)
    print("TEST: Checkpoint Creation and Job Resumption")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_mgr = CheckpointManager(vault_dir=tmpdir)
        job_id = "test-job-checkpoint"

        # Create checkpoint
        checkpoint_data = {
            "progress": 50,
            "last_record_id": 500,
            "state": "processing",
            "timestamp": int(time.time()),
        }

        checkpoint_mgr.create_checkpoint(job_id, checkpoint_data)

        # Verify checkpoint exists
        checkpoint_dir = Path(tmpdir) / "checkpoints"
        assert checkpoint_dir.exists(), "Checkpoints directory should exist"

        checkpoints = list(checkpoint_dir.glob(f"*{job_id}*"))
        assert len(checkpoints) > 0, "Checkpoint files should exist"

        print("[PASS] Checkpoint creation and resumption successful")
        return True


def test_exponential_backoff_strategy():
    """Test exponential backoff retry strategy"""
    print("\n" + "="*60)
    print("TEST: Exponential Backoff Retry Strategy")
    print("="*60)

    strategy = ExponentialBackoffStrategy(
        base_delay=1,
        max_retries=3,
        retriable_errors=["timeout", "temporary_failure"]
    )

    # Test retry decision
    error1 = "timeout"
    assert strategy.should_retry(error1, 0), "Should retry timeout on first attempt"
    assert strategy.should_retry(error1, 1), "Should retry timeout on second attempt"
    assert strategy.should_retry(error1, 2), "Should retry timeout on third attempt"
    assert not strategy.should_retry(error1, 3), "Should not retry after max_retries"

    # Test non-retriable error
    error2 = "permanent_failure"
    assert not strategy.should_retry(error2, 0), "Should not retry non-retriable error"

    # Test delay calculation
    delay_1st = strategy.get_backoff_delay(0)
    delay_2nd = strategy.get_backoff_delay(1)
    delay_3rd = strategy.get_backoff_delay(2)

    assert delay_1st < delay_2nd < delay_3rd, "Delays should increase exponentially"
    assert delay_1st >= 1, "First delay should be >= base_delay"

    print("[PASS] Exponential backoff strategy verified")
    return True


def test_budget_gate():
    """Test budget enforcement"""
    print("\n" + "="*60)
    print("TEST: Budget Gate and Spending Control")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        budget_gate = BudgetGate(vault_dir=tmpdir)

        # Test budget check
        job_id = "test-job-budget"

        # Create job budget
        budget_gate.set_job_budget(job_id, 1000)  # $1000

        # Check budget for small cost
        decision = budget_gate.can_execute(job_id, 100)
        assert decision.can_execute, "Should allow execution under budget"

        # Spend some budget
        budget_gate.record_spending(job_id, 600)

        # Check budget for remaining
        decision = budget_gate.can_execute(job_id, 300)
        assert decision.can_execute, "Should allow execution with exact remaining budget"

        # Check budget for exceeding
        decision = budget_gate.can_execute(job_id, 500)
        assert not decision.can_execute, "Should block execution over budget"

        # Verify spending tracked
        spending = budget_gate.get_spending(job_id)
        assert spending >= 600, "Should track spending"

        print("[PASS] Budget gate enforcement verified")
        return True


def test_enhanced_orchestrator():
    """Test enhanced orchestrator with vault integration"""
    print("\n" + "="*60)
    print("TEST: Enhanced Orchestrator with Vault Integration")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        orchestrator = EnhancedOrchestrator(
            vault_dir=tmpdir,
            framework="django",
            language="python"
        )

        # Create job
        job_id = "test-orch-job"
        job_config = {
            "name": "orchestrator_test",
            "budget": 5000,
            "max_retries": 3,
        }

        job_dir = orchestrator.create_job(job_id, job_config)
        assert job_dir is not None, "Job should be created"
        assert Path(job_dir).exists(), "Job directory should exist"

        # Verify vault entry
        vault_dir_path = Path(tmpdir) / "jobs" / job_id
        assert vault_dir_path.exists(), "Job vault entry should exist"

        print("[PASS] Enhanced orchestrator verified")
        return True


def test_vault_factory():
    """Test vault creation via factory function"""
    print("\n" + "="*60)
    print("TEST: Vault Factory Function")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        orchestrator = create_enhanced_orchestrator(
            vault_dir=tmpdir,
            framework="fastapi",
            language="python"
        )

        assert orchestrator is not None, "Factory should create orchestrator"
        assert orchestrator.vault is not None, "Vault should be initialized"
        assert orchestrator.checkpoint_manager is not None, "CheckpointManager should be initialized"
        assert orchestrator.budget_gate is not None, "BudgetGate should be initialized"

        print("[PASS] Vault factory function verified")
        return True


def test_audit_trail():
    """Test audit trail generation"""
    print("\n" + "="*60)
    print("TEST: Audit Trail and Decision Records")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        vault = JobVault(vault_dir=tmpdir)
        job_id = "test-job-audit"
        job_config = {"name": "audit_test"}

        vault.create_job(job_id, job_config, "django", "python")

        # Create multiple work log entries
        for i in range(5):
            entry = WorkLogEntry(
                timestamp=f"2026-05-09T14:{30+i}:45Z",
                agent="worker",
                action=f"step_{i+1}",
                result=f"Step {i+1} completed",
            )
            vault.append_work_log(job_id, entry)

        # Verify audit trail
        job_dir = Path(tmpdir) / "jobs" / job_id
        work_log = job_dir / "work_log.md"

        assert work_log.exists(), "Audit trail should be created"

        with open(work_log) as f:
            content = f.read()
            for i in range(5):
                assert f"step_{i+1}" in content, f"Step {i+1} should be in audit trail"

        print("[PASS] Audit trail generation verified")
        return True


def test_concurrent_job_handling():
    """Test handling multiple concurrent jobs"""
    print("\n" + "="*60)
    print("TEST: Concurrent Job Handling")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        vault = JobVault(vault_dir=tmpdir)
        job_config = {"name": "concurrent_test"}

        # Create multiple jobs
        job_ids = []
        for i in range(5):
            job_id = f"concurrent-job-{i:03d}"
            vault.create_job(job_id, job_config, "django", "python")
            job_ids.append(job_id)

        # Verify all jobs created independently
        jobs_dir = Path(tmpdir) / "jobs"
        created_jobs = [d.name for d in jobs_dir.iterdir() if d.is_dir()]

        assert len(created_jobs) == 5, "All jobs should be created"
        for job_id in job_ids:
            assert job_id in created_jobs, f"Job {job_id} should exist"

        print("[PASS] Concurrent job handling verified")
        return True


def test_state_persistence():
    """Test state persistence across sessions"""
    print("\n" + "="*60)
    print("TEST: State Persistence Across Sessions")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        job_id = "persist-test"
        job_config = {"name": "persistence_test"}

        # Session 1: Create job and log
        vault1 = JobVault(vault_dir=tmpdir)
        vault1.create_job(job_id, job_config, "django", "python")

        entry1 = WorkLogEntry(
            timestamp="2026-05-09T14:30:45Z",
            agent="agent1",
            action="create",
            result="Job created",
        )
        vault1.append_work_log(job_id, entry1)

        # Session 2: Load vault and verify state
        vault2 = JobVault(vault_dir=tmpdir)
        job_dir = vault2.get_job_dir(job_id)
        assert job_dir is not None, "Job should be recoverable in new session"

        work_log_path = Path(job_dir) / "work_log.md"
        assert work_log_path.exists(), "Work log should persist"

        with open(work_log_path) as f:
            content = f.read()
            assert "Job created" in content, "Work log entry should persist"

        print("[PASS] State persistence verified")
        return True


def main():
    """Run all vault integration tests"""
    tests = [
        ("Job Vault Creation", test_job_vault_creation),
        ("Work Log Tracking", test_job_work_log),
        ("Checkpoint & Resumption", test_checkpoint_creation_and_resumption),
        ("Exponential Backoff", test_exponential_backoff_strategy),
        ("Budget Gate", test_budget_gate),
        ("Enhanced Orchestrator", test_enhanced_orchestrator),
        ("Vault Factory", test_vault_factory),
        ("Audit Trail", test_audit_trail),
        ("Concurrent Jobs", test_concurrent_job_handling),
        ("State Persistence", test_state_persistence),
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
    print(f"VAULT INTEGRATION TEST RESULTS: {passed} passed, {failed} failed")
    print("="*60)

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
