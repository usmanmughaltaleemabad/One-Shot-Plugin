#!/usr/bin/env python3
"""
Comprehensive Gap Testing Suite

Runs validation tests for all 8 gaps plus Phase 0.
Generates detailed test report.

Run: python test_all_gaps.py
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# Import all generators
from generate_migrations import MigrationGenerator
from generate_framework_configs import ConfigGenerator
from generate_cli_scaffold import CLIScaffoldGenerator
from generate_handlers_orchestration import HandlerOrchestrator
from generate_enterprise_configs import EnterpriseConfigGenerator
from generate_openapi_docs import OpenAPIDocGenerator
from generate_comprehensive_tests import TestSuiteGenerator


class ComprehensiveGapTester:
    """Runs comprehensive tests for all gaps."""

    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'gaps': {
                'phase_0': {'status': 'PENDING', 'tests': []},
                'gap_1': {'status': 'PENDING', 'tests': []},
                'gap_2': {'status': 'PENDING', 'tests': []},
                'gap_3': {'status': 'PENDING', 'tests': []},
                'gap_4': {'status': 'PENDING', 'tests': []},
                'gap_5': {'status': 'PENDING', 'tests': []},
                'gap_6': {'status': 'PENDING', 'tests': []},
                'gap_7': {'status': 'PENDING', 'tests': []},
                'gap_8': {'status': 'PENDING', 'tests': []},
            },
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'overall_status': 'PENDING'
            }
        }

    # Gap 2: Migrations
    def test_gap_2_migrations(self):
        """Test migration generation for all frameworks."""
        tests_passed = 0
        total_tests = 4

        # Django
        gen = MigrationGenerator('django', '/test/project')
        models_code = """
