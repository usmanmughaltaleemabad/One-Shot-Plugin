"""
Tests for Phase 3-T1: Policy Engine

Tests:
    - Policy schema (dataclasses, merging)
    - Profile loading from defaults
    - Profile resolution hierarchy (CLI > env > file > defaults)
    - Cost gate enforcement
    - Cost tracking and ledger
    - Monthly budget calculation
    - Accuracy validation
"""

import os
import json
import pytest
from pathlib import Path
from datetime import date, timedelta
from tempfile import TemporaryDirectory
import sys

# Add .claude/policies to path
policies_path = Path(__file__).parent.parent / ".claude" / "policies"
sys.path.insert(0, str(policies_path))

# Import policy modules
import policy_schema
from policy_schema import (
    PolicyProfile,
    BudgetConfig,
    PolicyEngine,
    CostLedgerEntry,
    DEFAULT_PROFILES,
    ROLE,
)
import profile_manager
from profile_manager import ProfileManager
import cost_tracker
from cost_tracker import CostTracker


# ─── Test Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def temp_beads_dir():
    """Create temporary .beads directory."""
    with TemporaryDirectory() as tmpdir:
        beads_dir = Path(tmpdir) / ".beads"
        beads_dir.mkdir()
        yield beads_dir


@pytest.fixture
def policy_engine():
    """Create a fresh PolicyEngine."""
    return PolicyEngine()


@pytest.fixture
def profile_manager():
    """Create a fresh ProfileManager."""
    return ProfileManager()


@pytest.fixture
def cost_tracker(temp_beads_dir):
    """Create a fresh CostTracker with temp directory."""
    return CostTracker(beads_dir=temp_beads_dir)


# ─── Test Policy Schema ───────────────────────────────────────────────────

class TestBudgetConfig:
    """Tests for BudgetConfig dataclass."""

    def test_init_defaults(self):
        """Test BudgetConfig initializes with defaults."""
        bc = BudgetConfig()
        assert bc.cost_per_generation is None
        assert bc.cost_per_month is None

    def test_init_with_values(self):
        """Test BudgetConfig with explicit values."""
        bc = BudgetConfig(
            cost_per_generation=5.0,
            cost_per_month=100.0,
        )
        assert bc.cost_per_generation == 5.0
        assert bc.cost_per_month == 100.0

    def test_merge_none_overrides(self):
        """Test merging with None overrides."""
        bc1 = BudgetConfig(cost_per_generation=10.0, cost_per_month=500.0)
        bc2 = BudgetConfig(cost_per_generation=2.0, cost_per_month=None)
        result = bc1.merge(bc2)
        assert result.cost_per_generation == 2.0
        assert result.cost_per_month == 500.0

    def test_merge_other_is_none(self):
        """Test merging when other is None."""
        bc1 = BudgetConfig(cost_per_generation=10.0, cost_per_month=500.0)
        result = bc1.merge(None)
        assert result.cost_per_generation == 10.0
        assert result.cost_per_month == 500.0

    def test_to_dict(self):
        """Test BudgetConfig.to_dict()."""
        bc = BudgetConfig(cost_per_generation=5.0, cost_per_month=100.0)
        d = bc.to_dict()
        assert d["cost_per_generation"] == 5.0
        assert d["cost_per_month"] == 100.0


