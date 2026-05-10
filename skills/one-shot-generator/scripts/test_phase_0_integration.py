#!/usr/bin/env python3
"""
Phase 0 Integration Tests

Validates all Phase 0 components on real and synthetic codebases.
Run: python test_phase_0_integration.py
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from plan_decisions import PlanDecisionEngine
from verify_generated import CodeValidator


class Phase0Validator:
    """Validates Phase 0 components."""

    def __init__(self):
        self.results = {
            'plan_decisions': [],
            'verify_generated': [],
            'overall': 'PENDING'
        }

    def test_planning_engine_django(self):
        """Test decision scoring on Django codebase."""
        context = {
            'framework': 'django',
            'language': 'python',
            'framework_version': '4.2',
            'package_manager': 'pip',
            'async_patterns': ['asyncio'],
            'orm_usage': True,
            'orm_type': 'django_orm',
            'testing_framework': 'pytest',
            'logging_style': 'structured',
            'error_handling': 'try_except_logging',
            'validation_style': 'model_validators',
            'api_framework': 'rest_framework',
            'codebase_size': 'large',
            'file_count': 150,
            'has_requirements': True,
        }

        engine = PlanDecisionEngine(context)
        decisions = engine.score_all_decisions()

        test = {
            'name': 'Django 4.2 with async + pytest',
            'context': context,
            'decisions': decisions,
            'expected_async': 8.0,  # Should favor async
            'expected_orm': 8.0,    # Should favor Django ORM
            'expected_testing': 8.0, # Should detect pytest
            'passed': all([
                decisions.get('async_decision', {}).get('score', 0) >= 7.0,
                decisions.get('orm_decision', {}).get('score', 0) >= 7.0,
                decisions.get('testing_framework', {}).get('score', 0) >= 7.0,
            ])
        }

        self.results['plan_decisions'].append(test)
        return test['passed']

    def test_planning_engine_fastapi(self):
        """Test decision scoring on FastAPI codebase."""
        context = {
            'framework': 'fastapi',
            'language': 'python',
            'framework_version': '0.95',
            'package_manager': 'pip',
            'async_patterns': ['asyncio', 'async def', 'await'],
            'orm_usage': True,
            'orm_type': 'sqlalchemy',
            'testing_framework': 'pytest',
            'logging_style': 'python_logging',
            'error_handling': 'exceptions',
            'validation_style': 'pydantic',
            'codebase_size': 'medium',
            'file_count': 40,
            'has_requirements': True,
        }

        engine = PlanDecisionEngine(context)
        decisions = engine.score_all_decisions()

        test = {
            'name': 'FastAPI 0.95 with SQLAlchemy + pytest',
            'context': context,
            'decisions': decisions,
            'expected_async': 9.0,     # Should strongly favor async
            'expected_orm': 8.0,       # Should favor SQLAlchemy
            'expected_testing': 8.0,   # Should detect pytest
            'passed': all([
                decisions.get('async_decision', {}).get('score', 0) >= 8.5,
                decisions.get('orm_decision', {}).get('score', 0) >= 7.5,
            ])
        }

        self.results['plan_decisions'].append(test)
        return test['passed']

    def test_planning_engine_spring(self):
        """Test decision scoring on Spring Boot codebase."""
        context = {
            'framework': 'spring',
            'language': 'java',
            'framework_version': '2.7',
            'package_manager': 'maven',
            'async_patterns': ['CompletableFuture', '@Async'],
            'orm_usage': True,
            'orm_type': 'hibernate_jpa',
            'testing_framework': 'junit',
            'logging_style': 'log4j2',
            'error_handling': 'exceptions',
            'validation_style': 'annotations',
            'codebase_size': 'large',
            'file_count': 80,
            'has_pom': True,
        }

        engine = PlanDecisionEngine(context)
        decisions = engine.score_all_decisions()

        test = {
            'name': 'Spring Boot 2.7 with Hibernate + JUnit',
            'context': context,
            'decisions': decisions,
            'expected_orm': 9.0,      # Should favor Hibernate
            'expected_testing': 9.0,  # Should detect JUnit
            'passed': all([
                decisions.get('orm_decision', {}).get('score', 0) >= 8.5,
                decisions.get('testing_framework', {}).get('score', 0) >= 8.5,
            ])
        }

        self.results['plan_decisions'].append(test)
        return test['passed']

    def test_planning_engine_go(self):
        """Test decision scoring on Go codebase."""
        context = {
            'framework': 'go',
            'language': 'go',
            'framework_version': '1.19',
            'package_manager': 'go',
            'async_patterns': ['goroutines', 'channels'],
            'orm_usage': False,
            'orm_type': 'raw_sql',
            'testing_framework': 'testing',
            'logging_style': 'structured',
            'error_handling': 'error_returns',
            'validation_style': 'manual',
            'codebase_size': 'medium',
            'file_count': 25,
            'has_go_mod': True,
        }

        engine = PlanDecisionEngine(context)
        decisions = engine.score_all_decisions()

        test = {
            'name': 'Go 1.19 with goroutines + testing',
            'context': context,
            'decisions': decisions,
            'expected_async': 9.0,    # Go uses async by default
            'expected_orm': 1.0,      # Go typically uses raw SQL
            'passed': all([
                decisions.get('async_decision', {}).get('score', 0) >= 8.5,
                decisions.get('orm_decision', {}).get('score', 0) <= 2.0,
            ])
        }

        self.results['plan_decisions'].append(test)
        return test['passed']

    def test_verification_python_syntax(self):
        """Test Python code syntax validation."""
        validator = CodeValidator(framework='django', language='python')

        # Valid code
        valid_code = """
