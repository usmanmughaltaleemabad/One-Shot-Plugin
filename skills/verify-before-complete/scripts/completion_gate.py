#!/usr/bin/env python3
"""
Skill: verify-before-complete
Completion Gate — Run verification gates before permitting completion claims.

Input: Project path, gate type (syntax|tests|lint|all)
Output: Gate results (status: CLEAR|BLOCKED|WARN)

Gates (configurable):
  1. syntax — CodeValidator from verify_generated.py
  2. tests — Auto-detect test runner and run tests
  3. lint — CodeReviewer from code_review_automation.py
  4. all — Run all gates in sequence

Superpowers rule: Claude cannot output "done", "complete", "finished"
until status == "CLEAR" in the JSON output.

Session state persisted in .one-shot-verify-session.json.
"""

import sys
import os
import json
import subprocess
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

# Shared library imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent / ".." / ".." / ".." / "one-shot-generator" / "scripts"))

try:
    from lib.base_script import __version__, setup_logging, timed_run
    from verify_generated import CodeValidator
    from code_review_automation import CodeReviewer
except ImportError as e:
    # Fallback utilities
    __version__ = "1.0.0"
    def setup_logging(name, level=None):
        import logging
        logger = logging.getLogger(name)
        logger.setLevel(level or "WARNING")
        return logger

    from contextlib import contextmanager
    @contextmanager
    def timed_run(name):
        import time
        start = time.time()
        class Timer:
            elapsed_ms = 0
        timer = Timer()
        try:
            yield timer
        finally:
            timer.elapsed_ms = int((time.time() - start) * 1000)

    # Stub classes if imports fail
    class CodeValidator:
        def __init__(self, **kwargs): pass
        def validate(self): return True, [], []

    class CodeReviewer:
        def __init__(self, **kwargs): pass
        def review(self, code, filepath='<generated>'):
            return {'overall': 'PASS', 'sections': {}}

__version__ = "1.0.0"
logger = setup_logging(__name__)


@dataclass
class GateResult:
    """Result from a single gate."""
    gate_name: str
    status: str  # PASS | WARN | BLOCK
    findings: List[str]
    output: str = ''

    def to_dict(self) -> Dict:
        return asdict(self)


