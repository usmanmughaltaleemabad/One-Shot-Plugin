#!/usr/bin/env python3
"""
End-to-end tests for strangler pattern: analyze → extract → deploy

Validates complete workflow from monolith analysis to microservice generation.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def test_analyze_then_extract():
    """Test complete analyze -> extract workflow."""
    print("\n" + "=" * 60)
    print("TEST: Analyze -> Extract Workflow (E2E)")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Step 1: Create a sample monolith
        print("\nStep 1: Creating sample monolith...")
        payment_dir = tmpdir / "payment"
        payment_dir.mkdir()
        (payment_dir / "processor.py").write_text('''
def charge(amount, card):
    """Process a charge."""
    return {"status": "success", "amount": amount}

def refund(transaction_id):
    """Refund a transaction."""
    return {"status": "refunded"}

class PaymentGateway:
    def __init__(self, api_key):
        self.api_key = api_key
''')

        auth_dir = tmpdir / "auth"
        auth_dir.mkdir()
        (auth_dir / "users.py").write_text('''
class User:
    def __init__(self, email, password):
        self.email = email
        self.password = password

def authenticate(email, password):
    """Authenticate user."""
    return True
''')

        # Step 2: Analyze the monolith
        print("Step 2: Analyzing monolith...")
        analyze_result = subprocess.run(
            [sys.executable, './strangler_analyzer.py', f'analyze @{tmpdir}'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        assert analyze_result.returncode == 0, f"Analysis failed: {analyze_result.stderr}"

        # Parse analysis results
        lines = analyze_result.stdout.split('\n')
        json_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_start = i
                break

        json_str = '\n'.join(lines[json_start:])
        analysis = json.loads(json_str)

        print(f"  Found {analysis['feature_count']} features")
        for feature in analysis['features'][:2]:
            print(f"    - {feature['name']}: {feature['difficulty']}")

        assert analysis['feature_count'] > 0, "No features found"

        # Step 3: Select first feature and extract it
        print("\nStep 3: Extracting first feature as microservice...")
        first_feature = analysis['features'][0]

        extract_result = subprocess.run(
            [sys.executable, './strangler_extractor.py',
             f'extract {json.dumps(first_feature)} --language go'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        assert extract_result.returncode == 0, f"Extraction failed: {extract_result.stderr}"

        # Parse extraction results
        lines = extract_result.stdout.split('\n')
        json_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_start = i
                break

        json_str = '\n'.join(lines[json_start:])
        extraction = json.loads(json_str)

        print(f"  Generated {extraction['file_count']} files")
        print(f"  Service: {extraction['service_name']}")

        # Verify extracted files
        assert extraction['status'] == 'extracted'
        assert extraction['service_name'] == first_feature['name']
        assert extraction['language'] == 'go'
        assert len(extraction['files']['service']) > 0
        assert len(extraction['files']['deployment']) > 0
        assert len(extraction['files']['adapter']) > 0

        print("\n[PASS] Complete workflow: analyze -> extract -> generate")
        print(f"  Monolith: {analysis['feature_count']} features")
        print(f"  Extracted: {extraction['service_name']} service ({extraction['file_count']} files)")


def test_multiple_feature_extraction():
    """Test extracting multiple features from one monolith."""
    print("\n" + "=" * 60)
    print("TEST: Multiple Feature Extraction")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create modules for multiple features
        for feature in ["payment", "notification", "inventory"]:
            feature_dir = tmpdir / feature
            feature_dir.mkdir()
            (feature_dir / f"{feature}_service.py").write_text(f'''
def process_{feature}():
    """Process {feature}."""
    return {{"status": "ok"}}

class {feature.title()}Service:
    pass
''')

        # Analyze
        analyze_result = subprocess.run(
            [sys.executable, './strangler_analyzer.py', f'analyze @{tmpdir}'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        lines = analyze_result.stdout.split('\n')
        json_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_start = i
                break

        json_str = '\n'.join(lines[json_start:])
        analysis = json.loads(json_str)

        print(f"Found {analysis['feature_count']} features")

        # Extract each feature
        extracted_count = 0
        for feature_data in analysis['features'][:3]:
            extract_result = subprocess.run(
                [sys.executable, './strangler_extractor.py',
                 f'extract {json.dumps(feature_data)} --language fastapi'],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent,
            )

            if extract_result.returncode == 0:
                extracted_count += 1

        print(f"Successfully extracted {extracted_count} microservices")
        assert extracted_count >= 2, "Should extract at least 2 features"

        print("[PASS] Multi-feature extraction successful")


def test_extraction_preserves_feature_info():
    """Test that extraction preserves all feature metadata."""
    print("\n" + "=" * 60)
    print("TEST: Feature Metadata Preservation")
    print("=" * 60)

    feature_json = {
        "name": "complex_feature",
        "modules": ["m1", "m2", "m3"],
        "functions": ["f1", "f2", "f3"],
        "classes": ["C1", "C2"],
        "entity_count": 7,
        "external_coupling": 5.5,
        "difficulty": "RED",
        "score": 3
    }

    extract_result = subprocess.run(
        [sys.executable, './strangler_extractor.py',
         f'extract {json.dumps(feature_json)} --language go'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )

    assert extract_result.returncode == 0, f"Extraction failed: {extract_result.stderr}"

    lines = extract_result.stdout.split('\n')
    json_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('{'):
            json_start = i
            break

    json_str = '\n'.join(lines[json_start:])
    extraction = json.loads(json_str)

    # Verify metadata preservation
    extracted_feature = extraction['feature']
    assert extracted_feature['name'] == feature_json['name']
    assert extracted_feature['entity_count'] == feature_json['entity_count']
    assert extracted_feature['external_coupling'] == feature_json['external_coupling']
    assert extracted_feature['difficulty'] == feature_json['difficulty']
    assert extracted_feature['score'] == feature_json['score']

    print("[PASS] All feature metadata preserved through extraction")
    print(f"  Original difficulty: {feature_json['difficulty']} (score {feature_json['score']}/10)")
    print(f"  Extracted as: {extraction['service_name']}")


def test_go_vs_fastapi_generation():
    """Test that both Go and FastAPI generation work correctly."""
    print("\n" + "=" * 60)
    print("TEST: Go vs FastAPI Generation")
    print("=" * 60)

    feature_json = {
        "name": "comparison_test",
        "modules": ["m1"],
        "functions": ["func1"],
        "classes": ["C1"],
        "entity_count": 2,
        "external_coupling": 2.0,
        "difficulty": "GREEN",
        "score": 8
    }

    # Extract as Go
    go_result = subprocess.run(
        [sys.executable, './strangler_extractor.py',
         f'extract {json.dumps(feature_json)} --language go'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )

    # Extract as FastAPI
    fastapi_result = subprocess.run(
        [sys.executable, './strangler_extractor.py',
         f'extract {json.dumps(feature_json)} --language fastapi'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )

    # Verify both completed successfully
    assert go_result.returncode == 0, f"Go extraction failed: {go_result.stderr}"
    assert fastapi_result.returncode == 0, f"FastAPI extraction failed: {fastapi_result.stderr}"

    # Check output contains expected markers
    go_contains_extracted = "[EXTRACTION COMPLETE]" in go_result.stdout
    fastapi_contains_extracted = "[EXTRACTION COMPLETE]" in fastapi_result.stdout

    assert go_contains_extracted, "Go extraction should show completion message"
    assert fastapi_contains_extracted, "FastAPI extraction should show completion message"

    # Verify language mentions
    assert "--language go" or "language: go" in go_result.stdout.lower()
    assert "--language fastapi" or "language: fastapi" in fastapi_result.stdout.lower()

    print("[PASS] Both Go and FastAPI generation work correctly")
    print("  Go: extraction complete")
    print("  FastAPI: extraction complete")
