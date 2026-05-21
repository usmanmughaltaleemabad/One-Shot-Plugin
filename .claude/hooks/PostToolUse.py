"""Post-Tool-Use validation hooks for the one-shot-prompting plugin.

This module implements automated validation checks that run after code generation,
ensuring generated code meets domain standards (GEN-001, GEN-006, etc.).

Standards Reference: .claude/standards/REGISTRY.md
"""

import os
import re
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def check_GEN_001_test_coverage(file_path: str, file_content: str) -> tuple[bool, str]:
    """GEN-001: All generated code must include tests.

    Rule: Every generated file with business logic must have a corresponding test file.

    Scope:
    - Models, services, API endpoints, background jobs: REQUIRED
    - Config files, migrations, type stubs: EXEMPT
    - Mark files with @skip-test comment to exempt
    """

    # Skip non-Python files and test files themselves
    if not file_path.endswith('.py') or file_path.startswith('tests/'):
        return True, "OK"

    # Skip exempted files
    if '@skip-test' in file_content:
        return True, "OK (exempted)"

    # Extract expected test file path
    # Convert: src/models/user.py -> tests/test_models_user.py
    test_file = file_path.replace('src/', 'tests/test_').replace('.py', '.py').replace('/', '_')
    if not test_file.startswith('tests/test_'):
        test_file = f"tests/test_{os.path.basename(file_path)}"

    # Check if test file exists (stub OK)
    if os.path.exists(test_file):
        return True, "OK"

    return False, f"GEN-001 FAIL: No test file found for {file_path}. Expected: {test_file}"


def check_GEN_006_no_secrets(file_path: str, file_content: str) -> tuple[bool, str]:
    """GEN-006: No hardcoded secrets (API keys, passwords, tokens).

    Rule: Generated code must not contain hardcoded credentials, API keys, or secrets.

    Scope:
    - Database passwords, API keys, OAuth tokens
    - Private encryption keys
    - AWS/Azure/GCP credentials

    Enforcement: Hook scans for hardcoded patterns
    """

    # Skip test fixtures marked @unsafe
    if '@unsafe' in file_content:
        return True, "OK (test fixture exempted)"

    # Patterns to detect (regex-based detection)
    secret_patterns = [
        (r'api_key\s*=\s*["\']sk-[a-zA-Z0-9_-]+["\']', 'API key'),
        (r'password\s*=\s*["\'][^"\']{8,}["\']', 'Password'),
        (r'secret\s*=\s*["\'][^"\']{8,}["\']', 'Secret'),
        (r'token\s*=\s*["\'][a-zA-Z0-9_-]{20,}["\']', 'Token'),
        (r'ANTHROPIC_API_KEY\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key'),
        (r'AWS_SECRET_ACCESS_KEY\s*=\s*["\'][^"\']+["\']', 'AWS secret'),
    ]

    for pattern, secret_type in secret_patterns:
        if re.search(pattern, file_content):
            return False, f"GEN-006 FAIL: Hardcoded {secret_type} detected in {file_path}"

    return True, "OK"


def on_tool_write(file_path: str, file_content: str) -> bool:
    """Run all post-write validation checks.

    Args:
        file_path: Path to the generated file
        file_content: Content of the generated file

    Returns:
        True if all checks pass, False if any block-level check fails
    """

    # GEN-001: Test coverage (warning only)
    success, message = check_GEN_001_test_coverage(file_path, file_content)
    if not success:
        logger.warning(message)
        # Don't block; log as warning

    # GEN-006: No hardcoded secrets (error - blocks code)
    success, message = check_GEN_006_no_secrets(file_path, file_content)
    if not success:
        logger.error(message)
        return False  # Block this file!

    return True


# Export for hook integration
__all__ = [
    'check_GEN_001_test_coverage',
    'check_GEN_006_no_secrets',
    'on_tool_write',
]