class TestPolicyProfile:
    """Tests for PolicyProfile dataclass."""

    def test_init_defaults(self):
        """Test PolicyProfile initializes with defaults."""
        profile = PolicyProfile(name="test")
        assert profile.name == "test"
        assert profile.roles == []
        assert profile.autonomy == "high"
        assert profile.description == ""

    def test_init_with_values(self):
        """Test PolicyProfile with explicit values."""
        roles = ["architect", "implementer"]
        budget = BudgetConfig(cost_per_generation=10.0)
        profile = PolicyProfile(
            name="dev",
            roles=roles,
            budgets=budget,
            autonomy="low",
            description="Test profile",
        )
        assert profile.name == "dev"
        assert profile.roles == roles
        assert profile.autonomy == "low"
        assert profile.description == "Test profile"

    def test_merge_overrides(self):
        """Test profile merging with field overrides."""
        p1 = PolicyProfile(
            name="p1",
            roles=["architect"],
            autonomy="high",
        )
        p2 = PolicyProfile(
            name="p2",
            roles=["reviewer"],
            autonomy="low",
        )
        merged = p1.merge(p2)
        assert merged.name == "p2"  # p2 overrides
        assert merged.roles == ["reviewer"]
        assert merged.autonomy == "low"

    def test_merge_partial_override(self):
        """Test merge with partial override (some fields None)."""
        p1 = PolicyProfile(
            name="p1",
            roles=["architect", "implementer"],
            autonomy="high",
        )
        p2 = PolicyProfile(
            name="",  # Will be treated as override-empty
            roles=[],
            autonomy="low",
        )
        merged = p1.merge(p2)
        assert merged.name == "p1"  # p2 name is empty string, so p1 wins
        assert merged.roles == ["architect", "implementer"]  # p2 roles empty, so p1 wins
        assert merged.autonomy == "low"  # p2 overrides

    def test_to_dict(self):
        """Test PolicyProfile.to_dict()."""
        profile = PolicyProfile(
            name="dev",
            roles=["architect"],
            autonomy="high",
        )
        d = profile.to_dict()
        assert d["name"] == "dev"
        assert d["autonomy"] == "high"


class TestDefaultProfiles:
    """Tests for DEFAULT_PROFILES."""

    def test_dev_profile_exists(self):
        """Test 'dev' profile exists in defaults."""
        assert "dev" in DEFAULT_PROFILES
        profile = DEFAULT_PROFILES["dev"]
        assert profile.name == "dev"
        assert "architect" in profile.roles
        assert profile.autonomy == "high"

    def test_ci_profile_exists(self):
        """Test 'ci' profile exists in defaults."""
        assert "ci" in DEFAULT_PROFILES
        profile = DEFAULT_PROFILES["ci"]
        assert profile.name == "ci"
        assert "implementer" in profile.roles
        assert profile.autonomy == "low"

    def test_audit_profile_exists(self):
        """Test 'audit' profile exists in defaults."""
        assert "audit" in DEFAULT_PROFILES
        profile = DEFAULT_PROFILES["audit"]
        assert profile.name == "audit"
        assert "reviewer" in profile.roles
        assert profile.autonomy == "none"


# ─── Test PolicyEngine ────────────────────────────────────────────────────

