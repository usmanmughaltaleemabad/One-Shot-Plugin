#!/usr/bin/env python3
"""Quick sanity test for Phase 1 modules."""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("Testing Phase 1 modules...\n")

tests_passed = 0
tests_failed = 0

# Test 1: format_multifile
print("[1/7] Testing format_multifile_output...")
try:
    from phase_1_gap_1_format_multifile import format_multifile_output

    files = {
        'models.py': 'class User: pass',
        'views.py': 'from models import User\ndef view(): pass',
        'tests.py': 'from views import view\ndef test(): pass',
    }
    result = format_multifile_output(files, 'django')
    order = [f for f, _ in result]

    # models should come first
    if order[0] == 'models.py':
        print("  PASS: models.py ordered first")
        tests_passed += 1
    else:
        print(f"  FAIL: Expected models.py first, got {order}")
        tests_failed += 1
except Exception as e:
    print(f"  ERROR: {e}")
    tests_failed += 1

# Test 2: autowire_into_project
print("\n[2/7] Testing autowire_into_project...")
try:
    from phase_1_gap_1_autowire_project import ProjectAutowire

    # Test framework detection
    autowire = ProjectAutowire('C:\\Projects\\plugin', 'django')
    if autowire.framework == 'django':
        print("  PASS: Framework detection works")
        tests_passed += 1
    else:
        print(f"  FAIL: Expected django, got {autowire.framework}")
        tests_failed += 1
except Exception as e:
    print(f"  ERROR: {e}")
    tests_failed += 1

# Test 3: migration_generator
print("\n[3/7] Testing migration_generator...")
try:
    from phase_1_gap_2_migration_generator import MigrationGenerator

    gen = MigrationGenerator('django')
    if gen.framework == 'django':
        print("  PASS: Migration generator initialized")
        tests_passed += 1
    else:
        print(f"  FAIL: Expected django, got {gen.framework}")
        tests_failed += 1
except Exception as e:
    print(f"  ERROR: {e}")
    tests_failed += 1

# Test 4: framework_config
print("\n[4/7] Testing framework_config...")
try:
    from phase_1_gap_3_framework_config import FrameworkConfigGenerator

    gen = FrameworkConfigGenerator('fastapi')
    config = gen.generate({'auth': True, 'cors': True})
    if 'main.py' in config:
        print("  PASS: Framework config generator works")
        tests_passed += 1
    else:
        print(f"  FAIL: Expected main.py in config, got {list(config.keys())}")
        tests_failed += 1
except Exception as e:
    print(f"  ERROR: {e}")
    tests_failed += 1

# Test 5: env_generator
print("\n[5/7] Testing env_generator...")
try:
    from phase_1_gap_3_env_generator import generate_env_template

    env = generate_env_template('django')
    if len(env) > 100 and 'DATABASE' in env:
        print("  PASS: Env generator works")
        tests_passed += 1
    else:
        print(f"  FAIL: Env template too small or missing DATABASE")
        tests_failed += 1
except Exception as e:
    print(f"  ERROR: {e}")
    tests_failed += 1

# Test 6: docker_compose
print("\n[6/7] Testing docker_compose...")
try:
    from phase_1_gap_3_docker_compose import DockerComposeGenerator

    gen = DockerComposeGenerator('fastapi', 'postgresql')
    compose = gen.generate_compose()
    if 'services' in compose and 'app' in compose['services']:
        print("  PASS: Docker Compose generator works")
        tests_passed += 1
    else:
        print(f"  FAIL: Missing services/app in docker-compose")
        tests_failed += 1
except Exception as e:
    print(f"  ERROR: {e}")
    tests_failed += 1

# Test 7: dependency_injection
print("\n[7/7] Testing dependency_injection...")
try:
    from phase_1_gap_3_dependency_injection import DependencyInjectionGenerator

    gen = DependencyInjectionGenerator('nestjs')
    gen.add_service('UserService', ['DatabaseService'])
    gen.add_service('DatabaseService', [])
    code = gen.generate()
    if 'UserService' in code and 'DatabaseService' in code:
        print("  PASS: DI generator works")
        tests_passed += 1
    else:
        print(f"  FAIL: DI code missing services")
        tests_failed += 1
except Exception as e:
    print(f"  ERROR: {e}")
    tests_failed += 1

# Summary
print("\n" + "="*50)
print(f"RESULTS: {tests_passed} PASSED, {tests_failed} FAILED")
print("="*50)

sys.exit(0 if tests_failed == 0 else 1)
