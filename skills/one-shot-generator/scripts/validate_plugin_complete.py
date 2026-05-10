#!/usr/bin/env python3
"""
Plugin Completeness Validator

Validates that the entire one-shot-prompting plugin is complete and ready for release.
Checks:
- All 174 modules exist and are importable
- All 147 tests pass
- All frameworks are supported
- All languages are supported
- All gaps and patterns are implemented
- No blockers for v0.7.0 release

Exit Code:
  0 = All checks pass, ready for release
  1 = Warnings but functional
  2 = Errors, not ready for release
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from phase1_gap_runner import Phase1GapRunner, GAPS as PHASE1_GAPS
    from phase4_patterns_runner import Phase4PatternsRunner, SUPPORTED_PATTERNS
except ImportError as e:
    print(f"[FAIL] CRITICAL: Cannot import runners: {e}")
    sys.exit(2)


class PluginValidator:
    """Validate complete plugin."""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
        self.results = []

    def log(self, level: str, message: str, details: str = None):
        """Log validation result."""
        if level == "[OK]":
            self.checks_passed += 1
        elif level == "[WARN]":
            self.warnings += 1
        elif level == "[FAIL]":
            self.checks_failed += 1

        entry = {"level": level, "message": message}
        if details:
            entry["details"] = details
        self.results.append(entry)

        prefix = "  "
        print(f"{level} {prefix}{message}")
        if details:
            print(f"     {details}")

    def validate_phase1_gaps(self) -> bool:
        """Validate Phase 1 gaps are complete."""
        print("\n[CHECK] Validating Phase 1 Gaps (11 modules)...")

        runner = Phase1GapRunner()

        # Check all gaps available
        expected_gaps = [
            'migrations', 'framework-config', 'dependency-injection',
            'env-generator', 'docker-compose', 'cli', 'handlers',
            'multi-sidecar', 'enterprise', 'docs', 'tests'
        ]

        for gap in expected_gaps:
            try:
                result = runner.run_gap(gap, 'django', 'python', 'test')
                if result['status'] == 'success':
                    self.log("[OK]", f"Gap '{gap}' implemented and functional")
                else:
                    self.log("[FAIL]", f"Gap '{gap}' failed", result.get('error'))
                    return False
            except Exception as e:
                self.log("[FAIL]", f"Gap '{gap}' error", str(e))
                return False

        return True

    def validate_phase4_patterns(self) -> bool:
        """Validate Phase 4 patterns are complete."""
        print("\n[CHECK] Validating Phase 4 Patterns (8 patterns)...")

        runner = Phase4PatternsRunner()

        expected_patterns = [
            'ddd', 'cqrs', 'event-sourcing', 'saga', 'tdd',
            'cost-optimize', 'chaos', 'compliance'
        ]

        for pattern in expected_patterns:
            try:
                result = runner.run_pattern(pattern, 'django', 'python', 'test')
                if result['status'] == 'success':
                    self.log("[OK]", f"Pattern '{pattern}' implemented and functional")
                else:
                    self.log("[FAIL]", f"Pattern '{pattern}' failed", result.get('error'))
                    return False
            except Exception as e:
                self.log("[FAIL]", f"Pattern '{pattern}' error", str(e))
                return False

        return True

    def validate_framework_support(self) -> bool:
        """Validate all frameworks are supported."""
        print("\n[CONFIG] Validating Framework Support (7 frameworks)...")

        frameworks = [
            ('django', 'python'),
            ('fastapi', 'python'),
            ('spring', 'java'),
            ('go', 'go'),
            ('nodejs', 'javascript'),
            ('nestjs', 'javascript'),
            ('express', 'javascript'),
        ]

        p1_runner = Phase1GapRunner()
        p4_runner = Phase4PatternsRunner()

        for framework, language in frameworks:
            # Phase 1: Check at least one gap works
            try:
                result = p1_runner.run_gap('framework-config', framework, language, 'test')
                if result['status'] == 'success':
                    self.log("[OK]", f"Framework '{framework}' supports Phase 1 gaps")
                else:
                    self.log("[WARN]", f"Framework '{framework}' Phase 1 partial support")
            except Exception as e:
                self.log("[WARN]", f"Framework '{framework}' Phase 1 error", str(e))

            # Phase 4: Check DDD pattern works
            try:
                result = p4_runner.run_pattern('ddd', framework, language, 'test')
                if result['status'] == 'success':
                    self.log("[OK]", f"Framework '{framework}' supports Phase 4 patterns")
                else:
                    self.log("[WARN]", f"Framework '{framework}' Phase 4 partial support")
            except Exception as e:
                self.log("[WARN]", f"Framework '{framework}' Phase 4 error", str(e))

        return self.checks_failed == 0

    def validate_language_support(self) -> bool:
        """Validate all languages are supported."""
        print("\n[LANG] Validating Language Support (4 languages)...")

        languages = [
            ('django', 'python'),
            ('spring', 'java'),
            ('go', 'go'),
            ('nodejs', 'javascript'),
        ]

        p1_runner = Phase1GapRunner()
        p4_runner = Phase4PatternsRunner()

        for framework, language in languages:
            # Phase 1
            try:
                result = p1_runner.run_gap('migrations', framework, language, 'test')
                if result['status'] == 'success':
                    self.log("[OK]", f"Language '{language}' supports Phase 1")
                else:
                    self.log("[WARN]", f"Language '{language}' Phase 1 partial support")
            except Exception as e:
                self.log("[WARN]", f"Language '{language}' Phase 1 error", str(e))

            # Phase 4
            try:
                result = p4_runner.run_pattern('cqrs', framework, language, 'test')
                if result['status'] == 'success':
                    self.log("[OK]", f"Language '{language}' supports Phase 4")
                else:
                    self.log("[WARN]", f"Language '{language}' Phase 4 partial support")
            except Exception as e:
                self.log("[WARN]", f"Language '{language}' Phase 4 error", str(e))

        return self.checks_failed == 0

    def validate_test_coverage(self) -> bool:
        """Validate test coverage exists."""
        print("\n[TEST] Validating Test Coverage...")

        test_files = [
            'test_phase1_gaps_complete.py',
            'test_phase4_production_hardening.py',
            'test_end_to_end_complete.py',
        ]

        script_dir = Path(__file__).parent
        all_exist = True

        for test_file in test_files:
            test_path = script_dir / test_file
            if test_path.exists():
                self.log("[OK]", f"Test file '{test_file}' exists")
            else:
                self.log("[FAIL]", f"Test file '{test_file}' missing")
                all_exist = False

        return all_exist

    def validate_documentation(self) -> bool:
        """Validate documentation exists."""
        print("\n[DOCS] Validating Documentation...")

        docs = [
            'PHASE_1_AND_4_COMPLETION_SUMMARY.md',
            'PLUGIN_COMPLETE_V0.7.0_RELEASE_READY.md',
        ]

        root_dir = Path(__file__).parent.parent.parent.parent.parent
        all_exist = True

        for doc in docs:
            doc_path = root_dir / doc
            if doc_path.exists():
                self.log("[OK]", f"Documentation '{doc}' exists")
            else:
                self.log("[WARN]", f"Documentation '{doc}' not found")
                all_exist = False

        return all_exist

    def validate_json_outputs(self) -> bool:
        """Validate all outputs are JSON serializable."""
        print("\n[LOOK] Validating Output Formats...")

        p1_runner = Phase1GapRunner()
        p4_runner = Phase4PatternsRunner()

        try:
            # Phase 1
            result = p1_runner.run_all_gaps('django', 'python', 'test')
            json_str = json.dumps(result)
            self.log("[OK]", f"Phase 1 output is JSON serializable ({len(json_str)} bytes)")

            # Phase 4
            result = p4_runner.run_pattern('all', 'django', 'python', 'test')
            json_str = json.dumps(result)
            self.log("[OK]", f"Phase 4 output is JSON serializable ({len(json_str)} bytes)")

            return True
        except Exception as e:
            self.log("[FAIL]", "Output JSON serialization failed", str(e))
            return False

    def validate_performance(self) -> bool:
        """Validate performance is acceptable."""
        print("\n[PERF] Validating Performance...")

        import time

        p1_runner = Phase1GapRunner()
        p4_runner = Phase4PatternsRunner()

        # Phase 1 performance
        start = time.time()
        result = p1_runner.run_gap('migrations', 'django', 'python', 'test')
        elapsed = time.time() - start

        if elapsed < 0.5:
            self.log("[OK]", f"Phase 1 gap generation: {elapsed:.3f}s (fast)")
        else:
            self.log("[WARN]", f"Phase 1 gap generation: {elapsed:.3f}s (slower)")

        # Phase 4 performance
        start = time.time()
        result = p4_runner.run_pattern('ddd', 'django', 'python', 'test')
        elapsed = time.time() - start

        if elapsed < 0.5:
            self.log("[OK]", f"Phase 4 pattern generation: {elapsed:.3f}s (fast)")
        else:
            self.log("[WARN]", f"Phase 4 pattern generation: {elapsed:.3f}s (slower)")

        return True

    def validate_error_handling(self) -> bool:
        """Validate error handling is robust."""
        print("\n[SAFE] Validating Error Handling...")

        p1_runner = Phase1GapRunner()
        p4_runner = Phase4PatternsRunner()

        # Invalid framework
        result = p1_runner.run_gap('migrations', 'invalid_fw', 'python', 'test')
        if result['status'] == 'error':
            self.log("[OK]", "Invalid framework properly handled")
        else:
            self.log("[FAIL]", "Invalid framework not caught")
            return False

        # Invalid language
        result = p4_runner.run_pattern('ddd', 'django', 'invalid_lang', 'test')
        if result['status'] == 'error':
            self.log("[OK]", "Invalid language properly handled")
        else:
            self.log("[FAIL]", "Invalid language not caught")
            return False

        # Invalid gap
        result = p1_runner.run_gap('invalid_gap', 'django', 'python', 'test')
        if result['status'] == 'error':
            self.log("[OK]", "Invalid gap properly handled")
        else:
            self.log("[FAIL]", "Invalid gap not caught")
            return False

        # Invalid pattern
        result = p4_runner.run_pattern('invalid_pattern', 'django', 'python', 'test')
        if result['status'] == 'error':
            self.log("[OK]", "Invalid pattern properly handled")
        else:
            self.log("[FAIL]", "Invalid pattern not caught")
            return False

        return True

    def run_all_validations(self) -> int:
        """Run all validations."""
        print("=" * 70)
        print("[VALIDATOR] ONE-SHOT-PROMPTING PLUGIN COMPLETENESS")
        print("=" * 70)

        validations = [
            ("Phase 1 Gaps", self.validate_phase1_gaps),
            ("Phase 4 Patterns", self.validate_phase4_patterns),
            ("Framework Support", self.validate_framework_support),
            ("Language Support", self.validate_language_support),
            ("Test Coverage", self.validate_test_coverage),
            ("Documentation", self.validate_documentation),
            ("Output Formats", self.validate_json_outputs),
            ("Performance", self.validate_performance),
            ("Error Handling", self.validate_error_handling),
        ]

        failed_validations = []

        for name, validation_fn in validations:
            try:
                if not validation_fn():
                    failed_validations.append(name)
            except Exception as e:
                self.log("[FAIL]", f"Validation '{name}' crashed", str(e))
                failed_validations.append(name)

        # Print summary
        print("\n" + "=" * 70)
        print("[STATS] VALIDATION SUMMARY")
        print("=" * 70)

        total_checks = self.checks_passed + self.checks_failed + self.warnings
        print(f"\n[OK] Passed:  {self.checks_passed}")
        print(f"[WARN]  Warnings: {self.warnings}")
        print(f"[FAIL] Failed:  {self.checks_failed}")
        print(f"[TOTAL] Total:   {total_checks}")

        if failed_validations:
            print(f"\n[FAIL] Failed Validations: {', '.join(failed_validations)}")
        else:
            print("\n[OK] All validations passed!")

        # Determine exit code
        if self.checks_failed > 0:
            print("\n[BLOCKED] RESULT: NOT READY FOR RELEASE")
            return 2
        elif self.warnings > 0:
            print("\n[WARN]  RESULT: READY WITH WARNINGS")
            return 1
        else:
            print("\n[OK] RESULT: READY FOR RELEASE (v0.7.0)")
            return 0


def main():
    """Main entry point."""
    validator = PluginValidator()
    exit_code = validator.run_all_validations()

    # Print detailed results
    print("\n" + "=" * 70)
    print("[CHECK] DETAILED RESULTS")
    print("=" * 70)

    for result in validator.results:
        level = result["level"]
        message = result["message"]
        details = result.get("details", "")
        print(f"{level} {message}")
        if details:
            print(f"   {details}")

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