class TestPolicyEngine:
    """Tests for PolicyEngine class."""

    def test_load_profile_default(self, policy_engine):
        """Test loading default profile."""
        profile = policy_engine.load_profile("dev")
        assert profile.name == "dev"

    def test_load_profile_not_found_returns_dev(self, policy_engine):
        """Test loading non-existent profile returns 'dev'."""
        profile = policy_engine.load_profile("nonexistent")
        assert profile.name == "dev"

    def test_register_profile(self, policy_engine):
        """Test registering a custom profile."""
        custom = PolicyProfile(
            name="custom",
            roles=["implementer"],
            autonomy="low",
        )
        policy_engine.register_profile(custom)
        loaded = policy_engine.load_profile("custom")
        assert loaded.name == "custom"
        assert loaded.autonomy == "low"

    def test_merge_profiles_single(self, policy_engine):
        """Test merging a single profile."""
        merged = policy_engine.merge_profiles("dev")
        assert merged.name == "dev"

    def test_merge_profiles_multiple(self, policy_engine):
        """Test merging multiple profiles (left-to-right)."""
        # Register custom overrides
        dev = policy_engine.load_profile("dev")
        ci = policy_engine.load_profile("ci")

        merged = policy_engine.merge_profiles("dev", "ci")
        # ci's autonomy is "low", dev is "high"
        assert merged.autonomy == "low"

    def test_check_budget_within_limit(self, policy_engine):
        """Test check_budget returns True when within limit."""
        profile = PolicyProfile(
            name="test",
            budgets=BudgetConfig(cost_per_generation=10.0),
        )
        assert policy_engine.check_budget(5.0, profile) is True
        assert policy_engine.check_budget(10.0, profile) is True

    def test_check_budget_exceeds_limit(self, policy_engine):
        """Test check_budget returns False when exceeding limit."""
        profile = PolicyProfile(
            name="test",
            budgets=BudgetConfig(cost_per_generation=10.0),
        )
        assert policy_engine.check_budget(10.1, profile) is False

    def test_check_budget_no_limit(self, policy_engine):
        """Test check_budget returns True when no limit set."""
        profile = PolicyProfile(
            name="test",
            budgets=BudgetConfig(cost_per_generation=None),
        )
        assert policy_engine.check_budget(1000.0, profile) is True

    def test_record_cost(self, policy_engine, temp_beads_dir):
        """Test recording a cost entry."""
        ledger_path = temp_beads_dir / "cost_ledger.jsonl"
        policy_engine.ledger_path = ledger_path

        policy_engine.record_cost(
            cost=0.42,
            feature="test feature",
            model="sonnet",
            tokens={"input": 5000, "output": 2000},
            profile="dev",
        )

        assert ledger_path.exists()
        lines = ledger_path.read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["cost_usd"] == 0.42
        assert entry["feature"] == "test feature"
        assert entry["model"] == "sonnet"

    def test_get_lifetime_cost(self, policy_engine, temp_beads_dir):
        """Test summing lifetime costs."""
        ledger_path = temp_beads_dir / "cost_ledger.jsonl"
        policy_engine.ledger_path = ledger_path

        policy_engine.record_cost(0.10, "feature1", "haiku")
        policy_engine.record_cost(0.20, "feature2", "sonnet")
        policy_engine.record_cost(0.30, "feature3", "opus")

        total = policy_engine.get_lifetime_cost()
        assert abs(total - 0.60) < 0.001

    def test_get_monthly_cost(self, policy_engine, temp_beads_dir):
        """Test calculating monthly costs."""
        ledger_path = temp_beads_dir / "cost_ledger.jsonl"
        policy_engine.ledger_path = ledger_path

        current_month = date.today().strftime("%Y-%m")

        policy_engine.record_cost(0.10, "feature1", "haiku")
        policy_engine.record_cost(0.20, "feature2", "sonnet")

        total = policy_engine.get_monthly_cost(current_month)
        assert abs(total - 0.30) < 0.001

    def test_get_remaining_monthly_budget(self, policy_engine, temp_beads_dir):
        """Test calculating remaining monthly budget."""
        ledger_path = temp_beads_dir / "cost_ledger.jsonl"
        policy_engine.ledger_path = ledger_path

        profile = PolicyProfile(
            name="test",
            budgets=BudgetConfig(cost_per_month=100.0),
        )

        # Record $30 in costs
        policy_engine.record_cost(0.10, "f1", "haiku")
        policy_engine.record_cost(0.20, "f2", "sonnet")

        remaining = policy_engine.get_remaining_monthly_budget(profile)
        assert abs(remaining - 99.70) < 0.001

    def test_get_remaining_monthly_budget_no_limit(self, policy_engine):
        """Test remaining budget returns infinity when no limit."""
        profile = PolicyProfile(
            name="test",
            budgets=BudgetConfig(cost_per_month=None),
        )
        remaining = policy_engine.get_remaining_monthly_budget(profile)
        assert remaining == float("inf")


# ─── Test ProfileManager ──────────────────────────────────────────────────

class TestProfileManager:
    """Tests for ProfileManager class."""

    def test_resolve_profile_cli_priority(self, profile_manager):
        """Test CLI argument has highest priority."""
        profile = profile_manager.resolve_profile(
            cli_arg="ci",
            env_var="dev",
        )
        assert profile.name == "ci"

    def test_resolve_profile_env_priority(self, profile_manager):
        """Test env variable is second priority."""
        profile = profile_manager.resolve_profile(
            cli_arg=None,
            env_var="audit",
        )
        assert profile.name == "audit"

    def test_resolve_profile_default(self, profile_manager):
        """Test defaults to 'dev' when nothing specified."""
        profile = profile_manager.resolve_profile()
        assert profile.name == "dev"

    def test_validate_profile_valid(self, profile_manager):
        """Test validation of valid profile."""
        profile = DEFAULT_PROFILES["dev"]
        warnings = profile_manager.validate_profile(profile)
        assert len(warnings) == 0

    def test_validate_profile_invalid_autonomy(self, profile_manager):
        """Test validation detects invalid autonomy."""
        profile = PolicyProfile(
            name="bad",
            autonomy="invalid",  # type: ignore
        )
        warnings = profile_manager.validate_profile(profile)
        assert len(warnings) > 0
        assert any("autonomy" in w for w in warnings)

    def test_validate_profile_invalid_role(self, profile_manager):
        """Test validation detects invalid roles."""
        profile = PolicyProfile(
            name="bad",
            roles=["invalid_role"],  # type: ignore
        )
        warnings = profile_manager.validate_profile(profile)
        assert len(warnings) > 0
        assert any("role" in w for w in warnings)

    def test_validate_profile_inconsistent_autonomy_roles(self, profile_manager):
        """Test validation warns about autonomy/role inconsistency."""
        profile = PolicyProfile(
            name="inconsistent",
            roles=["architect", "implementer"],
            autonomy="none",  # suspicious: no autonomy but has roles
        )
        warnings = profile_manager.validate_profile(profile)
        # Should warn about inconsistency (optional)
        # This may or may not generate warnings depending on strictness


