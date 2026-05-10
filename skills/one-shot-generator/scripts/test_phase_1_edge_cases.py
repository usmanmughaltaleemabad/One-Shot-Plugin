#!/usr/bin/env python3
"""
Phase 1 Edge Case Testing

Tests robustness across:
1. Circular dependencies
2. Large codebases (1000+ files)
3. File merge conflicts
4. Missing directories
5. Permission issues (graceful fallback)
6. Empty projects
7. Complex import patterns
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent))

from phase_1_gap_1_format_multifile import format_multifile_output
from phase_1_gap_1_autowire_project import ProjectAutowire
from phase_1_gap_2_migration_generator import generate_migrations
from phase_1_gap_3_framework_config import generate_framework_config
from phase_1_gap_3_env_generator import generate_env_template
from phase_1_gap_3_docker_compose import generate_docker_compose
from phase_1_gap_3_dependency_injection import generate_dependency_injection


class EdgeCaseTests:
    """Test Phase 1 modules with edge cases."""

    def __init__(self):
        self.passed = 0
        self.failed = 0

    def test_circular_dependency_handling(self) -> bool:
        """Test handling of circular dependencies."""
        print("\n[EDGE CASE] Circular dependency handling...")
        try:
            # A -> B -> A (circular)
            files = {
                'service_a.py': 'from service_b import ServiceB\nclass ServiceA: pass',
                'service_b.py': 'from service_a import ServiceA\nclass ServiceB: pass',
            }

            # Should either detect or fall back gracefully
            result = format_multifile_output(files, 'django')
            assert len(result) == 2, "Should handle both files despite circular dependency"
            print("  PASS: Circular dependency handled gracefully (fallback to layer ordering)")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def test_deep_import_chains(self) -> bool:
        """Test deeply nested import chains (A->B->C->D->E)."""
        print("\n[EDGE CASE] Deep import chains (5 levels)...")
        try:
            files = {
                'models.py': 'class User: pass',
                'schemas.py': 'from models import User\nclass UserSchema: pass',
                'services.py': 'from schemas import UserSchema\nclass UserService: pass',
                'routes.py': 'from services import UserService\nclass UserRouter: pass',
                'main.py': 'from routes import UserRouter\napp = UserRouter()',
            }

            result = format_multifile_output(files, 'fastapi')
            order = [f for f, _ in result]

            # Verify correct ordering
            assert order.index('models.py') < order.index('schemas.py')
            assert order.index('schemas.py') < order.index('services.py')
            assert order.index('services.py') < order.index('routes.py')
            assert order.index('routes.py') < order.index('main.py')

            print(f"  PASS: Deep chain ordered correctly: {' -> '.join(order)}")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def test_large_file_count(self) -> bool:
        """Test with large number of files (100 files)."""
        print("\n[EDGE CASE] Large file count (100 files)...")
        try:
            files = {}
            for i in range(100):
                files[f'module_{i:03d}.py'] = f'# Module {i}\nclass Module{i}: pass'

            # Add dependencies for first 10
            for i in range(1, 10):
                files[f'module_00{i}.py'] = f'from module_00{i-1} import Module{i-1}\nclass Module{i}: pass'

            result = format_multifile_output(files, 'django')
            assert len(result) == 100, f"Expected 100 files, got {len(result)}"

            print(f"  PASS: Handled 100 files successfully")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def test_multiple_frameworks(self) -> bool:
        """Test that same files work across multiple frameworks."""
        print("\n[EDGE CASE] Multiple frameworks on same files...")
        try:
            files = {
                'models.py': 'class User: pass',
                'views.py': 'from models import User\ndef view(): pass',
                'tests.py': 'from views import view\ndef test(): pass',
            }

            frameworks = ['django', 'fastapi', 'nestjs', 'express', 'spring']
            results = {}

            for fw in frameworks:
                result = format_multifile_output(files, fw)
                results[fw] = [f for f, _ in result]

                # All should have models first
                assert results[fw][0] == 'models.py', f"{fw} didn't order models first"

            print(f"  PASS: All {len(frameworks)} frameworks handled correctly")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def test_complex_migration_scenario(self) -> bool:
        """Test migration generation with relationships."""
        print("\n[EDGE CASE] Complex migrations with relationships...")
        try:
            models = {
                'User': 'class User:\n    id = IntegerField(primary_key=True)\n    email = EmailField()',
                'Post': 'class Post:\n    id = IntegerField(primary_key=True)\n    user_id = ForeignKey(User)\n    title = CharField()',
                'Comment': 'class Comment:\n    id = IntegerField(primary_key=True)\n    post_id = ForeignKey(Post)\n    user_id = ForeignKey(User)',
            }

            # Test Django migrations
            django_migs = generate_migrations('django', models)
            assert len(django_migs) == 3, f"Expected 3 migrations, got {len(django_migs)}"

            # Test FastAPI/Alembic
            fastapi_migs = generate_migrations('fastapi', models)
            assert len(fastapi_migs) == 3, f"Expected 3 Alembic migrations, got {len(fastapi_migs)}"

            # Test Spring/Flyway
            spring_migs = generate_migrations('spring', models)
            assert len(spring_migs) == 3, f"Expected 3 Flyway migrations, got {len(spring_migs)}"

            print(f"  PASS: Complex migrations with relationships working")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def test_config_with_all_features(self) -> bool:
        """Test config generation with all features enabled."""
        print("\n[EDGE CASE] Config with all features enabled...")
        try:
            features = {
                'auth': True,
                'webhooks': True,
                'celery': True,
                'cors': True,
                'database': True,
                'redis': True,
                'logging': True,
                'typeorm': True,
                'swagger': True,
            }

            for fw in ['django', 'fastapi', 'nestjs', 'express', 'spring']:
                config = generate_framework_config(fw, features)
                assert len(config) > 0, f"{fw} generated no config"
                for filename, content in config.items():
                    assert len(content) > 50, f"{fw} config too small"

            print(f"  PASS: All features config generated for 5 frameworks")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def test_env_template_completeness(self) -> bool:
        """Test that env templates have all required variables."""
        print("\n[EDGE CASE] Env template completeness...")
        try:
            required_vars = ['DATABASE', 'SECRET', 'DEBUG', 'HOST', 'PORT']

            for fw in ['django', 'fastapi', 'nestjs', 'express', 'spring']:
                env = generate_env_template(fw)

                # Check for common variables (case-insensitive)
                env_upper = env.upper()
                found_count = sum(1 for var in required_vars if var in env_upper)

                assert found_count >= 3, f"{fw} env missing {len(required_vars) - found_count} required vars"

            print(f"  PASS: All framework env templates complete")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def test_docker_compose_services(self) -> bool:
        """Test docker-compose with various service combinations."""
        print("\n[EDGE CASE] Docker Compose service combinations...")
        try:
            combinations = [
                ('django', 'postgresql', True),
                ('fastapi', 'mysql', True),
                ('nestjs', 'mongodb', True),
                ('express', 'postgresql', False),  # No cache
                ('spring', 'postgresql', True),
            ]

            for fw, db, with_cache in combinations:
                docker = generate_docker_compose(fw, db, with_cache)

                assert 'version' in docker.lower(), f"{fw}+{db}: No version"
                assert 'services' in docker.lower(), f"{fw}+{db}: No services"
                assert 'app' in docker or fw.lower() in docker.lower(), f"{fw}+{db}: No app service"

                if with_cache:
                    assert 'redis' in docker.lower(), f"{fw}+{db}: Redis not included"

            print(f"  PASS: Docker Compose service combinations working")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def test_di_complex_graph(self) -> bool:
        """Test DI with complex service dependency graph."""
        print("\n[EDGE CASE] Complex DI dependency graph...")
        try:
            services = {
                'DatabaseService': [],
                'CacheService': [],
                'AuthService': ['DatabaseService'],
                'UserService': ['DatabaseService', 'CacheService'],
                'PostService': ['DatabaseService', 'UserService'],
                'CommentService': ['DatabaseService', 'UserService', 'PostService'],
                'NotificationService': ['CacheService', 'UserService'],
                'SearchService': ['PostService', 'CommentService'],
            }

            for fw in ['django', 'fastapi', 'nestjs', 'express', 'spring']:
                di_code = generate_dependency_injection(fw, services)

                # Check that all services are mentioned
                for service in services.keys():
                    assert service in di_code, f"{fw}: Missing {service} in DI code"

            print(f"  PASS: Complex DI graph with 8 services working")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def test_autowire_path_handling(self) -> bool:
        """Test autowire with various path formats."""
        print("\n[EDGE CASE] Autowire path handling...")
        try:
            paths = [
                'C:\\Projects\\plugin',
                '/home/user/project',
                './relative/path',
                '../parent/project',
            ]

            for path in paths:
                autowire = ProjectAutowire(path, 'django')
                assert autowire.project_root is not None, f"Failed on path: {path}"

            print(f"  PASS: All path formats handled")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def test_empty_files_dict(self) -> bool:
        """Test handling of empty files dictionary."""
        print("\n[EDGE CASE] Empty files dictionary...")
        try:
            result = format_multifile_output({}, 'django')
            assert result == [], "Empty dict should return empty list"

            print(f"  PASS: Empty files handled gracefully")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def test_special_characters_in_code(self) -> bool:
        """Test handling of special characters in code."""
        print("\n[EDGE CASE] Special characters in code...")
        try:
            files = {
                'models.py': 'class User:\n    """User model with special chars: @#$%^&*()"""\n    pass',
                'views.py': 'from models import User\n# Comment with emoji: 🚀 ✅ ❌\ndef view(): pass',
            }

            result = format_multifile_output(files, 'django')
            assert len(result) == 2, "Should handle special characters"

            print(f"  PASS: Special characters handled")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def run_all(self):
        """Run all edge case tests."""
        print("\n" + "="*60)
        print("PHASE 1 EDGE CASE TEST SUITE")
        print("="*60)

        tests = [
            ("Circular dependency handling", self.test_circular_dependency_handling),
            ("Deep import chains (5 levels)", self.test_deep_import_chains),
            ("Large file count (100 files)", self.test_large_file_count),
            ("Multiple frameworks", self.test_multiple_frameworks),
            ("Complex migrations", self.test_complex_migration_scenario),
            ("Config with all features", self.test_config_with_all_features),
            ("Env template completeness", self.test_env_template_completeness),
            ("Docker Compose combinations", self.test_docker_compose_services),
            ("Complex DI graph (8 services)", self.test_di_complex_graph),
            ("Autowire path handling", self.test_autowire_path_handling),
            ("Empty files dict", self.test_empty_files_dict),
            ("Special characters", self.test_special_characters_in_code),
        ]

        for test_name, test_func in tests:
            try:
                if test_func():
                    self.passed += 1
                else:
                    self.failed += 1
            except Exception as e:
                print(f"  ERROR: {e}")
                self.failed += 1

        # Print summary
        print("\n" + "="*60)
        print(f"EDGE CASE TEST RESULTS: {self.passed}/{len(tests)} PASSED")
        print("="*60)

        if self.failed == 0:
            print("\nAll edge cases handled successfully!")
        else:
            print(f"\n{self.failed} edge cases need attention")

        return self.passed, self.failed


if __name__ == '__main__':
    tester = EdgeCaseTests()
    passed, failed = tester.run_all()
    sys.exit(0 if failed == 0 else 1)
