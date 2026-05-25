"""
Test zone_approval_gate.py — mandatory approval between PLAN and BUILD zones.
"""

import json
import tempfile
from pathlib import Path

import pytest

# Add scripts dir to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "one-shot-generator" / "scripts"))

from zone_approval_gate import enforce_zone_gate


@pytest.fixture
def sample_spec():
    """Create a minimal valid spec.json for testing."""
    return {
        "entities": [
            {
                "name": "User",
                "table_name": "users",
                "fields": [
                    {"name": "id", "type": "int"},
                    {"name": "name", "type": "str"},
                    {"name": "email", "type": "str"},
                ],
            }
        ],
        "relationships": [
            {"from": "User", "relationship_type": "has_many", "to": "Post"}
        ],
        "api_surface": [
            {"method": "POST", "path": "/users", "handler": "create_user"},
            {"method": "GET", "path": "/users", "handler": "list_users"},
        ],
        "test_contract": {"auth": "bearer", "pagination": "offset", "errors": "json"},
        "wiring": [{"target": "main.py", "action": "add_routes"}],
    }


def test_zone_approval_gate_bypassed_on_force(sample_spec):
    """Test that --force bypasses the approval gate."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_spec, f)
        spec_file = f.name

    try:
        result = enforce_zone_gate(
            spec_file=spec_file,
            arguments="--force",
            force_bypass=False,
        )
        assert result["status"] == "bypassed"
        assert result["bypass_reason"] == "force_flag"
    finally:
        Path(spec_file).unlink()


def test_zone_approval_gate_bypassed_on_skip_approval(sample_spec):
    """Test that --skip-approval bypasses the approval gate."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_spec, f)
        spec_file = f.name

    try:
        result = enforce_zone_gate(
            spec_file=spec_file,
            arguments="--skip-approval",
            force_bypass=False,
        )
        assert result["status"] == "bypassed"
        assert result["bypass_reason"] == "skip_approval_flag"
    finally:
        Path(spec_file).unlink()


def test_zone_approval_gate_bypassed_on_programmatic_override(sample_spec):
    """Test that force_bypass parameter bypasses the gate."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_spec, f)
        spec_file = f.name

    try:
        result = enforce_zone_gate(
            spec_file=spec_file,
            arguments="",
            force_bypass=True,  # Direct parameter override
        )
        assert result["status"] == "bypassed"
        assert result["bypass_reason"] == "programmatic_override"
    finally:
        Path(spec_file).unlink()


def test_zone_approval_gate_missing_spec():
    """Test that missing spec file fails gracefully."""
    with pytest.raises(SystemExit):
        enforce_zone_gate(
            spec_file="/nonexistent/spec.json",
            arguments="",
            force_bypass=False,
        )


def test_zone_approval_gate_malformed_spec(sample_spec):
    """Test that malformed JSON fails gracefully."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{malformed json")
        spec_file = f.name

    try:
        with pytest.raises(SystemExit):
            enforce_zone_gate(
                spec_file=spec_file,
                arguments="",
                force_bypass=False,
            )
    finally:
        Path(spec_file).unlink()


def test_zone_approval_gate_structure():
    """Test that gate returns correct JSON structure."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"entities": []}, f)
        spec_file = f.name

    try:
        result = enforce_zone_gate(
            spec_file=spec_file,
            arguments="--force",
            force_bypass=False,
        )
        assert "zone" in result
        assert result["zone"] == "PLAN_TO_BUILD_GATE"
        assert "status" in result
        assert "decision_time" in result
        assert "bypass_reason" in result
    finally:
        Path(spec_file).unlink()