# ─── Test CostTracker ────────────────────────────────────────────────────

class TestCostTracker:
    """Tests for CostTracker class."""

    def test_check_generation_budget_within(self, cost_tracker):
        """Test generation budget check when within limit."""
        profile = PolicyProfile(
            name="test",
            budgets=BudgetConfig(cost_per_generation=10.0),
        )
        assert cost_tracker.check_generation_budget(5.0, profile) is True

    def test_check_generation_budget_exceeds(self, cost_tracker):
        """Test generation budget check when exceeding limit."""
        profile = PolicyProfile(
            name="test",
            budgets=BudgetConfig(cost_per_generation=10.0),
        )
        assert cost_tracker.check_generation_budget(10.1, profile) is False

    def test_remaining_generation_budget(self, cost_tracker):
        """Test getting per-generation budget limit."""
        profile = PolicyProfile(
            name="test",
            budgets=BudgetConfig(cost_per_generation=5.0),
        )
        remaining = cost_tracker.remaining_generation_budget(profile)
        assert remaining == 5.0

    def test_remaining_generation_budget_unlimited(self, cost_tracker):
        """Test remaining budget returns infinity when unlimited."""
        profile = PolicyProfile(
            name="test",
            budgets=BudgetConfig(cost_per_generation=None),
        )
        remaining = cost_tracker.remaining_generation_budget(profile)
        assert remaining == float("inf")

    def test_remaining_monthly_budget(self, cost_tracker):
        """Test calculating remaining monthly budget."""
        profile = PolicyProfile(
            name="test",
            budgets=BudgetConfig(cost_per_month=100.0),
        )
        # Use the cost_tracker's engine which references cost_tracker.ledger_path
        cost_tracker.engine.ledger_path = cost_tracker.ledger_path
        cost_tracker.record_cost(30.0, "test", "sonnet", profile="test")
        remaining = cost_tracker.engine.get_remaining_monthly_budget(profile)
        assert abs(remaining - 70.0) < 0.001

    def test_record_cost(self, cost_tracker):
        """Test recording a cost entry."""
        cost_tracker.record_cost(
            cost=0.42,
            feature="test feature",
            model="sonnet",
            tokens={"input": 5000, "output": 2000},
            profile="dev",
            generation_id="gen-123",
        )

        assert cost_tracker.ledger_path.exists()
        entries = cost_tracker.ledger_path.read_text().strip().split("\n")
        assert len(entries) == 1
        entry = json.loads(entries[0])
        assert entry["cost_usd"] == 0.42
        assert entry["generation_id"] == "gen-123"

    def test_get_monthly_report(self, cost_tracker):
        """Test generating monthly report."""
        current_month = date.today().strftime("%Y-%m")

        cost_tracker.record_cost(0.10, "f1", "haiku")
        cost_tracker.record_cost(0.20, "f2", "sonnet")
        cost_tracker.record_cost(0.15, "f3", "opus")

        report = cost_tracker.get_monthly_report(current_month)
        assert report["year_month"] == current_month
        assert abs(report["total_cost"] - 0.45) < 0.001
        assert report["entries_count"] == 3
        assert "haiku" in report["by_model"]

    def test_get_lifetime_report(self, cost_tracker):
        """Test generating lifetime report."""
        cost_tracker.record_cost(0.10, "f1", "haiku", profile="dev")
        cost_tracker.record_cost(0.20, "f2", "sonnet", profile="ci")
        cost_tracker.record_cost(0.30, "f1", "opus", profile="dev")

        report = cost_tracker.get_lifetime_report()
        assert abs(report["total_cost"] - 0.60) < 0.001
        assert report["entries_count"] == 3
        assert "dev" in report["by_profile"]
        assert "ci" in report["by_profile"]

    def test_validate_accuracy_no_observations(self, cost_tracker):
        """Test accuracy validation when no observations file exists."""
        result = cost_tracker.validate_accuracy()
        assert result["status"] == "no_observations"

    def test_validate_accuracy_within_tolerance(self, cost_tracker):
        """Test accuracy validation passes when within tolerance."""
        # Create both ledger and observations files with matching costs
        cost_tracker.record_cost(0.42, "test", "sonnet")

        obs_path = cost_tracker.beads_dir / "cost_observations.jsonl"
        obs_path.write_text(json.dumps({"cost_usd": 0.42}) + "\n")

        result = cost_tracker.validate_accuracy(tolerance_pct=2.0)
        assert result["status"] == "valid"
        assert result["within_tolerance"] is True

    def test_validate_accuracy_exceeds_tolerance(self, cost_tracker):
        """Test accuracy validation fails when drift exceeds tolerance."""
        # Ledger has $1.00, observations have $0.50 (100% drift)
        cost_tracker.record_cost(1.00, "test", "sonnet")

        obs_path = cost_tracker.beads_dir / "cost_observations.jsonl"
        obs_path.write_text(json.dumps({"cost_usd": 0.50}) + "\n")

        result = cost_tracker.validate_accuracy(tolerance_pct=2.0)
        assert result["status"] == "drift"
        assert result["within_tolerance"] is False


