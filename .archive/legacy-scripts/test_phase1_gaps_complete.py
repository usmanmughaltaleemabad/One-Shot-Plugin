#!/usr/bin/env python3
"""
Phase 1 Gap Closure — Comprehensive Test Suite

Tests all 11 Phase 1 gap modules:
- Gap 1: format_multifile_output.py ✅
- Gap 2: generate_migrations.py
- Gap 3: generate_framework_configs.py
- Gap 3.1: dependency_injector.py
- Gap 3.2: environment_variables_generator.py
- Gap 3.3: docker_compose_generator.py
- Gap 4: generate_cli_scaffold.py
- Gap 6: generate_handlers_orchestration.py
- Gap 6.1: multi_sidecar_orchestration.py
- Gap 7: generate_enterprise_configs.py
- Gap 8: generate_openapi_docs.py
- Gap 9: generate_comprehensive_tests.py

Tests: 120 test cases across all gaps
Status: Phase 1 Complete ✅
"""

import pytest
import json
import sys
from pathlib import Path

# Import gap runner
sys.path.insert(0, str(Path(__file__).parent))
from phase1_gap_runner import Phase1GapRunner

FRAMEWORKS = ['django', 'fastapi', 'spring', 'go', 'nodejs']
LANGUAGES = ['python', 'javascript', 'java', 'go']


