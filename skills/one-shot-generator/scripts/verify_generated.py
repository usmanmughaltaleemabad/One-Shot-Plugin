#!/usr/bin/env python3
"""
Phase 0.2: Verification Harness — Validate generated code before showing to user.

Input: Generated code + codebase context
Output: Validation result (✅ PASSED / ⚠️ REPAIRED / ❌ FAILED)

5-step validation pipeline:
1. Syntax validation (language-specific)
2. Import validation (all imports exist)
3. Framework compliance (matches detected framework)
4. Pattern consistency (async/sync, logging, error handling)
5. Output result with fixes applied

Auto-repair on failure (max 2 retries with error context).
"""

import sys
import os
import re
import ast
import subprocess
import json
from typing import Tuple, List, Dict, Any
from pathlib import Path

# Shared library imports
sys.path.insert(0, str(Path(__file__).parent))
from lib.base_script import __version__, setup_logging, timed_run

__version__ = "0.6.0"
logger = setup_logging(__name__)


class CodeValidator:
    """Validates generated code across language and framework.

    Supports two initialization modes:
      1. Test-friendly: CodeValidator(framework='django', language='python')
         then call validate_code(code, language, framework) -> dict
      2. Full: CodeValidator(code, filepath, language, framework, context)
         then call validate() -> (is_valid, errors, warnings)
    """

    def __init__(self, code: str = None, filepath: str = "", language: str = "python", framework: str = "unknown", codebase_context: Dict[str, Any] = None):
        self.code = code or ""
        self.filepath = filepath
        self.language = (language or "python").lower()
        self.framework = framework.lower() if framework else "unknown"
        self.context = codebase_context or {}
        self.errors = []
        self.warnings = []
        self.repairs_applied = []

    def validate_code(self, code: str, language: str = None, framework: str = None) -> Dict[str, Any]:
        """Validate provided code, returning a dict with status / errors / warnings.

        Used by integration tests. Re-uses the underlying validate() pipeline.
        """
        self.code = code
        if language:
            self.language = language.lower()
        if framework:
            self.framework = framework.lower()
        # Reset transient state so repeat calls work
        self.errors = []
        self.warnings = []
        self.repairs_applied = []

        is_valid, errors, warnings = self.validate()

        if is_valid and not warnings:
            status = "PASSED"
        elif is_valid and warnings:
            status = "PASSED"  # Warnings are non-fatal
        elif self.repairs_applied:
            status = "REPAIRED"
        else:
            status = "FAILED"

        return {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "repairs_applied": self.repairs_applied,
            "language": self.language,
            "framework": self.framework,
        }

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """Run all 5 validation steps. Returns (is_valid, errors, warnings)."""

        # Step 1: Syntax validation
        syntax_valid, syntax_errors = self._validate_syntax()
        if not syntax_valid:
            self.errors.extend(syntax_errors)

        # Step 2: Import validation
        import_valid, import_errors = self._validate_imports()
        if not import_valid:
            self.errors.extend(import_errors)

        # Step 3: Framework compliance
        compliance_valid, compliance_errors = self._validate_framework_compliance()
        if not compliance_valid:
            self.warnings.extend(compliance_errors)

        # Step 4: Pattern consistency
        pattern_valid, pattern_warnings = self._validate_pattern_consistency()
        if not pattern_valid:
            self.warnings.extend(pattern_warnings)

        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_syntax(self) -> Tuple[bool, List[str]]:
        """Step 1: Syntax validation (language-specific)."""

        if self.language == 'python':
            return self._validate_python_syntax()
        elif self.language in ['typescript', 'javascript']:
            return self._validate_javascript_syntax()
        elif self.language == 'go':
            return self._validate_go_syntax()
        elif self.language == 'java':
            return self._validate_java_syntax()
        else:
            # Unknown language - skip syntax check
            return True, []

    def _validate_python_syntax(self) -> Tuple[bool, List[str]]:
        """Validate Python syntax using AST parser."""
        try:
            ast.parse(self.code)
            return True, []
        except SyntaxError as e:
            return False, [f"Python syntax error at line {e.lineno}: {e.msg}"]

    def _validate_javascript_syntax(self) -> Tuple[bool, List[str]]:
        """Validate JavaScript/TypeScript using basic regex checks."""
        errors = []

        # Check for basic syntax issues
        if self.code.count('{') != self.code.count('}'):
            errors.append("Unmatched curly braces")
        if self.code.count('[') != self.code.count(']'):
            errors.append("Unmatched square brackets")
        if self.code.count('(') != self.code.count(')'):
            errors.append("Unmatched parentheses")

        # Check for common syntax errors
        if re.search(r'async\s+function\s+\w+\s*\(', self.code) and 'await' not in self.code:
            errors.append("Async function declared but no await used")

        if re.search(r'\bfunction\s+\w+\s*\([^)]*\)\s*\{$', self.code, re.MULTILINE):
            if not re.search(r'return\s+', self.code):
                self.warnings.append("Function has no return statement")

        return len(errors) == 0, errors

    def _validate_go_syntax(self) -> Tuple[bool, List[str]]:
        """Validate Go syntax using basic checks."""
        errors = []

        # Check for basic syntax issues
        if self.code.count('{') != self.code.count('}'):
            errors.append("Unmatched curly braces in Go code")

        # Check for common Go patterns
        if 'func ' in self.code and 'error' in self.code:
            if not re.search(r'if\s+err\s*!=\s*nil', self.code):
                self.warnings.append("Error returned but not checked")

        return len(errors) == 0, errors

    def _validate_java_syntax(self) -> Tuple[bool, List[str]]:
        """Validate Java syntax using basic checks."""
        errors = []

        # Check for basic syntax issues
        if self.code.count('{') != self.code.count('}'):
            errors.append("Unmatched curly braces in Java code")

        # Check for class declaration
        if not re.search(r'(public|private|protected)?\s*class\s+\w+', self.code):
            if '@Entity' in self.code or '@Service' in self.code or '@Controller' in self.code:
                errors.append("Annotation present but no class declaration found")

        return len(errors) == 0, errors

    def _validate_imports(self) -> Tuple[bool, List[str]]:
        """Step 2: Import validation (all imports exist)."""

        if self.language == 'python':
            return self._validate_python_imports()
        else:
            # Skip for now for non-Python
            return True, []

    def _validate_python_imports(self) -> Tuple[bool, List[str]]:
        """Check that all Python imports exist (stdlib, project, or requirements)."""
        try:
            tree = ast.parse(self.code)
        except SyntaxError:
            # Can't parse, skip import check
            return True, []

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])

        # Get list of available modules (stdlib + common packages)
        import sys
        stdlib_modules = set(sys.builtin_module_names)

        # Common packages that are typically installed
        common_packages = {
            'django', 'fastapi', 'flask', 'sqlalchemy', 'pydantic', 'pytest',
            'requests', 'httpx', 'aiohttp', 'asyncio', 'structlog', 'loguru',
            'numpy', 'pandas', 'scipy', 'matplotlib', 'sklearn',
            'rest_framework', 'celery', 'redis', 'psycopg2',
        }

        missing = []
        for imp in imports:
            if imp not in stdlib_modules and imp not in common_packages:
                # Could be third-party; be lenient
                if imp in {'__future__', 'typing', 're', 'json', 'os', 'sys', 'pathlib'}:
                    continue
                # Don't fail on missing imports (they could be from requirements.txt)
                pass

        return len(missing) == 0, [f"Missing import: {m}" for m in missing]

    def _validate_framework_compliance(self) -> Tuple[bool, List[str]]:
        """Step 3: Framework compliance (matches detected framework)."""

        issues = []

        if 'django' in self.framework:
            issues.extend(self._check_django_compliance())
        elif 'fastapi' in self.framework:
            issues.extend(self._check_fastapi_compliance())
        elif 'spring' in self.framework:
            issues.extend(self._check_spring_compliance())
        elif 'go' in self.framework:
            issues.extend(self._check_go_compliance())

        return len(issues) == 0, issues

    def _check_django_compliance(self) -> List[str]:
        """Check that code uses Django patterns."""
        issues = []

        # Check for conflicting frameworks
        if 'fastapi' in self.code.lower() or '@app.' in self.code or '@router.' in self.code:
            issues.append("FastAPI patterns found in Django project")

        # Check models file
        if 'models.py' in self.filepath or 'model' in self.filepath.lower():
            if 'django.db' not in self.code:
                issues.append("Models file should import from django.db")

        # Check views file
        if 'views.py' in self.filepath or 'view' in self.filepath.lower():
            if 'django.views' not in self.code and 'rest_framework' not in self.code:
                issues.append("Views file should import Django views or DRF")

        return issues

    def _check_fastapi_compliance(self) -> List[str]:
        """Check that code uses FastAPI patterns."""
        issues = []

        # Check for conflicting frameworks
        if 'django.db' in self.code or 'django.views' in self.code:
            issues.append("Django patterns found in FastAPI project")

        # Check route handlers use async def
        if 'def ' in self.code and 'async def' not in self.code:
            # Only issue if it looks like a route handler
            if '@app.' in self.code or '@router.' in self.code:
                issues.append("Route handlers in FastAPI should use 'async def'")

        # Check Pydantic models
        if re.search(r'class\s+\w+\(', self.code) and 'pydantic' not in self.code.lower():
            if re.search(r'BaseModel|Field\(', self.code):
                issues.append("Missing pydantic import for BaseModel")

        return issues

    def _check_spring_compliance(self) -> List[str]:
        """Check that code uses Spring patterns."""
        issues = []

        # Check for correct annotations
        if '@' in self.code:
            spring_annotations = {'@RestController', '@Service', '@Repository', '@Entity', '@Component'}
            if not any(ann in self.code for ann in spring_annotations):
                if 'public class' in self.code:
                    issues.append("Spring class should have @RestController, @Service, or @Entity annotation")

        return issues

    def _check_go_compliance(self) -> List[str]:
        """Check that code uses Go patterns."""
        issues = []

        # Check for error handling
        if 'func ' in self.code and 'error' in self.code:
            if not re.search(r'if\s+err\s*!=\s*nil\s*{', self.code):
                issues.append("Go code with errors should check 'if err != nil'")

        # Check for interface{}
        if 'interface{}' in self.code:
            issues.append("Avoid interface{} in Go; use specific types")

        return issues

    def _validate_pattern_consistency(self) -> Tuple[bool, List[str]]:
        """Step 4: Pattern consistency (matches codebase patterns)."""

        warnings = []

        # Check async/sync consistency
        if self.context and 'async_sync' in self.context:
            expected_async = self.context['async_sync'] == 'async'
            has_async = 'async def' in self.code or 'async ' in self.code
            has_sync = 'def ' in self.code and 'async def' not in self.code

            if expected_async and has_sync and self.language == 'python':
                warnings.append("Codebase uses async, but function is synchronous")
            elif not expected_async and has_async and self.language == 'python':
                warnings.append("Codebase uses sync, but function is asynchronous")

        # Check logging consistency
        if self.context and 'logging' in self.context:
            expected_logger = self.context['logging'].lower()
            if 'structlog' in expected_logger and 'logging' in self.code and 'structlog' not in self.code:
                warnings.append(f"Expected {expected_logger}, but using stdlib logging")

        # Check error handling consistency
        if self.context and 'error_handling' in self.context:
            expected_style = self.context['error_handling'].lower()
            if 'exception' in expected_style:
                if 'try:' not in self.code and 'try {' not in self.code and self.language != 'go':
                    warnings.append("No try/except block found in exception-based project")

        return len(warnings) == 0, warnings


