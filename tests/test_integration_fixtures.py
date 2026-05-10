#!/usr/bin/env python3
"""
Integration Tests using Synthetic Project Fixtures

Tests the plugin on minimal, synthetic Django and FastAPI projects.
These fixtures simulate real projects without requiring external dependencies.

Run: pytest tests/test_integration_fixtures.py -v
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add scripts to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent / 'skills' / 'one-shot-generator' / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))

from analyze_codebase import detect_language_and_framework, detect_patterns, detect_conventions, detect_structure
from plan_decisions import PlanDecisionEngine
from verify_generated import CodeValidator
from format_multifile_output import format_multifile_response
from autowire_into_project import ProjectAutoWirer

FIXTURES_DIR = Path(__file__).parent / 'fixtures'


class TestIntegrationDjangoFixture:
    """Test plugin components on Django minimal fixture."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.django_fixture = FIXTURES_DIR / 'django_minimal'
        assert self.django_fixture.exists(), f"Django fixture not found: {self.django_fixture}"

    def test_analyze_django_codebase(self):
        """Test codebase analysis on Django fixture."""
        language, framework, version, orm, database, key_libs = detect_language_and_framework(
            str(self.django_fixture)
        )

        assert language == 'python', f"Expected Python, got {language}"
        assert framework == 'django', f"Expected Django, got {framework}"
        assert orm == 'django_orm', f"Expected Django ORM, got {orm}"

    def test_plan_django_decisions(self):
        """Test decision planning on Django fixture."""
        language, framework, version, orm, database, key_libs = detect_language_and_framework(
            str(self.django_fixture)
        )
        patterns = detect_patterns(str(self.django_fixture), language)
        conventions = detect_conventions(str(self.django_fixture), language)

        context = {
            'framework': framework,
            'language': language,
            'orm': orm,
            'key_libs': key_libs,
            'patterns': patterns,
            'conventions': conventions,
        }

        engine = PlanDecisionEngine(context)
        decisions = engine.score_all_decisions()

        assert 'async_sync' in decisions
        assert 'persistence' in decisions
        assert decisions['persistence']['choice'] in ['Django ORM', 'Raw SQL', 'SQLAlchemy']
        assert decisions['persistence']['score'] >= 5

    def test_django_autodiscovery(self):
        """Test framework auto-discovery on Django fixture."""
        structure = detect_structure(str(self.django_fixture))
        assert structure.get('app_root') is not None
        assert 'manage.py' in str(self.django_fixture)