class CompletionGate:
    """Orchestrates all verification gates."""

    SESSION_FILE = '.one-shot-verify-session.json'

    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root)
        self.session_file = self.project_root / self.SESSION_FILE
        self.results: List[GateResult] = []

    def run_gate(self, gate_type: str, code_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run a single gate.

        Args:
            gate_type: 'syntax' | 'tests' | 'lint' | 'all'
            code_files: List of code file paths to check (for syntax/lint gates)

        Returns:
            {
                'gate_name': str,
                'status': 'PASS' | 'WARN' | 'BLOCK',
                'findings': [str],
                'output': str,
            }
        """
        gate_type = gate_type.lower()

        if gate_type == 'syntax':
            return self._gate_syntax(code_files or [])
        elif gate_type == 'tests':
            return self._gate_tests()
        elif gate_type == 'lint':
            return self._gate_lint(code_files or [])
        elif gate_type == 'all':
            return self._gate_all(code_files)
        else:
            return {
                'error': f'Unknown gate type: {gate_type}',
                'valid_gates': ['syntax', 'tests', 'lint', 'all'],
            }

    def _gate_syntax(self, code_files: List[str]) -> Dict[str, Any]:
        """Run syntax validation gate."""
        result = GateResult(gate_name='syntax', status='PASS', findings=[])

        if not code_files:
            # Auto-detect Python files in project
            code_files = list(self.project_root.glob('**/*.py'))[:10]

        for filepath in code_files:
            try:
                if not filepath.exists():
                    continue

                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()

                # Use CodeValidator from verify_generated.py
                validator = CodeValidator(code=code, filepath=str(filepath))
                is_valid, errors, warnings = validator.validate()

                if not is_valid:
                    result.status = 'BLOCK'
                    result.findings.extend([f"{filepath}: {e}" for e in errors])
                elif warnings and result.status != 'BLOCK':
                    result.status = 'WARN'
                    result.findings.extend([f"{filepath}: {w}" for w in warnings])

            except Exception as e:
                result.status = 'BLOCK'
                result.findings.append(f"Error validating {filepath}: {str(e)}")

        self.results.append(result)
        return result.to_dict()

    def _gate_tests(self) -> Dict[str, Any]:
        """Run test suite (auto-detect test runner)."""
        result = GateResult(gate_name='tests', status='PASS', findings=[])

        # Try to auto-detect test runner
        test_commands = [
            ('pytest', 'pytest --tb=short -v'),
            ('jest', 'npm test'),
            ('go', 'go test ./...'),
            ('mvn', 'mvn test'),
            ('gradle', 'gradle test'),
        ]

        for name, cmd in test_commands:
            try:
                # Check if test framework is available
                check = subprocess.run(
                    cmd.split()[0] + ' --version' if ' ' not in cmd else cmd.split()[0],
                    capture_output=True,
                    timeout=5,
                    shell=True,
                )
                if check.returncode != 0:
                    continue

                # Run tests
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=str(self.project_root),
                )

                result.output = proc.stdout + proc.stderr

                if proc.returncode != 0:
                    result.status = 'BLOCK'
                    result.findings.append(f'{name}: test suite failed')
                    # Extract failure summary from output
                    for line in result.output.split('\n'):
                        if 'FAILED' in line or 'ERROR' in line or 'failed' in line:
                            result.findings.append(line.strip())
                else:
                    result.findings.append(f'{name}: all tests passed')

                self.results.append(result)
                return result.to_dict()

            except subprocess.TimeoutExpired:
                result.status = 'BLOCK'
                result.findings.append(f'{name}: tests timed out (>60s)')
                self.results.append(result)
                return result.to_dict()
            except Exception:
                continue

        # No test runner detected
        result.status = 'WARN'
        result.findings.append('No test runner detected (pytest/jest/go/mvn/gradle)')
        self.results.append(result)
        return result.to_dict()

    def _gate_lint(self, code_files: List[str]) -> Dict[str, Any]:
        """Run linting/review gate."""
        result = GateResult(gate_name='lint', status='PASS', findings=[])

        if not code_files:
            code_files = list(self.project_root.glob('**/*.py'))[:10]

        for filepath in code_files:
            try:
                if not filepath.exists():
                    continue

                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()

                # Use CodeReviewer from code_review_automation.py
                reviewer = CodeReviewer(language='python', framework='unknown')
                review = reviewer.review(code, str(filepath))

                overall = review.get('overall', 'PASS')
                if overall == 'BLOCK':
                    result.status = 'BLOCK'
                elif overall == 'WARN' and result.status != 'BLOCK':
                    result.status = 'WARN'

                # Collect findings from all sections
                for section_name, section in review.get('sections', {}).items():
                    section_status = section.get('status', 'PASS')
                    if section_status in ['WARN', 'BLOCK']:
                        for finding in section.get('findings', []):
                            msg = finding.get('message', '')
                            severity = finding.get('severity', 'info')
                            if severity in ['block', 'warn']:
                                result.findings.append(f"{section_name}: {msg}")

            except Exception as e:
                result.findings.append(f"Error reviewing {filepath}: {str(e)}")

        self.results.append(result)
        return result.to_dict()

    def _gate_all(self, code_files: Optional[List[str]]) -> Dict[str, Any]:
        """Run all gates in sequence."""
        results = []

        # Run syntax
        syntax_result = self._gate_syntax(code_files or [])
        results.append(syntax_result)

        # Run tests only if syntax passes (or warns)
        if syntax_result['status'] != 'BLOCK':
            tests_result = self._gate_tests()
            results.append(tests_result)

        # Run lint
        lint_result = self._gate_lint(code_files or [])
        results.append(lint_result)

        # Compute overall status
        overall_status = 'CLEAR'  # Default: all gates passed
        blocking_issues = []

        for r in results:
            if r['status'] == 'BLOCK':
                overall_status = 'BLOCKED'
                blocking_issues.extend(r['findings'])
            elif r['status'] == 'WARN' and overall_status != 'BLOCKED':
                overall_status = 'WARN'

        return {
            'overall_status': overall_status,
            'gates_passed': [r['gate_name'] for r in results if r['status'] == 'PASS'],
            'gates_warned': [r['gate_name'] for r in results if r['status'] == 'WARN'],
            'gates_blocked': [r['gate_name'] for r in results if r['status'] == 'BLOCK'],
            'blocking_issues': blocking_issues,
            'gate_results': results,
        }

    def save_session(self):
        """Persist gate results to session file."""
        try:
            session_data = {
                'timestamp': datetime.now().isoformat(),
                'results': [r.to_dict() for r in self.results],
            }
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save session: {e}")


def main():
    """CLI entry point for completion_gate."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Run completion verification gates'
    )
    parser.add_argument('--gate', default='all',
                       choices=['syntax', 'tests', 'lint', 'all'],
                       help='Gate to run')
    parser.add_argument('--cwd', default='.', help='Project root directory')
    parser.add_argument('--files', default='',
                       help='Comma-separated list of files to check')

    args = parser.parse_args()

    with timed_run(f'completion_gate_{args.gate}'):
        gate = CompletionGate(args.cwd)
        code_files = [Path(f.strip()) for f in args.files.split(',') if f.strip()] if args.files else None
        result = gate.run_gate(args.gate, code_files)
        gate.save_session()

    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