from django.db import models

class User(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
"""

        result = validator.validate_code(valid_code, 'python', 'django')

        test = {
            'name': 'Python syntax validation (valid code)',
            'code_snippet': 'User model with 3 fields',
            'status': result.get('status'),
            'passed': result.get('status') == 'PASSED'
        }

        self.results['verify_generated'].append(test)
        return test['passed']

    def test_verification_python_syntax_error(self):
        """Test Python code syntax error detection."""
        validator = CodeValidator(framework='django', language='python')

        # Invalid code (missing colon)
        invalid_code = """
from django.db import models

class User(models.Model)
    email = models.EmailField(unique=True)
"""

        result = validator.validate_code(invalid_code, 'python', 'django')

        test = {
            'name': 'Python syntax validation (invalid code)',
            'code_snippet': 'User model with syntax error',
            'status': result.get('status'),
            'passed': result.get('status') in ['REPAIRED', 'FAILED']
        }

        self.results['verify_generated'].append(test)
        return test['passed']

    def test_verification_import_validation(self):
        """Test import validation."""
        validator = CodeValidator(framework='fastapi', language='python')

        # Code with valid imports
        code_with_valid_imports = """
from fastapi import FastAPI
from pydantic import BaseModel
import json

app = FastAPI()

class Item(BaseModel):
    id: int
    name: str
"""

        result = validator.validate_code(code_with_valid_imports, 'python', 'fastapi')

        test = {
            'name': 'Import validation (all valid)',
            'code_snippet': 'FastAPI app with Pydantic',
            'status': result.get('status'),
            'passed': result.get('status') == 'PASSED'
        }

        self.results['verify_generated'].append(test)
        return test['passed']

    def test_verification_framework_compliance(self):
        """Test framework compliance validation."""
        validator = CodeValidator(framework='fastapi', language='python')

        # FastAPI-compliant code
        fastapi_code = """
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.get("/items/")
async def read_items():
    return []

@app.post("/items/")
async def create_item(item: Item):
    return item
"""

        result = validator.validate_code(fastapi_code, 'python', 'fastapi')

        test = {
            'name': 'Framework compliance (FastAPI patterns)',
            'code_snippet': 'FastAPI with Pydantic models',
            'status': result.get('status'),
            'passed': result.get('status') == 'PASSED'
        }

        self.results['verify_generated'].append(test)
        return test['passed']

    def run_all_tests(self):
        """Run all Phase 0 tests."""
        print("\n" + "="*80)
        print("PHASE 0 INTEGRATION TESTS")
        print("="*80 + "\n")

        # Planning Engine Tests
        print("Testing Planning Engine...")
        print("-" * 80)

        results = []
        results.append(("Django 4.2", self.test_planning_engine_django()))
        results.append(("FastAPI 0.95", self.test_planning_engine_fastapi()))
        results.append(("Spring Boot 2.7", self.test_planning_engine_spring()))
        results.append(("Go 1.19", self.test_planning_engine_go()))

        for test_name, passed in results:
            status = "[PASS]" if passed else "[FAIL]"
            print(f"  {status}: {test_name}")

        planning_passed = all(r[1] for r in results)

        # Verification Tests
        print("\nTesting Verification Harness...")
        print("-" * 80)

        verify_results = []
        verify_results.append(("Python syntax (valid)", self.test_verification_python_syntax()))
        verify_results.append(("Python syntax (invalid)", self.test_verification_python_syntax_error()))
        verify_results.append(("Import validation", self.test_verification_import_validation()))
        verify_results.append(("Framework compliance", self.test_verification_framework_compliance()))

        for test_name, passed in verify_results:
            status = "[PASS]" if passed else "[FAIL]"
            print(f"  {status}: {test_name}")

        verification_passed = all(r[1] for r in verify_results)

        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Planning Engine: {'[PASS] ALL PASSED' if planning_passed else '[FAIL] SOME FAILED'}")
        print(f"Verification Harness: {'[PASS] ALL PASSED' if verification_passed else '[FAIL] SOME FAILED'}")
        print(f"Overall: {'[PASS] PHASE 0 READY' if planning_passed and verification_passed else '[FAIL] PHASE 0 NEEDS FIXES'}")
        print("="*80 + "\n")

        self.results['overall'] = 'PASSED' if planning_passed and verification_passed else 'FAILED'

        # Save results
        with open('phase_0_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)

        return planning_passed and verification_passed


if __name__ == '__main__':
    validator = Phase0Validator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)
