#!/usr/bin/env python3
"""
Phase 4 TDD: Cycle Enforcer

Enforces TDD workflow: Red → Green → Refactor

TDD cycle:
1. RED: Write failing test (test what you want to build)
2. GREEN: Write minimal code to pass test
3. REFACTOR: Improve code while keeping test passing

Benefits:
- Write tests first (spec-driven development)
- Minimal code (no unused features)
- Immediate feedback
- Confidence: if test passes, feature works
- Documentation: tests show how to use code

This module enforces the workflow:
- Validate test exists and fails
- Write code to pass test
- Refactor while keeping test passing
- Move to next test

Usage:
    python phase4_tdd_cycle_enforcer.py --task "add email validation"

Input: Task/feature to implement
Output: TDD workflow with test harness
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


def generate_tdd_cycle_manager() -> str:
    """Generate TDD cycle manager."""

    manager = '''
class TDDCycleManager:
    """
    Manages TDD workflow.

    Enforces: Red → Green → Refactor cycle

    Responsibilities:
    1. Track cycle phases
    2. Validate test exists
    3. Run tests (expect fail in Red, pass in Green)
    4. Guide refactoring
    5. Track metrics (time, iterations)
    """

    def __init__(self):
        self.current_phase = "setup"  # setup, red, green, refactor, done
        self.test_file = None
        self.code_file = None
        self.test_results = []
        self.cycle_history = []
        self.start_time = datetime.utcnow()

    def setup_test_environment(
        self,
        test_file: str,
        code_file: str
    ) -> None:
        """Setup: specify test and code files"""
        self.test_file = test_file
        self.code_file = code_file
        self.current_phase = "red"

    def enter_red_phase(self) -> Dict:
        """
        RED phase: Write failing test.

        Test should fail because feature not implemented.

        Requirements:
        - Test file exists
        - Test is runnable
        - Test fails (expected)
        """
        print("📍 PHASE: RED")
        print(f"  Test file: {self.test_file}")
        print("  Write a test for your feature (it should fail)")
        print("  Command: pytest {self.test_file} -v")

        return {
            "phase": "red",
            "action": "write_failing_test",
            "expected_result": "test fails",
            "next": "run_red_tests"
        }

    def run_red_tests(self, test_runner: Callable) -> Dict:
        """Run tests, verify they fail"""
        print("\n🔴 Running tests (expect FAILURE)...")

        result = test_runner(self.test_file)

        if result["passed"] > 0 and result["failed"] == 0:
            # Tests pass - skip red phase
            print("  ⚠️  Tests already pass! Skipping to green.")
            self.current_phase = "green"
            return {"status": "already_passing"}

        if result["failed"] > 0:
            print(f"  ✓ Tests failing as expected ({result['failed']} failures)")
            self.current_phase = "green"
            self.test_results.append(result)
            return {"status": "ready_for_green", "failures": result["failed"]}

        return {"status": "error", "message": "Could not run tests"}

    def enter_green_phase(self) -> Dict:
        """
        GREEN phase: Write minimal code to pass test.

        Requirements:
        - Implement feature (minimal!)
        - All tests pass
        - No extra features

        Do NOT:
        - Optimize prematurely
        - Add extra features
        - Refactor yet
        """
        print("\n📍 PHASE: GREEN")
        print(f"  Code file: {self.code_file}")
        print("  Write MINIMAL code to make test pass")
        print("  Do NOT optimize or add extra features yet")

        return {
            "phase": "green",
            "action": "write_minimal_code",
            "expected_result": "all tests pass"
        }

    def run_green_tests(self, test_runner: Callable) -> Dict:
        """Run tests, verify they pass"""
        print("\n🟢 Running tests (expect SUCCESS)...")

        result = test_runner(self.test_file)

        if result["failed"] > 0:
            print(f"  ❌ Tests still failing ({result['failed']} failures)")
            print("  Go back to GREEN phase, write more code")
            return {"status": "still_failing", "failures": result["failed"]}

        if result["passed"] > 0:
            print(f"  ✓ All tests passing! ({result['passed']} passed)")
            self.current_phase = "refactor"
            self.test_results.append(result)
            return {"status": "ready_for_refactor", "passed": result["passed"]}

        return {"status": "error"}

    def enter_refactor_phase(self) -> Dict:
        """
        REFACTOR phase: Improve code quality.

        Now tests pass. Keep them passing while:
        - Remove duplication
        - Improve readability
        - Optimize performance
        - Split into functions
        - Add comments

        Requirements:
        - All tests still pass after refactor
        - Code quality improved
        - No new features
        """
        print("\n📍 PHASE: REFACTOR")
        print("  Tests are passing! Now improve code quality:")
        print("  - Remove duplication")
        print("  - Improve readability")
        print("  - Split into functions")
        print("  - Optimize performance")
        print("  ⚠️  Keep all tests passing!")

        return {
            "phase": "refactor",
            "action": "improve_code_quality",
            "expected_result": "code cleaner, tests still pass"
        }

    def run_refactor_tests(self, test_runner: Callable) -> Dict:
        """Run tests after refactor, ensure still passing"""
        print("\n🔵 Running tests after refactor...")

        result = test_runner(self.test_file)

        if result["failed"] > 0:
            print(f"  ❌ Refactoring broke tests ({result['failed']} failures)")
            print("  Revert refactoring changes")
            return {"status": "refactoring_broke_tests"}

        if result["passed"] > 0:
            print(f"  ✓ Tests still passing after refactor ({result['passed']} passed)")
            self.current_phase = "done"
            self.test_results.append(result)
            return {"status": "refactor_complete"}

        return {"status": "error"}

    def complete_cycle(self) -> Dict:
        """Mark cycle complete"""
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()

        cycle = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_file": self.test_file,
            "code_file": self.code_file,
            "duration_seconds": elapsed,
            "test_results": self.test_results
        }

        self.cycle_history.append(cycle)
        self.current_phase = "setup"

        return {
            "status": "cycle_complete",
            "cycle": cycle
        }

    def get_metrics(self) -> Dict:
        """Get TDD metrics"""
        if not self.cycle_history:
            return {}

        durations = [c["duration_seconds"] for c in self.cycle_history]
        total_tests = sum(
            len(c["test_results"]) for c in self.cycle_history
        )

        return {
            "cycles_completed": len(self.cycle_history),
            "avg_cycle_duration": sum(durations) / len(durations),
            "total_tests": total_tests,
            "total_time": sum(durations)
        }
'''

    return manager


def generate_test_runner_helper() -> str:
    """Generate test runner helper."""

    runner = '''
class TDDTestRunner:
    """
    Runs tests and reports results.

    Result format:
    {
        "passed": int,
        "failed": int,
        "errors": list,
        "skipped": int,
        "total_time": float
    }
    """

    def __init__(self):
        self.test_history = []

    def run_tests(self, test_file: str) -> Dict:
        """
        Run test file and return results.

        Parse test output to determine:
        - How many passed
        - How many failed
        - Error messages
        """
        # Implementation: run pytest or unittest
        # Parse output
        # Return structured results

        result = {
            "file": test_file,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
            "timestamp": datetime.utcnow().isoformat()
        }

        self.test_history.append(result)
        return result

    def get_last_run(self) -> Optional[Dict]:
        """Get last test run results"""
        return self.test_history[-1] if self.test_history else None

    def run_coverage(self, test_file: str) -> Dict:
        """Run tests with coverage report"""
        # Run pytest with --cov
        # Return coverage metrics

        return {
            "file": test_file,
            "coverage_percent": 0,
            "covered_lines": 0,
            "missing_lines": 0
        }
'''

    return runner


def generate_tdd_workflow_guide() -> str:
    """Generate TDD workflow guide."""

    guide = '''
class TDDWorkflowGuide:
    """
    Step-by-step guide for TDD workflow.

    Typical TDD session:

    1. SETUP
       - Pick feature to implement (small!)
       - Create test file
       - Create code file
       - Run setup

    2. RED
       - Write test for feature
       - Test should fail (feature not implemented)
       - Run: TDD.run_red_tests()

    3. GREEN
       - Write minimal code to pass test
       - Focus on making test pass (don't optimize)
       - Run: TDD.run_green_tests()

    4. REFACTOR
       - Improve code quality (while tests pass)
       - Remove duplication
       - Improve readability
       - Run: TDD.run_refactor_tests()

    5. REPEAT
       - Pick next feature
       - Go to RED phase

    Example: Add email validation

    1. Write test:
    def test_valid_email():
        assert is_valid_email("alice@example.com") == True

    def test_invalid_email():
        assert is_valid_email("not-an-email") == False

    2. Write code (minimal):
    def is_valid_email(email):
        return "@" in email  # Minimal!

    3. Tests pass! Refactor:
    import re
    EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"

    def is_valid_email(email):
        return bool(re.match(EMAIL_REGEX, email))

    4. Tests still pass! Done.
    """

    @staticmethod
    def validate_test_format(test_code: str) -> List[str]:
        """
        Validate test follows TDD patterns.

        Good test:
        - Has clear description
        - Tests one thing
        - Has assertions
        - Uses meaningful names

        Bad test:
        - Tests multiple things
        - No assertions
        - Unclear purpose
        """
        issues = []

        if "def test_" not in test_code:
            issues.append("Test function must start with 'test_'")

        if "assert" not in test_code:
            issues.append("Test must have assertions")

        return issues

    @staticmethod
    def validate_implementation(code: str, test_code: str) -> List[str]:
        """
        Validate implementation is minimal.

        Should implement only what test requires.
        """
        issues = []

        # Check for over-engineering
        if "if" in code and "else" in code and "elif" in code:
            if "def " not in code:  # All conditional, no functions
                issues.append("Consider splitting into functions")

        return issues
'''

    return guide


def generate_tdd_system() -> dict:
    """Generate complete TDD system."""

    imports = '''from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


'''

    module_doc = '''"""
TDD: Test-Driven Development Cycle Enforcer

Enforces: RED → GREEN → REFACTOR workflow

TDD Cycle:

1. RED: Write failing test
   - Test describes what you want to build
   - Test fails (feature not implemented yet)
   - You know what to implement

2. GREEN: Write minimal code to pass test
   - Implement feature (minimal!)
   - Don't optimize yet
   - Don't add extra features
   - All tests pass

3. REFACTOR: Improve code quality
   - Remove duplication
   - Improve readability
   - Optimize performance
   - Keep all tests passing!

Benefits:
✓ Tests first (specification-driven)
✓ Minimal code (no unused features)
✓ Immediate feedback (test → code → test)
✓ Confidence (if test passes, feature works)
✓ Documentation (tests show how to use code)
✓ Refactoring safety (tests catch regressions)

Anti-patterns to avoid:
✗ Writing all code first, tests later (test debt)
✗ Over-engineering in GREEN phase (premature optimization)
✗ Skipping REFACTOR (code quality degrades)
✗ Testing multiple things (tests should be focused)
✗ Ignoring test failures (they're signals!)

Typical session metrics:
- RED phase: 1-5 minutes (write test)
- GREEN phase: 5-20 minutes (write code)
- REFACTOR phase: 5-15 minutes (improve)
- Total: 15-40 minutes per feature
"""
'''

    manager = generate_tdd_cycle_manager()
    runner = generate_test_runner_helper()
    guide = generate_tdd_workflow_guide()

    complete_code = imports + module_doc + "\n" + manager + "\n" + runner + "\n" + guide

    return {
        "code": complete_code,
        "pattern": "TDD Cycle Enforcer",
        "module": "tdd_cycle_enforcer.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate TDD cycle enforcer")
    parser.add_argument("--task", help="Task/feature to implement")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_tdd_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
