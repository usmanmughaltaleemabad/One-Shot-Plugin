#!/usr/bin/env python3
"""
Policy Schema — v1.0.0 (Phase 3-T1: Policy Engine)

Pydantic models for policy profiles, budget tracking, and autonomy levels.
Defines the contract for profile merging and cost gate enforcement.

CLI:
    from policy_schema import PolicyProfile, PolicyEngine
    engine = PolicyEngine()
    profile = engine.load_profile("dev")
    if engine.check_budget(0.50, profile):
        # Safe to proceed
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Literal, Any
from pathlib import Path
from datetime import datetime, date
import json


# ─── Autonomy Levels ────────────────────────────────────────────────────────

AUT_LEVEL = Literal["none", "low", "high"]
ROLE = Literal["architect", "implementer", "test-author", "reviewer", "critic", "wirer"]


# ─── Budget Configuration ───────────────────────────────────────────────────

@dataclass
class BudgetConfig:
    """Cost limits for a profile."""
    cost_per_generation: Optional[float] = None
    """Max USD spend per single generation (e.g., 10.0)."""

    cost_per_month: Optional[float] = None
    """Max USD spend per calendar month (e.g., 500.0)."""

    def merge(self, other: BudgetConfig | None) -> BudgetConfig:
        """Merge two budget configs; other overrides self."""
        if other is None:
            return BudgetConfig(
                cost_per_generation=self.cost_per_generation,
                cost_per_month=self.cost_per_month,
            )
        return BudgetConfig(
            cost_per_generation=other.cost_per_generation or self.cost_per_generation,
            cost_per_month=other.cost_per_month or self.cost_per_month,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─── Policy Profile ────────────────────────────────────────────────────────

@dataclass
class PolicyProfile:
    """Defines roles, budgets, and autonomy for a profile."""
    name: str
    """Profile name (e.g., 'dev', 'ci', 'audit')."""

    roles: List[ROLE] = field(default_factory=list)
    """Agent roles allowed in this profile."""

    budgets: BudgetConfig = field(default_factory=BudgetConfig)
    """Cost limits for this profile."""

    autonomy: AUT_LEVEL = "high"
    """Autonomy level: 'none' (manual approval), 'low' (checks required),
    'high' (self-directed)."""

    description: str = ""
    """Human-readable profile description."""

    def merge(self, other: PolicyProfile | None) -> PolicyProfile:
        """Merge two profiles; other's non-empty fields override self."""
        if other is None:
            return PolicyProfile(
                name=self.name,
                roles=self.roles,
                budgets=self.budgets,
                autonomy=self.autonomy,
                description=self.description,
            )
        return PolicyProfile(
            name=other.name or self.name,
            roles=other.roles or self.roles,
            budgets=self.budgets.merge(other.budgets),
            autonomy=other.autonomy or self.autonomy,
            description=other.description or self.description,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "roles": self.roles,
            "budgets": self.budgets.to_dict(),
            "autonomy": self.autonomy,
            "description": self.description,
        }


# ─── Default Profiles ──────────────────────────────────────────────────────

DEFAULT_PROFILES = {
    "dev": PolicyProfile(
        name="dev",
        roles=["architect", "implementer", "test-author", "reviewer", "critic"],
        budgets=BudgetConfig(
            cost_per_generation=10.0,
            cost_per_month=500.0,
        ),
        autonomy="high",
        description="Development profile with full agent access and high budgets.",
    ),
    "ci": PolicyProfile(
        name="ci",
        roles=["implementer", "reviewer"],
        budgets=BudgetConfig(
            cost_per_generation=2.0,
            cost_per_month=100.0,
        ),
        autonomy="low",
        description="CI/CD profile with limited agents and tight budgets.",
    ),
    "audit": PolicyProfile(
        name="audit",
        roles=["reviewer"],
        budgets=BudgetConfig(
            cost_per_generation=5.0,
            cost_per_month=50.0,
        ),
        autonomy="none",
        description="Audit profile allowing only review agents, no generation.",
    ),
}


# ─── Cost Ledger Entry ──────────────────────────────────────────────────────

@dataclass
class CostLedgerEntry:
    """Single cost entry in the ledger."""
    date: str
    """ISO 8601 date (YYYY-MM-DD)."""

    feature: str
    """User-provided feature description."""

    cost_usd: float
    """Actual cost in USD."""

    model: str
    """Model used (e.g., 'haiku', 'sonnet')."""

    tokens: Dict[str, int] = field(default_factory=dict)
    """Token counts: {'input': 1000, 'output': 500}."""

    profile: str = "dev"
    """Profile used for generation."""

    generation_id: str = ""
    """Unique generation ID for correlation."""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─── Policy Engine ─────────────────────────────────────────────────────────