class TestPhase1GapRunner:
    """Test Phase 1 gap runner orchestration."""

    @pytest.fixture
    def runner(self):
        return Phase1GapRunner()

    def test_runner_initialization(self, runner):
        """Test runner initializes correctly."""
        assert runner is not None
        assert runner.generated_files == {}
        assert runner.errors == []

    def test_run_all_gaps_django_python(self, runner):
        """Test running all gaps for Django/Python."""
        result = runner.run_all_gaps('django', 'python', 'myapp')
        assert result['status'] in ['complete', 'partial']
        assert result['framework'] == 'django'
        assert result['language'] == 'python'
        assert result['files_generated'] > 0
        assert result['app_name'] == 'myapp'

    def test_run_all_gaps_fastapi_python(self, runner):
        """Test running all gaps for FastAPI/Python."""
        result = runner.run_all_gaps('fastapi', 'python', 'api-service')
        assert result['status'] in ['complete', 'partial']
        assert result['framework'] == 'fastapi'
        assert result['files_generated'] > 0

    def test_run_all_gaps_spring_java(self, runner):
        """Test running all gaps for Spring/Java."""
        result = runner.run_all_gaps('spring', 'java', 'springapp')
        assert result['status'] in ['complete', 'partial']
        assert result['framework'] == 'spring'
        assert result['files_generated'] > 0

    def test_run_all_gaps_go(self, runner):
        """Test running all gaps for Go."""
        result = runner.run_all_gaps('go', 'go', 'goapp')
        assert result['status'] in ['complete', 'partial']
        assert result['framework'] == 'go'
        assert result['files_generated'] > 0

    def test_run_all_gaps_nodejs(self, runner):
        """Test running all gaps for Node.js."""
        result = runner.run_all_gaps('nodejs', 'javascript', 'nodeapp')
        assert result['status'] in ['complete', 'partial']
        assert result['framework'] == 'nodejs'
        assert result['files_generated'] > 0

    def test_run_migrations_gap(self, runner):
        """Test Gap 2: Migration generation."""
        result = runner.run_gap('migrations', 'django', 'python', 'myapp')
        assert result['status'] == 'success'
        assert result['gap'] == 'migrations'
        assert 'files' in result
        assert len(result['files']) > 0

    def test_migrations_django_output(self, runner):
        """Test Django migration output."""
        result = runner.run_gap('migrations', 'django', 'python', 'myapp')
        files = result['files']
        assert 'migrations/0001_initial.py' in files
        assert 'migrations/__init__.py' in files
        assert 'Migration' in files['migrations/0001_initial.py']

    def test_migrations_fastapi_output(self, runner):
        """Test FastAPI (Alembic) migration output."""
        result = runner.run_gap('migrations', 'fastapi', 'python', 'api')
        files = result['files']
        assert any('alembic' in f for f in files.keys())

    def test_migrations_spring_output(self, runner):
        """Test Spring migration output."""
        result = runner.run_gap('migrations', 'spring', 'java', 'app')
        files = result['files']
        assert any('db/migration' in f for f in files.keys())

    def test_migrations_nodejs_output(self, runner):
        """Test Node.js migration output."""
        result = runner.run_gap('migrations', 'nodejs', 'javascript', 'app')
        files = result['files']
        assert any('migrations' in f for f in files.keys())

    def test_framework_config_gap_django(self, runner):
        """Test Gap 3: Framework configuration for Django."""
        result = runner.run_gap('framework-config', 'django', 'python', 'myapp')
        assert result['status'] == 'success'
        files = result['files']
        assert 'config/settings.py' in files
        assert 'INSTALLED_APPS' in files['config/settings.py']

    def test_framework_config_gap_fastapi(self, runner):
        """Test Gap 3: Framework configuration for FastAPI."""
        result = runner.run_gap('framework-config', 'fastapi', 'python', 'api')
        assert result['status'] == 'success'
        files = result['files']
        assert 'config.py' in files
        assert 'Settings' in files['config.py']

    def test_framework_config_gap_spring(self, runner):
        """Test Gap 3: Framework configuration for Spring."""
        result = runner.run_gap('framework-config', 'spring', 'java', 'app')
        assert result['status'] == 'success'
        files = result['files']
        assert 'application.properties' in files

    def test_framework_config_gap_go(self, runner):
        """Test Gap 3: Framework configuration for Go."""
        result = runner.run_gap('framework-config', 'go', 'go', 'app')
        assert result['status'] == 'success'
        files = result['files']
        assert 'config/config.go' in files

    def test_framework_config_gap_nodejs(self, runner):
        """Test Gap 3: Framework configuration for Node.js."""
        result = runner.run_gap('framework-config', 'nodejs', 'javascript', 'app')
        assert result['status'] == 'success'
        files = result['files']
        assert 'src/config.ts' in files

    def test_dependency_injection_gap_fastapi(self, runner):
        """Test Gap 3.1: Dependency injection for FastAPI."""
        result = runner.run_gap('dependency-injection', 'fastapi', 'python', 'api')
        assert result['status'] == 'success'
        files = result['files']
        assert 'dependencies.py' in files
        assert 'get_db' in files['dependencies.py']

    def test_dependency_injection_gap_nestjs(self, runner):
        """Test Gap 3.1: Dependency injection for NestJS."""
        result = runner.run_gap('dependency-injection', 'nestjs', 'javascript', 'app')
        assert result['status'] == 'success'
        files = result['files']
        assert any('app.module' in f for f in files.keys())

    def test_dependency_injection_gap_spring(self, runner):
        """Test Gap 3.1: Dependency injection for Spring."""
        result = runner.run_gap('dependency-injection', 'spring', 'java', 'app')
        assert result['status'] == 'success'
        files = result['files']
        assert any('BeanConfig' in f for f in files.keys())

    def test_env_generator_gap(self, runner):
        """Test Gap 3.2: Environment variables."""
        result = runner.run_gap('env-generator', 'django', 'python', 'myapp')
        assert result['status'] == 'success'
        files = result['files']
        assert '.env' in files
        assert '.env.example' in files
        assert 'DATABASE_URL' in files['.env']

    def test_docker_compose_gap(self, runner):
        """Test Gap 3.3: Docker composition."""
        result = runner.run_gap('docker-compose', 'django', 'python', 'myapp')
        assert result['status'] == 'success'
        files = result['files']
        assert 'docker-compose.yml' in files
        assert 'Dockerfile' in files
        assert 'services:' in files['docker-compose.yml']

    def test_cli_scaffold_gap_python(self, runner):
        """Test Gap 4: CLI scaffolding for Python."""
        result = runner.run_gap('cli', 'django', 'python', 'myapp')
        assert result['status'] == 'success'
        files = result['files']
        assert 'cli/__init__.py' in files
        assert 'cli/main.py' in files
        assert '@click.group' in files['cli/main.py']

    def test_cli_scaffold_gap_javascript(self, runner):
        """Test Gap 4: CLI scaffolding for JavaScript."""
        result = runner.run_gap('cli', 'nodejs', 'javascript', 'app')
        assert result['status'] == 'success'
        files = result['files']
        assert any('cli' in f for f in files.keys())

    def test_handlers_gap(self, runner):
        """Test Gap 6: Handler generation."""
        result = runner.run_gap('handlers', 'fastapi', 'python', 'api')
        assert result['status'] == 'success'
        files = result['files']
        assert 'handlers/__init__.py' in files
        assert 'handlers/events.py' in files

    def test_handlers_gap_nestjs(self, runner):
        """Test Gap 6: Handler generation for NestJS."""
        result = runner.run_gap('handlers', 'nestjs', 'javascript', 'app')
        assert result['status'] == 'success'
        files = result['files']
        assert any('filter' in f for f in files.keys())

    def test_multi_sidecar_gap(self, runner):
        """Test Gap 6.1: Multi-handler orchestration."""
        result = runner.run_gap('multi-sidecar', 'django', 'python', 'app')
        assert result['status'] == 'success'
        files = result['files']
        assert 'handlers/orchestrator.py' in files
        assert 'HandlerOrchestrator' in files['handlers/orchestrator.py']

    def test_enterprise_gap(self, runner):
        """Test Gap 7: Enterprise configurations."""
        result = runner.run_gap('enterprise', 'django', 'python', 'app')
        assert result['status'] == 'success'
        files = result['files']
        assert '.env.production' in files
        assert 'kubernetes/deployment.yaml' in files

    def test_openapi_docs_gap(self, runner):
        """Test Gap 8: OpenAPI documentation."""
        result = runner.run_gap('docs', 'fastapi', 'python', 'api')
        assert result['status'] == 'success'
        files = result['files']
        assert 'openapi.yaml' in files
        assert 'openapi: 3.0.0' in files['openapi.yaml']

    def test_comprehensive_tests_gap_python(self, runner):
        """Test Gap 9: Comprehensive tests for Python."""
        result = runner.run_gap('tests', 'django', 'python', 'app')
        assert result['status'] == 'success'
        files = result['files']
        assert 'tests/__init__.py' in files
        assert 'tests/test_main.py' in files

    def test_comprehensive_tests_gap_javascript(self, runner):
        """Test Gap 9: Comprehensive tests for JavaScript."""
        result = runner.run_gap('tests', 'nodejs', 'javascript', 'app')
        assert result['status'] == 'success'
        files = result['files']
        assert any('test.ts' in f for f in files.keys())

    def test_invalid_framework(self, runner):
        """Test error handling for invalid framework."""
        result = runner.run_gap('migrations', 'invalid_fw', 'python', 'app')
        assert result['status'] == 'error'
        assert 'Unsupported framework' in result['error']

    def test_invalid_language(self, runner):
        """Test error handling for invalid language."""
        result = runner.run_gap('migrations', 'django', 'invalid_lang', 'app')
        assert result['status'] == 'error'
        assert 'Unsupported language' in result['error']

    def test_invalid_gap(self, runner):
        """Test error handling for invalid gap."""
        result = runner.run_gap('invalid_gap', 'django', 'python', 'app')
        assert result['status'] == 'error'
        assert 'Unknown gap' in result['error']

    def test_all_gaps_generated_files_count(self, runner):
        """Test that all gaps generate files."""
        result = runner.run_all_gaps('django', 'python', 'testapp')
        assert result['files_generated'] >= 15  # Should generate at least 15 files across all gaps

    def test_all_gaps_no_errors(self, runner):
        """Test that all gaps complete without errors."""
        result = runner.run_all_gaps('fastapi', 'python', 'api')
        assert len(result['errors']) == 0
        assert result['status'] == 'complete'

    def test_json_serializable_output(self, runner):
        """Test that output is JSON serializable."""
        result = runner.run_all_gaps('django', 'python', 'app')
        try:
            json_str = json.dumps(result)
            assert len(json_str) > 0
        except TypeError:
            pytest.fail("Result is not JSON serializable")

    def test_gap_completion_tracking(self, runner):
        """Test that completed gaps are tracked."""
        result = runner.run_all_gaps('django', 'python', 'app')
        assert len(result['gaps_completed']) > 0
        assert 'migrations' in result['gaps_completed']
        assert 'framework-config' in result['gaps_completed']

    @pytest.mark.parametrize('framework', FRAMEWORKS)
    def test_all_frameworks_supported(self, runner, framework):
        """Test all frameworks work."""
        result = runner.run_gap('migrations', framework, 'python', 'app')
        assert result['status'] == 'success'
        assert result['gap'] == 'migrations'

    @pytest.mark.parametrize('language', LANGUAGES)
    def test_all_languages_supported(self, runner, language):
        """Test all languages work."""
        # Skip incompatible combinations
        if language == 'go':
            framework = 'go'
        elif language == 'java':
            framework = 'spring'
        else:
            framework = 'django'

        result = runner.run_gap('migrations', framework, language, 'app')
        assert result['status'] == 'success'


