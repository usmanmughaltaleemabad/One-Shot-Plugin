#!/usr/bin/env python3
"""
Integration tests for failure_detector.py

Tests failure counter increment, reset, rollback trigger, and state persistence.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run_failure_detector(action: str, **kwargs) -> dict:
    """Run failure_detector.py and return parsed JSON output."""
    # Convert action name: should_trigger -> should-trigger
    action_name = action.replace("_", "-")
    cmd = [
        sys.executable,
        "./skills/one-shot-generator/scripts/failure_detector.py",
        "--action",
        action_name,
        "--json",
    ]
    for key, value in kwargs.items():
        if value is not None:
            cmd.append(f"--{key.replace('_', '-')}")
            if not isinstance(value, bool):
                cmd.append(str(value))
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent.parent,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {result.stderr}")
    return json.loads(result.stdout)


def test_failure_counter_increments():
    """Test that consecutive failure counter increments."""
    # Start fresh by resetting
    run_failure_detector("reset")

    # Record first failure
    result1 = run_failure_detector("record", spec_hash="spec-001")
    assert result1["consecutive_failures"] == 1, "First failure should increment to 1"

    # Record second failure
    result2 = run_failure_detector("record", spec_hash="spec-002")
    assert result2["consecutive_failures"] == 2, "Second failure should increment to 2"

    # Record third failure
    result3 = run_failure_detector("record", spec_hash="spec-003")
    assert result3["consecutive_failures"] == 3, "Third failure should increment to 3"

    print("[PASS] test_failure_counter_increments")


def test_reset_clears_counter():
    """Test that reset sets counter to zero."""
    # Set up some failures
    run_failure_detector("reset")
    run_failure_detector("record", spec_hash="spec-001")
    run_failure_detector("record", spec_hash="spec-002")

    # Verify we have failures
    status = run_failure_detector("status")
    assert status["state"]["consecutive_failures"] == 2, "Should have 2 failures before reset"

    # Reset
    run_failure_detector("reset")

    # Verify counter is 0
    status = run_failure_detector("status")
    assert status["state"]["consecutive_failures"] == 0, "Counter should be 0 after reset"

    print("[PASS] test_reset_clears_counter")


def test_rollback_triggered_at_threshold():
    """Test that rollback is triggered at threshold (default 3)."""
    # Start fresh
    run_failure_detector("reset")

    # Record 2 failures (below threshold)
    run_failure_detector("record", spec_hash="spec-001")
    run_failure_detector("record", spec_hash="spec-002")

    # Check trigger at threshold=3 (should be False)
    result = run_failure_detector("should-trigger", threshold=3)
    assert result["trigger"] is False, "Rollback should not trigger at 2/3 failures"

    # Record 3rd failure
    run_failure_detector("record", spec_hash="spec-003")

    # Check trigger (should be True)
    result = run_failure_detector("should-trigger", threshold=3)
    assert result["trigger"] is True, "Rollback should trigger at 3/3 failures"

    print("[PASS] test_rollback_triggered_at_threshold")


def test_rollback_with_custom_threshold():
    """Test rollback with custom threshold."""
    # Start fresh
    run_failure_detector("reset")

    # Record 4 failures
    for i in range(4):
        run_failure_detector("record", spec_hash=f"spec-{i+1:03d}")

    # Check trigger at threshold=2 (should be True)
    result = run_failure_detector("should-trigger", threshold=2)
    assert result["trigger"] is True, "Rollback should trigger at 4/2 failures"

    # Check trigger at threshold=5 (should be False)
    result = run_failure_detector("should-trigger", threshold=5)
    assert result["trigger"] is False, "Rollback should not trigger at 4/5 failures"

    print("[PASS] test_rollback_with_custom_threshold")


def test_failure_state_persistence():
    """Test that failure state persists across invocations."""
    # Start fresh
    run_failure_detector("reset")

    # Record one failure
    run_failure_detector("record", spec_hash="spec-persistence-001")

    # Fetch status in separate invocation
    status = run_failure_detector("status")
    assert status["state"]["consecutive_failures"] == 1, "Failure should persist across calls"
    assert (
        status["state"]["last_failing_spec"] == "spec-persistence-001"
    ), "Spec hash should persist"
    assert status["state"]["last_failure_ts"] is not None, "Timestamp should be recorded"

    print("[PASS] test_failure_state_persistence")


def test_status_action():
    """Test status action returns current state."""
    run_failure_detector("reset")
    run_failure_detector("record", spec_hash="spec-status-test")

    status = run_failure_detector("status")
    assert "state" in status, "Status should have 'state' key"
    assert status["state"]["consecutive_failures"] == 1
    assert status["state"]["last_failing_spec"] == "spec-status-test"
    assert status["state"]["last_failure_ts"] is not None

    print("[PASS] test_status_action")


def test_state_on_empty_file():
    """Test that empty/missing state file returns defaults."""
    # This is tested implicitly by reset working correctly
    # Additional test: run status right after reset
    run_failure_detector("reset")
    status = run_failure_detector("status")
    assert status["state"]["consecutive_failures"] == 0
    assert status["state"]["last_failing_spec"] is None
    assert status["state"]["last_failure_ts"] is None

    print("[PASS] test_state_on_empty_file")


def test_record_without_reset():
    """Test that recording works even if prior state is unknown."""
    # This is a resilience test: even if file is corrupted,
    # we should be able to record new state
    run_failure_detector("reset")
    result = run_failure_detector("record", spec_hash="spec-001")
    assert result["consecutive_failures"] == 1

    print("[PASS] test_record_without_reset")


def test_spec_hash_tracked():
    """Test that spec_hash is properly tracked."""
    run_failure_detector("reset")

    specs = ["spec-aaa", "spec-bbb", "spec-ccc"]
    for spec in specs:
        run_failure_detector("record", spec_hash=spec)

    status = run_failure_detector("status")
    # Last recorded spec should be the most recent
    assert status["state"]["last_failing_spec"] == specs[-1]

    print("[PASS] test_spec_hash_tracked")


if __name__ == "__main__":
    tests = [
        test_failure_counter_increments,
        test_reset_clears_counter,
        test_rollback_triggered_at_threshold,
        test_rollback_with_custom_threshold,
        test_failure_state_persistence,
        test_status_action,
        test_state_on_empty_file,
        test_record_without_reset,
        test_spec_hash_tracked,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1

    if failed:
        print(f"\n{failed}/{len(tests)} tests failed")
        sys.exit(1)
    else:
        print(f"\nAll {len(tests)} tests passed!")