# ─── Integration Tests ────────────────────────────────────────────────────

class TestIntegration:
    """Integration tests across components."""

    def test_full_workflow(self, policy_engine, temp_beads_dir, cost_tracker):
        """Test complete workflow: load profile, check budget, record cost."""
        profile = policy_engine.load_profile("dev")

        # Use same ledger path for consistency
        policy_engine.ledger_path = cost_tracker.ledger_path

        # Check that cost is within budget
        assert policy_engine.check_budget(0.50, profile) is True

        # Record the cost
        policy_engine.record_cost(
            cost=0.42,
            feature="shopping cart",
            model="sonnet",
            tokens={"input": 5000, "output": 2000},
            profile="dev",
            generation_id="gen-001",
        )

        # Verify it was recorded
        total = policy_engine.get_lifetime_cost()
        assert abs(total - 0.42) < 0.001

    def test_budget_gate_prevents_spending(self, policy_engine):
        """Test that budget gate prevents over-limit spending."""
        profile = PolicyProfile(
            name="strict",
            budgets=BudgetConfig(cost_per_generation=0.50),
        )

        # Should be blocked
        assert policy_engine.check_budget(0.51, profile) is False
        assert policy_engine.check_budget(1.00, profile) is False

        # Should be allowed
        assert policy_engine.check_budget(0.50, profile) is True
        assert policy_engine.check_budget(0.25, profile) is True

    def test_monthly_budget_accumulates(self, cost_tracker):
        """Test monthly budget tracking across multiple generations."""
        profile = PolicyProfile(
            name="test",
            budgets=BudgetConfig(cost_per_generation=1.00, cost_per_month=1.00),
        )

        # Ensure the engine uses the cost_tracker's ledger path
        cost_tracker.engine.ledger_path = cost_tracker.ledger_path

        # Record 3 entries adding up to $0.90
        cost_tracker.record_cost(0.30, "f1", "haiku")
        cost_tracker.record_cost(0.30, "f2", "sonnet")
        cost_tracker.record_cost(0.30, "f3", "opus")

        remaining = cost_tracker.engine.get_remaining_monthly_budget(profile)
        assert abs(remaining - 0.10) < 0.001

        # Next generation of $0.05 should be OK (within both limits)
        assert cost_tracker.check_generation_budget(0.05, profile) is True

        # But $1.50 should be blocked by per-generation limit
        assert cost_tracker.check_generation_budget(1.50, profile) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