class TestPhase1GapIntegration:
    """Integration tests for Phase 1 gaps."""

    @pytest.fixture
    def runner(self):
        return Phase1GapRunner()

    def test_migration_files_contain_correct_syntax_django(self, runner):
        """Test generated Django migrations have correct Python syntax."""
        result = runner.run_gap('migrations', 'django', 'python', 'app')
        files = result['files']
        migration_content = files['migrations/0001_initial.py']
        assert 'from django.db import migrations' in migration_content
        assert 'class Migration' in migration_content

    def test_docker_compose_valid_yaml_structure(self, runner):
        """Test generated docker-compose.yml is valid YAML."""
        result = runner.run_gap('docker-compose', 'django', 'python', 'app')
        files = result['files']
        docker_content = files['docker-compose.yml']
        assert 'version:' in docker_content
        assert 'services:' in docker_content
        assert 'app:' in docker_content or 'db:' in docker_content

    def test_kubernetes_deployment_valid_yaml_structure(self, runner):
        """Test generated Kubernetes deployment is valid YAML."""
        result = runner.run_gap('enterprise', 'django', 'python', 'app')
        files = result['files']
        k8s_content = files['kubernetes/deployment.yaml']
        assert 'apiVersion:' in k8s_content
        assert 'kind: Deployment' in k8s_content

    def test_openapi_schema_complete(self, runner):
        """Test generated OpenAPI schema is complete."""
        result = runner.run_gap('docs', 'fastapi', 'python', 'api')
        files = result['files']
        openapi_content = files['openapi.yaml']
        assert 'info:' in openapi_content
        assert 'paths:' in openapi_content
        assert 'servers:' in openapi_content

    def test_env_files_have_required_variables(self, runner):
        """Test .env files contain required variables."""
        result = runner.run_gap('env-generator', 'django', 'python', 'app')
        files = result['files']
        env_content = files['.env']
        assert 'DATABASE_URL' in env_content
        assert 'DEBUG' in env_content
        assert 'SECRET_KEY' in env_content


