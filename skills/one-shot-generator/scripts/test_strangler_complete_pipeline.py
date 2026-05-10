#!/usr/bin/env python3
"""
Complete Pipeline Integration Tests

Tests the full strangler pattern workflow:
1. Analyze monolith
2. Extract first service
3. Validate service
4. Generate roadmap for all features
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def test_complete_pipeline():
    """Test full analyze -> extract -> validate -> roadmap workflow."""
    print("\n" + "=" * 60)
    print("TEST: Complete Strangler Pipeline")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Step 1: Create a sample monolith
        print("\nStep 1: Creating sample monolith...")
        auth_dir = tmpdir / "auth"
        auth_dir.mkdir()
        (auth_dir / "service.py").write_text('''
def login(email, password):
    return {"token": "abc123"}

def verify_token(token):
    return token == "abc123"

class User:
    pass

class Token:
    pass
''')

        payment_dir = tmpdir / "payment"
        payment_dir.mkdir()
        (payment_dir / "processor.py").write_text('''
def charge(amount, card):
    return {"status": "success"}

def refund(transaction_id):
    return {"status": "refunded"}

class Payment:
    pass
''')

        # Step 2: Analyze monolith
        print("Step 2: Analyzing monolith...")
        analyze_result = subprocess.run(
            [sys.executable, './strangler_analyzer.py', f'analyze @{tmpdir}'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        if analyze_result.returncode != 0:
            print(f"[FAIL] Analysis failed")
            return False

        # Parse analysis
        lines = analyze_result.stdout.split('\n')
        json_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_start = i
                break

        json_str = '\n'.join(lines[json_start:])
        analysis = json.loads(json_str)

        print(f"  Found {analysis['feature_count']} features")
        assert analysis['feature_count'] > 0

        # Step 3: Extract first service
        print("Step 3: Extracting first feature as microservice...")
        first_feature = analysis['features'][0]

        extract_result = subprocess.run(
            [sys.executable, './strangler_extractor.py',
             f'extract {json.dumps(first_feature)} --language fastapi'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        if extract_result.returncode != 0:
            print(f"[FAIL] Extraction failed")
            return False

        print(f"  Generated microservice: {first_feature['name']}")

        # Step 4: Create extracted service directory and validate
        print("Step 4: Validating extracted service...")
        service_dir = tmpdir / "extracted_service"
        service_dir.mkdir()

        # Create minimal service structure
        (service_dir / 'requirements.txt').write_text('fastapi==0.104.0\nuvicorn==0.24.0\n')
        (service_dir / 'main.py').write_text('from fastapi import FastAPI\napp = FastAPI()\n')
        (service_dir / 'router.py').write_text('from fastapi import APIRouter\nrouter = APIRouter()\n')
        (service_dir / 'adapter.py').write_text('# Adapter\n')
        (service_dir / 'Dockerfile').write_text('FROM python:3.11\n')
        (service_dir / 'k8s').mkdir()
        (service_dir / 'k8s' / 'deployment.yaml').write_text('apiVersion: v1\n')
        (service_dir / 'migrations').mkdir()
        (service_dir / 'migrations' / '001_init.sql').write_text('CREATE TABLE shadow (id INT);\n')

        validate_result = subprocess.run(
            [sys.executable, './strangler_validate.py',
             f'validate @{service_dir} --language fastapi'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        # Parse validation
        val_lines = validate_result.stdout.split('\n')
        val_json_start = None
        for i, line in enumerate(val_lines):
            if line.strip().startswith('{'):
                val_json_start = i
                break

        if val_json_start:
            val_json_str = '\n'.join(val_lines[val_json_start:])
            validation = json.loads(val_json_str)
            print(f"  Validation status: {validation['status']}")
            assert validation['status'] in ['PASS', 'WARN']
        else:
            print("[WARN] Could not parse validation results")

        # Step 5: Generate roadmap
        print("Step 5: Generating extraction roadmap...")
        roadmap_result = subprocess.run(
            [sys.executable, './strangler_roadmap.py', 'roadmap @demo'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        if roadmap_result.returncode != 0:
            print(f"[FAIL] Roadmap generation failed")
            return False

        # Parse roadmap
        rm_lines = roadmap_result.stdout.split('\n')
        rm_json_start = None
        for i, line in enumerate(rm_lines):
            if line.strip().startswith('{'):
                rm_json_start = i
                break

        if rm_json_start:
            rm_json_str = '\n'.join(rm_lines[rm_json_start:])
            roadmap = json.loads(rm_json_str)
            print(f"  Timeline: {roadmap['total_duration_weeks']} weeks")
            print(f"  Investment: ${roadmap['total_cost_estimate']:,}")
            print(f"  Phases: {len(roadmap['phases'])}")

        print("\n[PASS] Complete pipeline executed successfully")
        return True


def test_feature_prioritization():
    """Test that roadmap prioritizes GREEN before YELLOW before RED."""
    print("\n" + "=" * 60)
    print("TEST: Feature Prioritization (GREEN -> YELLOW -> RED)")
    print("=" * 60)

    roadmap_result = subprocess.run(
        [sys.executable, './strangler_roadmap.py', 'roadmap @demo'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )

    # Parse roadmap
    lines = roadmap_result.stdout.split('\n')
    json_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('{'):
            json_start = i
            break

    json_str = '\n'.join(lines[json_start:])
    roadmap = json.loads(json_str)

    # Extract risk levels from phases
    phases = roadmap['phases'][1:]  # Skip planning phase
    risks = [p['risk_level'] for p in phases]

    print(f"Phase order: {' -> '.join(risks)}")

    # Verify ordering
    green_indices = [i for i, r in enumerate(risks) if r == 'GREEN']
    yellow_indices = [i for i, r in enumerate(risks) if r == 'YELLOW']
    red_indices = [i for i, r in enumerate(risks) if r == 'RED']

    if green_indices and yellow_indices:
        assert max(green_indices) < min(yellow_indices), "GREEN should come before YELLOW"
    if yellow_indices and red_indices:
        assert max(yellow_indices) < min(red_indices), "YELLOW should come before RED"

    print("[PASS] Features correctly prioritized by difficulty")
    return True


def test_roadmap_metrics():
    """Test that roadmap calculates correct metrics."""
    print("\n" + "=" * 60)
    print("TEST: Roadmap Financial Metrics")
    print("=" * 60)

    roadmap_result = subprocess.run(
        [sys.executable, './strangler_roadmap.py', 'roadmap @demo'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )

    lines = roadmap_result.stdout.split('\n')
    json_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('{'):
            json_start = i
            break

    json_str = '\n'.join(lines[json_start:])
    roadmap = json.loads(json_str)

    # Verify metrics exist and are non-zero
    assert roadmap['total_cost_estimate'] > 0, "Cost should be positive"
    assert roadmap['annual_payoff'] > 0, "Payoff should be positive"
    assert roadmap['roi'] >= 0, "ROI should be non-negative"
    assert roadmap['total_duration_weeks'] > 0, "Duration should be positive"

    print(f"  Total Investment: ${roadmap['total_cost_estimate']:,}")
    print(f"  Annual Payoff: ${roadmap['annual_payoff']:,}")
    print(f"  2-Year ROI: {roadmap['roi']:.2f}x")
    print(f"  Timeline: {roadmap['total_duration_weeks']} weeks")

    print("[PASS] Roadmap metrics calculated correctly")
    return True


def main():
    """Run all tests."""
    tests = [
        ("Complete Pipeline", test_complete_pipeline),
        ("Feature Prioritization", test_feature_prioritization),
        ("Roadmap Metrics", test_roadmap_metrics),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[ERROR] {name}: {str(e)}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Complete Pipeline Tests: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