class PolicyEngine:
    """Main interface for policy management, budget checks, and cost tracking."""

    def __init__(self, ledger_path: Path | None = None):
        """Initialize policy engine.

        Args:
            ledger_path: Path to cost ledger file (default: .beads/cost_ledger.jsonl)
        """
        self.profiles: Dict[str, PolicyProfile] = DEFAULT_PROFILES.copy()
        self.ledger_path = ledger_path or Path.home() / ".cache" / "one-shot" / "cost_ledger.jsonl"
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def load_profile(self, name: str) -> PolicyProfile:
        """Load a profile by name.

        Returns default profile if not found.
        """
        if name not in self.profiles:
            return self.profiles.get("dev", DEFAULT_PROFILES["dev"])
        return self.profiles[name]

    def register_profile(self, profile: PolicyProfile) -> None:
        """Register a new or override existing profile."""
        self.profiles[profile.name] = profile

    def merge_profiles(self, *names: str) -> PolicyProfile:
        """Merge multiple profiles in order (left-to-right merge).

        Example:
            merged = engine.merge_profiles("dev", "audit")
            # audit overrides dev where both exist
        """
        if not names:
            return self.load_profile("dev")

        result = self.load_profile(names[0])
        for name in names[1:]:
            other = self.load_profile(name)
            result = result.merge(other)
        return result

    def check_budget(self, cost: float, profile: PolicyProfile) -> bool:
        """Check if cost is within budget limits.

        Args:
            cost: Cost in USD
            profile: Policy profile

        Returns:
            True if within limit, False otherwise
        """
        if profile.budgets.cost_per_generation is None:
            return True

        return cost <= profile.budgets.cost_per_generation

    def get_remaining_monthly_budget(self, profile: PolicyProfile) -> float:
        """Calculate remaining monthly budget by reading ledger.

        Args:
            profile: Policy profile

        Returns:
            Remaining USD budget for this month
        """
        if profile.budgets.cost_per_month is None:
            return float("inf")

        today = date.today()
        current_month = today.strftime("%Y-%m")
        spent = 0.0

        if self.ledger_path.exists():
            for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    entry_dict = json.loads(line)
                    entry_date = entry_dict.get("date", "")
                    if entry_date.startswith(current_month):
                        spent += float(entry_dict.get("cost_usd", 0.0))
                except json.JSONDecodeError:
                    pass

        remaining = profile.budgets.cost_per_month - spent
        return max(0.0, remaining)

    def record_cost(self, cost: float, feature: str, model: str = "sonnet",
                    tokens: Dict[str, int] | None = None,
                    profile: str = "dev",
                    generation_id: str = "") -> None:
        """Record a cost entry in the ledger.

        Args:
            cost: Cost in USD
            feature: Feature description
            model: Model name
            tokens: Token counts {'input': X, 'output': Y}
            profile: Profile name
            generation_id: Unique generation ID
        """
        entry = CostLedgerEntry(
            date=date.today().isoformat(),
            feature=feature,
            cost_usd=cost,
            model=model,
            tokens=tokens or {},
            profile=profile,
            generation_id=generation_id,
        )

        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def get_lifetime_cost(self) -> float:
        """Get total cost across all ledger entries."""
        if not self.ledger_path.exists():
            return 0.0

        total = 0.0
        for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry_dict = json.loads(line)
                total += float(entry_dict.get("cost_usd", 0.0))
            except json.JSONDecodeError:
                pass

        return round(total, 4)

    def get_monthly_cost(self, year_month: str | None = None) -> float:
        """Get cost for a specific month (YYYY-MM format).

        Args:
            year_month: Month to query (default: current month)

        Returns:
            Total cost in USD for that month
        """
        if year_month is None:
            year_month = date.today().strftime("%Y-%m")

        if not self.ledger_path.exists():
            return 0.0

        total = 0.0
        for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry_dict = json.loads(line)
                entry_date = entry_dict.get("date", "")
                if entry_date.startswith(year_month):
                    total += float(entry_dict.get("cost_usd", 0.0))
            except json.JSONDecodeError:
                pass

        return round(total, 4)
