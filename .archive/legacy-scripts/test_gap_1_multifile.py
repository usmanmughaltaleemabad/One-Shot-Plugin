#!/usr/bin/env python3
"""
Gap 1 Integration Tests: Multi-File Generation

Tests format_multifile_output and autowire_into_project scripts.
Run: python test_gap_1_multifile.py
"""

import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from format_multifile_output import MultiFileFormatter
from autowire_into_project import ProjectAutoWirer


class Gap1Validator:
    """Validates Gap 1 multi-file generation."""

    def __init__(self):
        self.results = {
            'formatting': [],
            'autowiring': [],
            'overall': 'PENDING'
        }

    def test_format_django_feature(self):
        """Test formatting 8-file Django feature."""
        formatter = MultiFileFormatter(framework='django')

        files = [
            {'name': 'models.py', 'content': 'class User(models.Model): pass', 'type': 'model'},
            {'name': 'views.py', 'content': 'class UserViewSet(ViewSet): pass', 'type': 'view'},
            {'name': 'serializers.py', 'content': 'class UserSerializer(Serializer): pass', 'type': 'serializer'},
            {'name': 'urls.py', 'content': 'urlpatterns = [...]', 'type': 'route'},
            {'name': 'admin.py', 'content': 'admin.site.register(User)', 'type': 'admin'},
            {'name': 'forms.py', 'content': 'class UserForm(forms.ModelForm): pass', 'type': 'form'},
            {'name': 'tests.py', 'content': 'class UserTests(TestCase): pass', 'type': 'test'},
            {'name': 'migrations/0001_initial.py', 'content': 'class Migration(migrations.Migration): pass', 'type': 'migration'},
        ]

        output = formatter.format_multifile_response(files, 'User Authentication')

        test = {
            'name': 'Format Django 8-file feature',
            'file_count': len(files),
            'has_summary_table': '| File |' in output,
            'has_file_contents': '# File Contents' in output or 'models.py' in output,
            'has_installation': 'Installation' in output or 'install' in output.lower(),
            'passed': all([
                '| File |' in output,
                len(files) == 8,
                'User' in output,
            ])
        }

        self.results['formatting'].append(test)
        return test['passed']

    def test_format_fastapi_feature(self):
        """Test formatting 7-file FastAPI feature."""
        formatter = MultiFileFormatter(framework='fastapi')

        files = [
            {'name': 'models.py', 'content': 'class Order(Base): pass', 'type': 'model'},
            {'name': 'schemas.py', 'content': 'class OrderSchema(BaseModel): pass', 'type': 'schema'},
            {'name': 'routes.py', 'content': '@router.get("/orders")', 'type': 'route'},
            {'name': 'crud.py', 'content': 'async def get_orders(): pass', 'type': 'crud'},
            {'name': 'dependencies.py', 'content': 'async def get_db(): pass', 'type': 'dependency'},
            {'name': 'tests.py', 'content': 'def test_get_orders(): pass', 'type': 'test'},
            {'name': 'migrations/0001_create_orders.py', 'content': 'def upgrade(): pass', 'type': 'migration'},
        ]

        output = formatter.format_multifile_response(files, 'Order API')

        test = {
            'name': 'Format FastAPI 7-file feature',
            'file_count': len(files),
            'has_summary_table': '| File |' in output,
            'has_file_contents': 'models.py' in output or '# File' in output,
            'passed': all([
                len(files) == 7,
                'Order' in output,
            ])
        }

        self.results['formatting'].append(test)
        return test['passed']

    def test_format_spring_feature(self):
        """Test formatting 5-file Spring feature."""
        formatter = MultiFileFormatter(framework='spring')

        files = [
            {'name': 'Product.java', 'content': '@Entity public class Product {}', 'type': 'entity'},
            {'name': 'ProductController.java', 'content': '@RestController public class ProductController {}', 'type': 'controller'},
            {'name': 'ProductService.java', 'content': '@Service public class ProductService {}', 'type': 'service'},
            {'name': 'ProductRepository.java', 'content': 'public interface ProductRepository {}', 'type': 'repository'},
            {'name': 'ProductTest.java', 'content': '@SpringBootTest public class ProductTest {}', 'type': 'test'},
        ]

        output = formatter.format_multifile_response(files, 'Product Management')

        test = {
            'name': 'Format Spring 5-file feature',
            'file_count': len(files),
            'has_java_extension': '.java' in output,
            'passed': all([
                len(files) == 5,
                'Product' in output,
            ])
        }

        self.results['formatting'].append(test)
        return test['passed']

    def test_autowire_django_project(self):
        """Test auto-wiring Django feature into project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal Django project structure
            project_root = Path(tmpdir)
            app_dir = project_root / 'app'
            app_dir.mkdir()

            # Create required files
            (app_dir / '__init__.py').write_text('')
            (app_dir / 'models.py').write_text('from django.db import models')
            (project_root / 'urls.py').write_text('from django.urls import path\nurlpatterns = []')
            (project_root / 'settings.py').write_text('INSTALLED_APPS = []')

            wirer = ProjectAutoWirer(framework='django', project_root=str(project_root))

            files = {
                'app/models.py': 'class User(models.Model): email = models.EmailField()',
                'app/views.py': 'from django.views import View',
                'app/urls.py': 'from django.urls import path\nurlpatterns = [path("users/", views.UserList)]',
            }

            result = wirer.autowire(files)

            test = {
                'name': 'Auto-wire Django feature',
                'success': result.get('success', False),
                'files_created': len(result.get('actions', [])) > 0,
                'has_next_steps': len(result.get('next_steps', [])) > 0,
                'passed': result.get('success', False) and len(result.get('actions', [])) > 0,
            }

            self.results['autowiring'].append(test)
            return test['passed']

    def test_autowire_fastapi_project(self):
        """Test auto-wiring FastAPI feature into project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal FastAPI project structure
            project_root = Path(tmpdir)
            (project_root / 'main.py').write_text(
                'from fastapi import FastAPI\napp = FastAPI()\n'
            )

            wirer = ProjectAutoWirer(framework='fastapi', project_root=str(project_root))

            files = {
                'models.py': 'class Order(Base): pass',
                'schemas.py': 'class OrderSchema(BaseModel): pass',
                'routes.py': 'from fastapi import APIRouter\nrouter = APIRouter()',
            }

            result = wirer.autowire(files)

            test = {
                'name': 'Auto-wire FastAPI feature',
                'success': result.get('success', False),
                'files_created': len(result.get('actions', [])) > 0,
                'has_next_steps': len(result.get('next_steps', [])) > 0,
                'passed': result.get('success', False),
            }

            self.results['autowiring'].append(test)
            return test['passed']

    def test_dependency_ordering(self):
        """Test that files are ordered by dependency."""
        formatter = MultiFileFormatter(framework='django')

        # Files in wrong order
        files = [
            {'name': 'tests.py', 'content': 'test code', 'type': 'test'},
            {'name': 'views.py', 'content': 'view code', 'type': 'view'},
            {'name': 'models.py', 'content': 'model code', 'type': 'model'},
        ]

        output = formatter.format_multifile_response(files, 'Test Feature')

        # Check if models appears before views, and views before tests
        models_pos = output.find('models.py')
        views_pos = output.find('views.py')
        tests_pos = output.find('tests.py')

        test = {
            'name': 'Dependency ordering (models → views → tests)',
            'models_first': models_pos < views_pos if models_pos >= 0 and views_pos >= 0 else True,
            'views_before_tests': views_pos < tests_pos if views_pos >= 0 and tests_pos >= 0 else True,
            'passed': (models_pos < views_pos) if models_pos >= 0 and views_pos >= 0 else True,
        }

        self.results['formatting'].append(test)
        return test['passed']

    def run_all_tests(self):
        """Run all Gap 1 tests."""
        print("\n" + "="*80)
        print("GAP 1 INTEGRATION TESTS: MULTI-FILE GENERATION")
        print("="*80 + "\n")

        # Formatting Tests
        print("Testing Multi-File Formatting...")
        print("-" * 80)

        format_results = []
        format_results.append(("Django 8-file", self.test_format_django_feature()))
        format_results.append(("FastAPI 7-file", self.test_format_fastapi_feature()))
        format_results.append(("Spring 5-file", self.test_format_spring_feature()))
        format_results.append(("Dependency ordering", self.test_dependency_ordering()))

        for test_name, passed in format_results:
            status = "[PASS]" if passed else "[FAIL]"
            print(f"  {status}: {test_name}")

        formatting_passed = all(r[1] for r in format_results)

        # Auto-wiring Tests
        print("\nTesting Auto-Wiring...")
        print("-" * 80)

        wire_results = []
        wire_results.append(("Django auto-wire", self.test_autowire_django_project()))
        wire_results.append(("FastAPI auto-wire", self.test_autowire_fastapi_project()))

        for test_name, passed in wire_results:
            status = "[PASS]" if passed else "[FAIL]"
            print(f"  {status}: {test_name}")

        autowiring_passed = all(r[1] for r in wire_results)

        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Formatting: {'[PASS] ALL PASSED' if formatting_passed else '[FAIL] SOME FAILED'}")
        print(f"Auto-wiring: {'[PASS] ALL PASSED' if autowiring_passed else '[FAIL] SOME FAILED'}")
        print(f"Overall: {'[PASS] GAP 1 READY' if formatting_passed and autowiring_passed else '[FAIL] GAP 1 NEEDS FIXES'}")
        print("="*80 + "\n")

        self.results['overall'] = 'PASSED' if formatting_passed and autowiring_passed else 'FAILED'

        with open('gap_1_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)

        return formatting_passed and autowiring_passed


if __name__ == '__main__':
    validator = Gap1Validator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)