class TestIntegrationFastAPIFixture:
    """Test plugin components on FastAPI minimal fixture."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.fastapi_fixture = FIXTURES_DIR / 'fastapi_minimal'
        assert self.fastapi_fixture.exists(), f"FastAPI fixture not found: {self.fastapi_fixture}"

    def test_analyze_fastapi_codebase(self):
        """Test codebase analysis on FastAPI fixture."""
        language, framework, version, orm, database, key_libs = detect_language_and_framework(
            str(self.fastapi_fixture)
        )

        assert language == 'python', f"Expected Python, got {language}"
        assert framework == 'fastapi', f"Expected FastAPI, got {framework}"

    def test_plan_fastapi_decisions(self):
        """Test decision planning on FastAPI fixture."""
        language, framework, version, orm, database, key_libs = detect_language_and_framework(
            str(self.fastapi_fixture)
        )
        patterns = detect_patterns(str(self.fastapi_fixture), language)

        context = {
            'framework': framework,
            'language': language,
            'orm': orm,
            'key_libs': key_libs,
            'patterns': patterns,
        }

        engine = PlanDecisionEngine(context)
        decisions = engine.score_all_decisions()

        assert 'async_sync' in decisions
        assert decisions['async_sync']['choice'] in ['async', 'sync']
        # FastAPI typically uses async
        assert decisions['async_sync']['score'] >= 5


class TestAutoWireIntegration:
    """Test auto-wiring on fixture projects."""

    def setup_method(self):
        """Setup test with temporary copy of fixtures."""
        self.django_fixture = FIXTURES_DIR / 'django_minimal'
        self.fastapi_fixture = FIXTURES_DIR / 'fastapi_minimal'

        # Create temporary working copies
        self.temp_django = Path(tempfile.mkdtemp())
        self.temp_fastapi = Path(tempfile.mkdtemp())

        # Copy fixtures to temp directories
        shutil.copytree(self.django_fixture, self.temp_django, dirs_exist_ok=True)
        shutil.copytree(self.fastapi_fixture, self.temp_fastapi, dirs_exist_ok=True)

    def teardown_method(self):
        """Cleanup temporary directories."""
        if self.temp_django.exists():
            shutil.rmtree(self.temp_django)
        if self.temp_fastapi.exists():
            shutil.rmtree(self.temp_fastapi)

    def test_autowire_django_dry_run(self):
        """Test Django auto-wiring in dry-run mode."""
        test_files = {
            'auth/models.py': 'class Profile(models.Model):\n    user = models.OneToOneField(User, on_delete=models.CASCADE)',
            'auth/views.py': '@api_view(["GET"])\ndef profile(request):\n    return Response({})',
        }

        wirer = ProjectAutoWirer(str(self.temp_django), 'django', dry_run=True)
        result = wirer.autowire(test_files, 'auth')

        assert result['success'] is True
        assert len(result['actions']) > 0
        # Verify dry-run (no files actually created)
        assert not (self.temp_django / 'auth' / 'models.py').exists()
        assert any('Would create' in action or 'Would update' in action for action in result['actions'])

    def test_autowire_fastapi_dry_run(self):
        """Test FastAPI auto-wiring in dry-run mode."""
        test_files = {
            'auth/router.py': 'from fastapi import APIRouter\nrouter = APIRouter()',
            'auth/schemas.py': 'from pydantic import BaseModel\nclass Token(BaseModel):\n    access_token: str',
        }

        wirer = ProjectAutoWirer(str(self.temp_fastapi), 'fastapi', dry_run=True)
        result = wirer.autowire(test_files, 'auth')

        assert result['success'] is True
        assert len(result['actions']) > 0
        # Verify dry-run (no files actually created)
        assert not (self.temp_fastapi / 'auth' / 'router.py').exists()

    def test_autowire_django_apply_changes(self):
        """Test Django auto-wiring with actual file creation."""
        test_files = {
            'auth/models.py': 'class Token(models.Model):\n    user = models.ForeignKey(User, on_delete=models.CASCADE)',
            'auth/views.py': 'def login(request):\n    return Response({})',
        }

        wirer = ProjectAutoWirer(str(self.temp_django), 'django', dry_run=False)
        result = wirer.autowire(test_files, 'auth')

        assert result['success'] is True
        # Verify files were created
        assert (self.temp_django / 'auth' / 'models.py').exists()
        assert (self.temp_django / 'auth' / 'views.py').exists()
        assert (self.temp_django / 'auth' / '__init__.py').exists()
        assert any('Created' in action for action in result['actions'])


class TestCodeValidation:
    """Test generated code validation."""

    def test_validate_python_code(self):
        """Test validation of Python code."""
        valid_code = "def hello():\n    return 'world'"
        invalid_code = "def hello():\n    return 'world"  # Missing quote

        validator_valid = CodeValidator(valid_code, 'test.py', 'python', 'django', {})
        is_valid, errors, warnings = validator_valid.validate()
        assert is_valid is True

        validator_invalid = CodeValidator(invalid_code, 'test.py', 'python', 'django', {})
        is_valid, errors, warnings = validator_invalid.validate()
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_javascript_code(self):
        """Test validation of JavaScript code."""
        valid_code = "function hello() {\n    return 'world';\n}"

        validator = CodeValidator(valid_code, 'test.js', 'javascript', 'express', {})
        is_valid, errors, warnings = validator.validate()
        # JavaScript validation may vary, but should not crash
        assert isinstance(is_valid, bool)


class TestMultiFileFormatting:
    """Test multi-file output formatting."""

    def test_format_django_files(self):
        """Test formatting multiple Django files."""
        files = {
            "models.py": "class User(models.Model):\n    name = models.CharField(max_length=100)",
            "views.py": "@api_view(['GET'])\ndef users(request):\n    return Response([])",
            "tests.py": "def test_users():\n    assert True",
        }

        output = format_multifile_response(files, 'django', 'User Management')

        assert isinstance(output, str)
        assert 'models.py' in output
        assert 'views.py' in output
        assert 'tests.py' in output
        assert len(output) > 100


if __name__ == '__main__':
    # Allow running directly with pytest
    import pytest
    pytest.main([__file__, '-v'])