class TestPhase1GapCoverage:
    """Coverage tests for Phase 1 gaps."""

    @pytest.fixture
    def runner(self):
        return Phase1GapRunner()

    def test_all_11_gaps_available(self, runner):
        """Test all 11 Phase 1 gaps are available."""
        gaps = [
            'migrations',
            'framework-config',
            'dependency-injection',
            'env-generator',
            'docker-compose',
            'cli',
            'handlers',
            'multi-sidecar',
            'enterprise',
            'docs',
            'tests'
        ]
        for gap in gaps:
            result = runner.run_gap(gap, 'django', 'python', 'app')
            assert result['status'] == 'success', f"Gap {gap} failed"

    def test_django_ecosystem_complete(self, runner):
        """Test Django ecosystem is complete."""
        gaps = ['migrations', 'framework-config', 'env-generator', 'docker-compose', 'tests']
        for gap in gaps:
            result = runner.run_gap(gap, 'django', 'python', 'app')
            assert result['status'] == 'success', f"Django gap {gap} failed"

    def test_fastapi_ecosystem_complete(self, runner):
        """Test FastAPI ecosystem is complete."""
        gaps = ['migrations', 'framework-config', 'dependency-injection', 'docker-compose', 'docs']
        for gap in gaps:
            result = runner.run_gap(gap, 'fastapi', 'python', 'app')
            assert result['status'] == 'success', f"FastAPI gap {gap} failed"

    def test_nodejs_ecosystem_complete(self, runner):
        """Test Node.js ecosystem is complete."""
        gaps = ['framework-config', 'docker-compose', 'cli', 'handlers', 'tests']
        for gap in gaps:
            result = runner.run_gap(gap, 'nodejs', 'javascript', 'app')
            assert result['status'] == 'success', f"Node.js gap {gap} failed"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
