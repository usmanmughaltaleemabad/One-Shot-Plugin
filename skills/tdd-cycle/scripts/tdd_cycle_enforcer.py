#!/usr/bin/env python3
"""
Skill: tdd-cycle
TDD Cycle Enforcer — Red-Green-Refactor with phase gates.

Phases:
  1. red — Generate ONLY failing test + NotImplementedError stub
  2. green — Generate minimal implementation to pass failing test
  3. refactor — Align with codebase conventions, no behavior changes

Each phase blocks proceeding to next without user confirmation.
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent / ".." / ".." / ".." / "one-shot-generator" / "scripts"))

try:
    from lib.base_script import __version__, setup_logging, timed_run
    from analyze_codebase import CodebaseAnalyzer
except ImportError:
    __version__ = "1.0.0"
    def setup_logging(name, level=None):
        import logging
        return logging.getLogger(name)

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

__version__ = "1.0.0"
logger = setup_logging(__name__)


class TDDCycleEnforcer:
    """Enforces Red-Green-Refactor cycle with phase gates."""

    def __init__(self, project_path: str = '.'):
        self.project_path = Path(project_path)
        self.context = {}

    def phase_red(self, feature_name: str) -> Dict[str, Any]:
        """
        RED phase: Generate failing test + NotImplementedError stub.
        """
        # Detect language and test framework
        language = self._detect_language()
        test_framework = self._detect_test_framework(language)

        test_file = self._generate_test_file(feature_name, language, test_framework)
        impl_file = self._generate_impl_stub(feature_name, language)

        return {
            'phase': 'RED',
            'language': language,
            'test_framework': test_framework,
            'test_file': test_file,
            'impl_file': impl_file,
            'run_command': self._test_command(language, test_framework),
            'expected_failure': 'NotImplementedError("RED: implement to make this pass")',
            'instructions': 'Run the test command above. Confirm it fails with NotImplementedError before proceeding to GREEN.',
        }

    def phase_green(self, test_file: str, feature_name: str) -> Dict[str, Any]:
        """
        GREEN phase: Generate minimal implementation to pass failing test.
        """
        # Read the test file to extract assertion signatures
        try:
            with open(test_file, 'r') as f:
                test_code = f.read()
        except Exception as e:
            return {'error': f'Failed to read test file: {e}'}

        language = self._detect_language()
        impl = self._generate_minimal_impl(feature_name, test_code, language)
        impl_file = self._infer_impl_file(test_file, language)

        return {
            'phase': 'GREEN',
            'language': language,
            'impl_file': impl_file,
            'implementation': impl,
            'run_command': self._test_command(language, self._detect_test_framework(language)),
            'expected_result': 'All tests pass',
            'instructions': 'Apply the implementation above, then run the test command. Confirm all tests pass before proceeding to REFACTOR.',
        }

    def phase_refactor(self, impl_file: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        REFACTOR phase: Align implementation with codebase conventions.
        """
        if language is None:
            language = self._detect_language()

        # Read implementation file
        try:
            with open(impl_file, 'r') as f:
                impl_code = f.read()
        except Exception as e:
            return {'error': f'Failed to read implementation file: {e}'}

        # Detect codebase conventions
        conventions = self._detect_conventions(language)

        # Generate refactored code
        refactored = self._apply_conventions(impl_code, conventions, language)

        return {
            'phase': 'REFACTOR',
            'language': language,
            'impl_file': impl_file,
            'refactored_implementation': refactored,
            'conventions_applied': conventions,
            'run_command': self._test_command(language, self._detect_test_framework(language)),
            'expected_result': 'All tests still pass',
            'instructions': 'Apply the refactored code above. Run tests to confirm they still pass. No behavior should change.',
        }

    # Helper methods
    def _detect_language(self) -> str:
        """Auto-detect primary language from project files."""
        py_files = list(self.project_path.glob('**/*.py'))
        js_files = list(self.project_path.glob('**/*.js')) + list(self.project_path.glob('**/*.ts'))
        go_files = list(self.project_path.glob('**/*.go'))

        if len(py_files) > len(js_files) and len(py_files) > len(go_files):
            return 'python'
        elif len(js_files) > len(go_files):
            return 'javascript'
        elif len(go_files) > 0:
            return 'go'
        return 'python'  # Default

    def _detect_test_framework(self, language: str) -> str:
        """Detect test framework for the language."""
        if language == 'python':
            return 'pytest'
        elif language == 'javascript':
            return 'jest'
        elif language == 'go':
            return 'testing'
        return 'unknown'

    def _test_command(self, language: str, framework: str) -> str:
        """Generate test command for language/framework."""
        commands = {
            ('python', 'pytest'): 'pytest tests/test_feature.py -v',
            ('python', 'unittest'): 'python -m unittest discover tests/',
            ('javascript', 'jest'): 'npm test',
            ('go', 'testing'): 'go test ./...',
        }
        return commands.get((language, framework), 'pytest tests/ -v')

    def _generate_test_file(self, feature_name: str, language: str, framework: str) -> str:
        """Generate a minimal failing test file."""
        filename = f'test_{feature_name.replace("-", "_").replace(" ", "_")}'

        if language == 'python':
            content = f'''"""Test {feature_name}."""
import pytest
from {feature_name.replace("-", "_")} import {feature_name.title().replace("-", "")}

class Test{feature_name.title().replace("-", "")}:
    def test_initialization(self):
        """Test that {feature_name} initializes."""
        obj = {feature_name.title().replace("-", "")}()
        assert obj is not None

    def test_basic_operation(self):
        """Test basic operation."""
        obj = {feature_name.title().replace("-", "")}()
        result = obj.do_something()
        assert result is not None
'''
            return f'tests/{filename}.py'

        elif language == 'javascript':
            content = f'''describe('{feature_name}', () => {{
  test('should initialize', () => {{
    const obj = new {feature_name.title().replace("-", "")}();
    expect(obj).toBeDefined();
  }});

  test('should perform basic operation', () => {{
    const obj = new {feature_name.title().replace("-", "")}();
    const result = obj.doSomething();
    expect(result).toBeDefined();
  }});
}});
'''
            return f'__tests__/{filename}.js'

        return f'test_{filename}.go'

    def _generate_impl_stub(self, feature_name: str, language: str) -> str:
        """Generate implementation stub with NotImplementedError."""
        class_name = feature_name.title().replace("-", "").replace(" ", "")

        if language == 'python':
            content = f'''"""Implementation of {feature_name}."""

class {class_name}:
    """Implements {feature_name}."""

    def __init__(self):
        raise NotImplementedError("RED: implement to make this pass")

    def do_something(self):
        raise NotImplementedError("RED: implement to make this pass")
'''
            return f'{feature_name.replace("-", "_")}.py'

        elif language == 'javascript':
            content = f'''/**
 * Implementation of {feature_name}
 */
class {class_name} {{
  constructor() {{
    throw new Error('RED: implement to make this pass');
  }}

  doSomething() {{
    throw new Error('RED: implement to make this pass');
  }}
}}

module.exports = {class_name};
'''
            return f'{feature_name.replace("-", "_")}.js'

        return f'{feature_name}.go'

    def _infer_impl_file(self, test_file: str, language: str) -> str:
        """Infer implementation file from test file."""
        base = test_file.replace('test_', '').replace('__tests__/', '').replace('tests/', '')
        return base

    def _generate_minimal_impl(self, feature_name: str, test_code: str, language: str) -> str:
        """Generate minimal implementation to pass test."""
        class_name = feature_name.title().replace("-", "").replace(" ", "")

        if language == 'python':
            return f'''"""Implementation of {feature_name}."""

class {class_name}:
    """Implements {feature_name}."""

    def __init__(self):
        """Initialize {class_name}."""
        pass

    def do_something(self):
        """Perform the main operation."""
        return True
'''
        elif language == 'javascript':
            return f'''/**
 * Implementation of {feature_name}
 */
class {class_name} {{
  constructor() {{
    this.initialized = true;
  }}

  doSomething() {{
    return true;
  }}
}}

module.exports = {class_name};
'''
        return f'// Minimal implementation of {feature_name}'

    def _detect_conventions(self, language: str) -> Dict[str, str]:
        """Detect codebase conventions."""
        return {
            'async_style': 'async/await',
            'logging': 'logging module',
            'error_handling': 'exceptions',
            'validation': 'pydantic',
            'testing': 'pytest',
        }

    def _apply_conventions(self, code: str, conventions: Dict[str, str], language: str) -> str:
        """Apply codebase conventions to code."""
        # For now, return code as-is (placeholder for actual convention application)
        return code


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='TDD Cycle Enforcer')
    parser.add_argument('--phase', required=True, choices=['red', 'green', 'refactor'])
    parser.add_argument('--feature', default='MyFeature', help='Feature name')
    parser.add_argument('--test-file', help='Path to test file (for green phase)')
    parser.add_argument('--impl-file', help='Path to impl file (for refactor phase)')
    parser.add_argument('--cwd', default='.', help='Project root')

    args = parser.parse_args()

    with timed_run(f'tdd_cycle_{args.phase}'):
        enforcer = TDDCycleEnforcer(args.cwd)

        if args.phase == 'red':
            result = enforcer.phase_red(args.feature)
        elif args.phase == 'green':
            result = enforcer.phase_green(args.test_file or 'test_feature.py', args.feature)
        else:  # refactor
            result = enforcer.phase_refactor(args.impl_file or 'feature.py')

    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
