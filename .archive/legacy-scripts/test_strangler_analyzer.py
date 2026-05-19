#!/usr/bin/env python3
"""
Unit tests for strangler_analyzer.py

Tests feature extraction, coupling analysis, and difficulty scoring.
"""

import json
import subprocess
import sys
from pathlib import Path
import tempfile


def test_strangler_analyze_on_current_project():
    """Test strangler_analyzer on current project."""
    # Run analyzer on scripts directory
    result = subprocess.run(
        [sys.executable, './strangler_analyzer.py', f'analyze @{Path.cwd()}'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )

    assert result.returncode == 0, f"Analyzer failed: {result.stderr}"

    # Parse JSON output (last block in output)
    lines = result.stdout.split('\n')
    json_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('{'):
            json_start = i
            break

    assert json_start is not None, "No JSON output found"
    json_str = '\n'.join(lines[json_start:])
    data = json.loads(json_str)

    # Assertions
    assert 'framework' in data
    assert 'feature_count' in data
    assert 'features' in data

    print("[PASS] test_strangler_analyze_on_current_project")


def test_strangler_analyze_synthetic_django():
    """Test analyzer on a synthetic Django project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create minimal Django structure
        project_path = Path(tmpdir)

        # Create auth module
        auth_dir = project_path / 'auth'
        auth_dir.mkdir()
        (auth_dir / '__init__.py').write_text('')
        (auth_dir / 'views.py').write_text('''
def login(request):
    pass

def logout(request):
    pass

class User:
    pass
''')

        # Create payment module
        payment_dir = project_path / 'payment'
        payment_dir.mkdir()
        (payment_dir / '__init__.py').write_text('')
        (payment_dir / 'views.py').write_text('''
def charge(request):
    pass

def refund(request):
    pass

class Payment:
    pass

class Invoice:
    pass
''')

        # Run analyzer
        result = subprocess.run(
            [sys.executable, './strangler_analyzer.py', f'analyze @{tmpdir}'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        assert result.returncode == 0, f"Analyzer failed: {result.stderr}"

        # Parse output
        lines = result.stdout.split('\n')
        json_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_start = i
                break

        json_str = '\n'.join(lines[json_start:])
        data = json.loads(json_str)

        # Should detect features
        feature_names = {f['name'] for f in data['features']}
        assert len(feature_names) > 0, f"No features found: {feature_names}"

        # Features should have entities
        for feature in data['features']:
            assert len(feature['modules']) > 0
            assert feature['entity_count'] > 0

        print("[PASS] test_strangler_analyze_synthetic_django")


def test_strangler_analyze_missing_path():
    """Test analyzer with missing path."""
    result = subprocess.run(
        [sys.executable, './strangler_analyzer.py', 'analyze @/nonexistent/path/xyz123'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )

    assert result.returncode == 1, "Should fail on missing path"
    assert "[ERROR]" in result.stdout or "[ERROR]" in result.stderr

    print("[PASS] test_strangler_analyze_missing_path")


def test_extraction_difficulty_scoring():
    """Test that difficulty scoring works correctly."""
    result = subprocess.run(
        [sys.executable, './strangler_analyzer.py', f'analyze @{Path.cwd()}'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )

    assert result.returncode == 0

    # Parse output
    lines = result.stdout.split('\n')
    json_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('{'):
            json_start = i
            break

    json_str = '\n'.join(lines[json_start:])
    data = json.loads(json_str)

    # All features should have valid difficulty
    for feature in data['features']:
        difficulty = feature['difficulty']
        assert difficulty in ['GREEN', 'YELLOW', 'RED'], f"Invalid difficulty: {difficulty}"

        # Verify difficulty correlates with score and coupling
        score = feature['score']
        coupling = feature['external_coupling']

        if difficulty == 'GREEN':
            assert score >= 7, f"GREEN should have high score, got {score}"
            assert coupling <= 3, f"GREEN should have low coupling, got {coupling}"
        elif difficulty == 'YELLOW':
            assert 3 <= score <= 9, f"YELLOW should have medium score, got {score}"
            assert coupling <= 6, f"YELLOW should have medium coupling, got {coupling}"
        # RED is catch-all

    print("[PASS] test_extraction_difficulty_scoring")


def run_all_tests():
    """Run all tests."""
    tests = [
        test_strangler_analyze_on_current_project,
        test_strangler_analyze_synthetic_django,
        test_strangler_analyze_missing_path,
        test_extraction_difficulty_scoring,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print("[FAIL] {}: {}".format(test.__name__, str(e)))
            failed += 1

    print("\n" + "=" * 60)
    print("Test Results: {} passed, {} failed".format(passed, failed))
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