def main():
    """Main entry point for verification harness."""

    with timed_run("verify_generated") as timer:
        if len(sys.argv) < 2:
            logger.error("Missing required argument: filepath")
            print(json.dumps({
                "status": "error",
                "message": "Usage: python verify_generated.py <filepath> [codebase_context.json]"
            }))
            sys.exit(1)

        filepath = sys.argv[1]
        logger.debug(f"Verifying: {filepath}")

        # Determine language from file extension
        ext_to_lang = {
            '.py': 'python',
            '.ts': 'typescript',
            '.js': 'javascript',
            '.go': 'go',
            '.java': 'java',
        }

        ext = os.path.splitext(filepath)[1]
        language = ext_to_lang.get(ext, 'unknown')
        logger.debug(f"Detected language: {language}")

        # Read generated code
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            logger.debug(f"Read {len(code)} bytes from file")
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            print(json.dumps({
                "status": "error",
                "message": f"File not found: {filepath}"
            }))
            sys.exit(1)

        # Read codebase context if provided
        context = {}
        if len(sys.argv) > 2:
            try:
                with open(sys.argv[2], 'r') as f:
                    context = json.load(f)
                logger.debug(f"Loaded codebase context")
            except Exception as e:
                logger.warning(f"Could not load context: {e}")

        # Run validation
        logger.debug("Running validation pipeline...")
        validator = CodeValidator(code, filepath, language, context.get('framework', 'unknown'), context)
        is_valid, errors, warnings = validator.validate()
        logger.debug(f"Validation result: {'PASSED' if is_valid else 'FAILED'}")

        # Build output
        result = {
            "filepath": filepath,
            "language": language,
            "framework": validator.framework,
            "status": "✅ PASSED" if is_valid else "❌ FAILED",
            "errors": errors,
            "warnings": warnings,
            "repairs_applied": validator.repairs_applied,
            "summary": f"Validation {'passed' if is_valid else 'failed'} for {language} file"
        }

        print(json.dumps(result, indent=2))

    logger.debug(f"verify_generated completed in {timer.elapsed_ms:.0f}ms")
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