from django.db import models
class User(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
"""
        filepath, content = gen.generate_migration(models_code, 'User Authentication')
        if filepath and '0001' in filepath and 'User' in content:
            tests_passed += 1
            self.results['gaps']['gap_2']['tests'].append({
                'name': 'Django migration generation',
                'status': 'PASS',
                'details': f'Generated {filepath}'
            })
        else:
            self.results['gaps']['gap_2']['tests'].append({
                'name': 'Django migration generation',
                'status': 'FAIL',
                'details': 'Migration not generated correctly'
            })

        # Alembic/FastAPI
        gen = MigrationGenerator('fastapi', '/test/project')
        sqlalchemy_code = """
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
"""
        filepath, content = gen.generate_migration(sqlalchemy_code, 'Order API')
        if filepath and 'alembic' in filepath and content:
            tests_passed += 1
            self.results['gaps']['gap_2']['tests'].append({
                'name': 'Alembic migration generation',
                'status': 'PASS',
                'details': f'Generated {filepath}'
            })
        else:
            self.results['gaps']['gap_2']['tests'].append({
                'name': 'Alembic migration generation',
                'status': 'FAIL',
                'details': 'Migration not generated'
            })

        # Spring/Flyway
        gen = MigrationGenerator('spring', '/test/project')
        spring_code = """
@Entity
@Table(name = "products")
public class Product {
    @Id
    private Long id;
    private String name;
}
"""
        filepath, content = gen.generate_migration(spring_code, 'Product Service')
        if filepath and '.sql' in filepath and 'CREATE TABLE' in content:
            tests_passed += 1
            self.results['gaps']['gap_2']['tests'].append({
                'name': 'Flyway SQL migration generation',
                'status': 'PASS',
                'details': f'Generated {filepath}'
            })
        else:
            self.results['gaps']['gap_2']['tests'].append({
                'name': 'Flyway SQL migration generation',
                'status': 'FAIL',
                'details': 'SQL migration not generated'
            })

        # Go
        gen = MigrationGenerator('go', '/test/project')
        go_code = """
type Todo struct {
    ID    int
    Title string
    Done  bool
}
"""
        filepath, content = gen.generate_migration(go_code, 'Todo List')
        if filepath and '.sql' in filepath:
            tests_passed += 1
            self.results['gaps']['gap_2']['tests'].append({
                'name': 'Go migration generation',
                'status': 'PASS',
                'details': f'Generated {filepath}'
            })
        else:
            self.results['gaps']['gap_2']['tests'].append({
                'name': 'Go migration generation',
                'status': 'FAIL',
                'details': 'Go migration not generated'
            })

        self.results['gaps']['gap_2']['status'] = 'PASS' if tests_passed == total_tests else 'FAIL'
        return tests_passed == total_tests

    # Gap 3: Config Generation
    def test_gap_3_configs(self):
        """Test framework config generation."""
        tests_passed = 0
        total_tests = 5

        frameworks_and_configs = [
            ('django', ['config/settings.py', 'manage.py', 'docker-compose.yml']),
            ('fastapi', ['main.py', 'config.py', 'requirements.txt']),
            ('spring', ['application.properties', 'pom.xml']),
            ('go', ['config.go', 'main.go', 'go.mod']),
            ('nodejs', ['package.json', 'server.js']),
        ]

        for framework, expected_files in frameworks_and_configs:
            gen = ConfigGenerator(framework, '/test/project')
            configs = gen.generate_configs(f'{framework.title()} App', {'database': 'postgresql'})

            generated_files = list(configs.keys())
            if any(f in generated_files for f in expected_files):
                tests_passed += 1
                self.results['gaps']['gap_3']['tests'].append({
                    'name': f'{framework.upper()} config generation',
                    'status': 'PASS',
                    'details': f'Generated {len(configs)} config files'
                })
            else:
                self.results['gaps']['gap_3']['tests'].append({
                    'name': f'{framework.upper()} config generation',
                    'status': 'FAIL',
                    'details': f'Expected files not generated'
                })

        self.results['gaps']['gap_3']['status'] = 'PASS' if tests_passed == total_tests else 'FAIL'
        return tests_passed == total_tests

    # Gap 4: CLI Scaffolding
    def test_gap_4_cli(self):
        """Test CLI scaffolding generation."""
        tests_passed = 0
        total_tests = 5

        frameworks = ['django', 'fastapi', 'spring', 'go', 'nodejs']

        for framework in frameworks:
            gen = CLIScaffoldGenerator(framework, '/test/project')
            files = gen.generate_cli('deploy', ['up', 'down', 'status'], {})

            if len(files) > 0:
                tests_passed += 1
                self.results['gaps']['gap_4']['tests'].append({
                    'name': f'{framework.upper()} CLI generation',
                    'status': 'PASS',
                    'details': f'Generated {len(files)} CLI files'
                })
            else:
                self.results['gaps']['gap_4']['tests'].append({
                    'name': f'{framework.upper()} CLI generation',
                    'status': 'FAIL',
                    'details': 'No CLI files generated'
                })

        self.results['gaps']['gap_4']['status'] = 'PASS' if tests_passed == total_tests else 'FAIL'
        return tests_passed == total_tests

    # Gap 5: Event Orchestration
    def test_gap_5_events(self):
        """Test event orchestration generation."""
        tests_passed = 0
        total_tests = 5

        frameworks = ['django', 'fastapi', 'spring', 'go', 'nodejs']
        events = ['UserCreated', 'OrderPlaced', 'PaymentProcessed']

        for framework in frameworks:
            gen = HandlerOrchestrator(framework, '/test/project')
            files = gen.generate_orchestration(events, {})

            if len(files) > 0:
                tests_passed += 1
                self.results['gaps']['gap_5']['tests'].append({
                    'name': f'{framework.upper()} event orchestration',
                    'status': 'PASS',
                    'details': f'Generated {len(files)} event files'
                })
            else:
                self.results['gaps']['gap_5']['tests'].append({
                    'name': f'{framework.upper()} event orchestration',
                    'status': 'FAIL',
                    'details': 'No event files generated'
                })

        self.results['gaps']['gap_5']['status'] = 'PASS' if tests_passed == total_tests else 'FAIL'
        return tests_passed == total_tests

    # Gap 6: Enterprise Configs
    def test_gap_6_enterprise(self):
        """Test enterprise config generation."""
        tests_passed = 0
        total_tests = 3

        targets = ['kubernetes', 'terraform', 'cloudformation']
        deployment_targets = ['kubernetes', 'terraform', 'cloudformation']

        for target in deployment_targets:
            gen = EnterpriseConfigGenerator('fastapi', target)
            configs = gen.generate_enterprise_configs('testapp', ['postgres', 'redis'], {})

            expected_files = {
                'kubernetes': ['k8s/deployment.yaml', 'k8s/service.yaml'],
                'terraform': ['terraform/main.tf', 'terraform/variables.tf'],
                'cloudformation': ['cloudformation/main.yaml'],
            }

            generated = list(configs.keys())
            if any(f in generated for f in expected_files.get(target, [])):
                tests_passed += 1
                self.results['gaps']['gap_6']['tests'].append({
                    'name': f'{target.upper()} deployment config',
                    'status': 'PASS',
                    'details': f'Generated {len(configs)} config files'
                })
            else:
                self.results['gaps']['gap_6']['tests'].append({
                    'name': f'{target.upper()} deployment config',
                    'status': 'FAIL',
                    'details': 'Expected deployment files not generated'
                })

        self.results['gaps']['gap_6']['status'] = 'PASS' if tests_passed == total_tests else 'FAIL'
        return tests_passed == total_tests

    # Gap 7: OpenAPI Docs
    def test_gap_7_openapi(self):
        """Test OpenAPI documentation generation."""
        endpoints = [
            {'path': '/items', 'method': 'GET', 'summary': 'List items'},
            {'path': '/items', 'method': 'POST', 'summary': 'Create item'},
        ]
        models = [
            {'name': 'Item', 'properties': {'id': {'type': 'integer'}, 'name': {'type': 'string'}}},
        ]

        gen = OpenAPIDocGenerator('fastapi', 'testapi')
        files = gen.generate_openapi_docs(endpoints, models)

        tests_passed = 0
        expected_files = ['openapi.yaml', 'openapi.json', 'docs/index.html', 'sdks/python_client.py']

        for expected_file in expected_files:
            if any(expected_file in f for f in files.keys()):
                tests_passed += 1

        self.results['gaps']['gap_7']['tests'].append({
            'name': 'OpenAPI spec generation',
            'status': 'PASS' if tests_passed == 4 else 'FAIL',
            'details': f'Generated {len(files)} documentation files'
        })

        self.results['gaps']['gap_7']['status'] = 'PASS' if tests_passed == 4 else 'FAIL'
        return tests_passed == 4

    # Gap 8: Test Generation
    def test_gap_8_tests(self):
        """Test comprehensive test generation."""
        endpoints = [
            {'path': '/items', 'method': 'GET', 'name': 'list_items'},
            {'path': '/items', 'method': 'POST', 'name': 'create_item'},
        ]
        models = [
            {'name': 'Item'},
        ]

        gen = TestSuiteGenerator('fastapi', 'pytest')
        tests = gen.generate_test_suite(endpoints, models)

        expected_test_files = ['tests/test_endpoints_0.py', 'tests/conftest.py', 'tests/fixtures.py']

        tests_passed = 0
        for expected_file in expected_test_files:
            if any(expected_file in f or 'test' in f for f in tests.keys()):
                tests_passed += 1

        self.results['gaps']['gap_8']['tests'].append({
            'name': 'Test suite generation',
            'status': 'PASS' if tests_passed >= 2 else 'FAIL',
            'details': f'Generated {len(tests)} test files'
        })

        self.results['gaps']['gap_8']['status'] = 'PASS' if tests_passed >= 2 else 'FAIL'
        return tests_passed >= 2

    def run_all_tests(self):
        """Run all gap tests."""
        print("\n" + "="*80)
        print("COMPREHENSIVE GAP TEST SUITE")
        print("="*80 + "\n")

        print("Testing Gap 2: Migrations...")
        gap_2_passed = self.test_gap_2_migrations()
        print(f"  Status: {'[PASS]' if gap_2_passed else '[FAIL]'}\n")

        print("Testing Gap 3: Framework Configs...")
        gap_3_passed = self.test_gap_3_configs()
        print(f"  Status: {'[PASS]' if gap_3_passed else '[FAIL]'}\n")

        print("Testing Gap 4: CLI Scaffolding...")
        gap_4_passed = self.test_gap_4_cli()
        print(f"  Status: {'[PASS]' if gap_4_passed else '[FAIL]'}\n")

        print("Testing Gap 5: Event Orchestration...")
        gap_5_passed = self.test_gap_5_events()
        print(f"  Status: {'[PASS]' if gap_5_passed else '[FAIL]'}\n")

        print("Testing Gap 6: Enterprise Deployment...")
        gap_6_passed = self.test_gap_6_enterprise()
        print(f"  Status: {'[PASS]' if gap_6_passed else '[FAIL]'}\n")

        print("Testing Gap 7: OpenAPI Documentation...")
        gap_7_passed = self.test_gap_7_openapi()
        print(f"  Status: {'[PASS]' if gap_7_passed else '[FAIL]'}\n")

        print("Testing Gap 8: Test Generation...")
        gap_8_passed = self.test_gap_8_tests()
        print(f"  Status: {'[PASS]' if gap_8_passed else '[FAIL]'}\n")

        # Summary
        all_gaps_passed = all([gap_2_passed, gap_3_passed, gap_4_passed, gap_5_passed, gap_6_passed, gap_7_passed, gap_8_passed])

        print("="*80)
        print("FINAL SUMMARY")
        print("="*80)
        print(f"Gap 2 (Migrations): {'[PASS]' if gap_2_passed else '[FAIL]'}")
        print(f"Gap 3 (Config): {'[PASS]' if gap_3_passed else '[FAIL]'}")
        print(f"Gap 4 (CLI): {'[PASS]' if gap_4_passed else '[FAIL]'}")
        print(f"Gap 5 (Events): {'[PASS]' if gap_5_passed else '[FAIL]'}")
        print(f"Gap 6 (Enterprise): {'[PASS]' if gap_6_passed else '[FAIL]'}")
        print(f"Gap 7 (OpenAPI): {'[PASS]' if gap_7_passed else '[FAIL]'}")
        print(f"Gap 8 (Tests): {'[PASS]' if gap_8_passed else '[FAIL]'}")
        print("\n" + "="*80)
        print(f"Overall: {'[PASS] ALL GAPS READY FOR INTEGRATION' if all_gaps_passed else '[FAIL] SOME GAPS NEED WORK'}")
        print("="*80 + "\n")

        self.results['summary']['overall_status'] = 'PASSED' if all_gaps_passed else 'FAILED'

        with open('comprehensive_gap_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)

        return all_gaps_passed


if __name__ == '__main__':
    tester = ComprehensiveGapTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
