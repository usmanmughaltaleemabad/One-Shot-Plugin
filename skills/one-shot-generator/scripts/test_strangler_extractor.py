#!/usr/bin/env python3
"""
Integration tests for strangler_extractor.py

Tests microservice generation for Go and FastAPI.
Validates generated code structure and deployment configs.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def test_extract_go_service():
    """Test extraction of Go microservice."""
    print("\n" + "=" * 60)
    print("TEST: Extract Go Microservice")
    print("=" * 60)

    feature_json = {
        "name": "payment",
        "modules": ["payment_service", "payment_models", "payment_utils"],
        "functions": ["process_charge", "process_refund", "validate_card"],
        "classes": ["Payment", "Invoice", "Transaction"],
        "entity_count": 5,
        "external_coupling": 4.2,
        "difficulty": "YELLOW",
        "score": 6
    }

    result = subprocess.run(
        [sys.executable, './strangler_extractor.py',
         f'extract {json.dumps(feature_json)} --language go'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )

    assert result.returncode == 0, f"Extractor failed: {result.stderr}"

    # Parse JSON output
    lines = result.stdout.split('\n')
    json_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('{'):
            json_start = i
            break

    assert json_start is not None, "No JSON output"

    json_str = '\n'.join(lines[json_start:])
    data = json.loads(json_str)

    # Assertions
    assert data['status'] == 'extracted', "Status should be 'extracted'"
    assert data['service_name'] == 'payment', f"Service name should be 'payment', got {data['service_name']}"
    assert data['language'] == 'go', "Language should be 'go'"
    assert data['file_count'] > 0, "Should have generated files"
    assert len(data['files']['service']) > 0, "Should have service files"
    assert len(data['files']['deployment']) > 0, "Should have deployment files"

    print(f"[PASS] Generated {data['file_count']} files for payment service (Go)")
    print(f"  Service: {data['files']['service']}")
    print(f"  Deployment: {data['files']['deployment']}")


def test_extract_fastapi_service():
    """Test extraction of FastAPI microservice."""
    print("\n" + "=" * 60)
    print("TEST: Extract FastAPI Microservice")
    print("=" * 60)

    feature_json = {
        "name": "notification",
        "modules": ["notification_service", "notification_email", "notification_sms"],
        "functions": ["send_email", "send_sms", "send_push"],
        "classes": ["EmailNotifier", "SMSNotifier", "NotificationQueue"],
        "entity_count": 6,
        "external_coupling": 3.1,
        "difficulty": "GREEN",
        "score": 9
    }

    result = subprocess.run(
        [sys.executable, './strangler_extractor.py',
         f'extract {json.dumps(feature_json)} --language fastapi'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )

    assert result.returncode == 0, f"Extractor failed: {result.stderr}"

    # Parse JSON
    lines = result.stdout.split('\n')
    json_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('{'):
            json_start = i
            break

    json_str = '\n'.join(lines[json_start:])
    data = json.loads(json_str)

    # Assertions
    assert data['status'] == 'extracted'
    assert data['service_name'] == 'notification'
    assert data['language'] == 'fastapi'
    assert data['file_count'] > 0
    assert len(data['files']['service']) > 0

    print(f"[PASS] Generated {data['file_count']} files for notification service (FastAPI)")
    print(f"  Service: {data['files']['service']}")


def test_generated_dockerfile():
    """Test that generated Dockerfile is valid."""
    print("\n" + "=" * 60)
    print("TEST: Validate Generated Dockerfile")
    print("=" * 60)

    feature_json = {
        "name": "auth",
        "modules": ["auth_service", "auth_models"],
        "functions": ["login", "logout", "refresh_token"],
        "classes": ["User", "Token"],
        "entity_count": 4,
        "external_coupling": 2.5,
        "difficulty": "GREEN",
        "score": 8
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create a simple Python file
        (tmpdir / "auth_service.py").write_text("def login(): pass\n")

        result = subprocess.run(
            [sys.executable, './strangler_extractor.py',
             f'extract {json.dumps(feature_json)} --language fastapi'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        assert result.returncode == 0, f"Extraction failed: {result.stderr}"

        lines = result.stdout.split('\n')
        json_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_start = i
                break

        json_str = '\n'.join(lines[json_start:])
        data = json.loads(json_str)

        # Verify Dockerfile is in deployment files
        docker_files = [f for f in data['files']['deployment'] if f['path'] == 'Dockerfile']
        assert len(docker_files) > 0, "Should have generated Dockerfile"

        print(f"[PASS] Generated valid Dockerfile in deployment files")


def test_adapter_generation():
    """Test that adapter is generated for strangler pattern."""
    print("\n" + "=" * 60)
    print("TEST: Adapter Generation")
    print("=" * 60)

    feature_json = {
        "name": "order",
        "modules": ["order_service", "order_models"],
        "functions": ["create_order", "update_order", "cancel_order"],
        "classes": ["Order", "OrderItem"],
        "entity_count": 4,
        "external_coupling": 5.0,
        "difficulty": "YELLOW",
        "score": 5
    }

    result = subprocess.run(
        [sys.executable, './strangler_extractor.py',
         f'extract {json.dumps(feature_json)} --language go'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )

    assert result.returncode == 0, f"Extraction failed: {result.stderr}"

    lines = result.stdout.split('\n')
    json_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('{'):
            json_start = i
            break

    json_str = '\n'.join(lines[json_start:])
    data = json.loads(json_str)

    # Verify adapter files exist
    assert len(data['files']['adapter']) > 0, "Should have generated adapter files"

    print(f"[PASS] Generated {len(data['files']['adapter'])} adapter file(s)")
    print(f"  Adapter: {data['files']['adapter']}")


def test_migration_generation():
    """Test that database migrations are generated."""
    print("\n" + "=" * 60)
    print("TEST: Migration Generation")
    print("=" * 60)

    feature_json = {
        "name": "inventory",
        "modules": ["inventory_service", "inventory_models"],
        "functions": ["add_stock", "remove_stock", "get_inventory"],
        "classes": ["Inventory", "StockLevel"],
        "entity_count": 3,
        "external_coupling": 2.0,
        "difficulty": "GREEN",
        "score": 9
    }

    result = subprocess.run(
        [sys.executable, './strangler_extractor.py',
         f'extract {json.dumps(feature_json)} --language fastapi'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )

    assert result.returncode == 0, f"Extraction failed: {result.stderr}"

    lines = result.stdout.split('\n')
    json_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('{'):
            json_start = i
            break

    json_str = '\n'.join(lines[json_start:])
    data = json.loads(json_str)

    # Verify migration files
    assert len(data['files']['migrations']) > 0, "Should have generated migration files"

    print(f"[PASS] Generated {len(data['files']['migrations'])} migration file(s)")
    print(f"  Migrations: {data['files']['migrations']}")


def test_k8s_deployment_generation():
    """Test Kubernetes deployment generation."""
    print("\n" + "=" * 60)
    print("TEST: Kubernetes Deployment Generation")
    print("=" * 60)

    feature_json = {
        "name": "shipping",
        "modules": ["shipping_service", "shipping_models"],
        "functions": ["calculate_cost", "track_shipment"],
        "classes": ["Shipment", "ShippingRate"],
        "entity_count": 3,
        "external_coupling": 3.5,
        "difficulty": "YELLOW",
        "score": 7
    }

    result = subprocess.run(
        [sys.executable, './strangler_extractor.py',
         f'extract {json.dumps(feature_json)} --language go'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
    )

    assert result.returncode == 0, f"Extraction failed: {result.stderr}"

    lines = result.stdout.split('\n')
    json_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('{'):
            json_start = i
            break

    json_str = '\n'.join(lines[json_start:])
    data = json.loads(json_str)

    # Verify K8s files
    k8s_files = [f for f in data['files']['deployment'] if 'k8s' in f['path']]
    assert len(k8s_files) > 0, "Should have generated K8s deployment files"

    print(f"[PASS] Generated {len(k8s_files)} Kubernetes file(s)")
    print(f"  K8s: {k8s_files}")
