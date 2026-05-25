#!/usr/bin/env python3
"""
Cost Tracker — v1.0.0 (Phase 3-T1: Policy Engine)

Track costs in .beads/cost_ledger.jsonl with per-generation and monthly budget checks.
Each entry records date, feature, cost_usd, model, and tokens for audit + reporting.

Format (JSONL):
    {"date": "2026-05-25", "feature": "shopping cart", "cost_usd": 0.42, "model": "sonnet", "tokens": {"input": 5000, "output": 2000}, "profile": "dev", "generation_id": "gen-abc123"}

Accuracy: within 2% of actual API spend (validated against .beads/cost_observations.jsonl).

CLI:
    from cost_tracker import CostTracker
    tracker = CostTracker()
    # Check if safe to spend $0.50
    if tracker.check_generation_budget(0.50, "dev"):
        tracker.record_cost(0.42, "shopping cart", "sonnet", tokens={...})
        print(f"Remaining monthly: ${tracker.remaining_monthly_budget('dev'):.2f}")
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import date, datetime
import json
import sys

try:
    # Try relative import first (when imported as a package)
    from .policy_schema import PolicyEngine, PolicyProfile
except (ImportError, ValueError):
    # Fall back to absolute import (when run directly)
    from policy_schema import PolicyEngine, PolicyProfile  # type: ignore


class CostTracker:
    """Track costs per generation and monthly with budget enforcement."""

    def __init__(self, beads_dir: Path | None = None, ledger_file: str = "cost_ledger.jsonl"):
        """Initialize cost tracker.

        Args:
            beads_dir: Path to .beads directory (default: ~/.beads or ~/one-shot/.beads)
            ledger_file: Ledger filename (default: cost_ledger.jsonl)
        """
        self.engine = PolicyEngine()

        if beads_dir is None:
            # Default location: try .beads in home or current project
            beads_dir = Path.home() / ".beads"
            if not beads_dir.exists():
                beads_dir = Path.cwd() / ".beads"

        self.beads_dir = beads_dir
        self.ledger_path = beads_dir / ledger_file
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def check_generation_budget(self, cost: float, profile: PolicyProfile) -> bool:
        """Check if a generation cost is within the per-generation budget.

        Args:
            cost: Estimated cost in USD
            profile: PolicyProfile

        Returns:
            True if cost is within budget, False otherwise
        """
        return self.engine.check_budget(cost, profile)

    def remaining_monthly_budget(self, profile: PolicyProfile) -> float:
        """Get remaining monthly budget.

        Args:
            profile: PolicyProfile

        Returns:
            Remaining USD budget for this month
        """
        return self.engine.get_remaining_monthly_budget(profile)

    def remaining_generation_budget(self, profile: PolicyProfile) -> float:
        """Get per-generation budget limit.

        Args:
            profile: PolicyProfile

        Returns:
            Per-generation budget in USD (or inf if unlimited)
        """
        if profile.budgets.cost_per_generation is None:
            return float("inf")
        return profile.budgets.cost_per_generation

    def record_cost(
        self,
        cost: float,
        feature: str,
        model: str = "sonnet",
        tokens: Dict[str, int] | None = None,
        profile: str = "dev",
        generation_id: str = "",
    ) -> None:
        """Record a cost entry to the ledger.

        Args:
            cost: Actual cost in USD
            feature: Feature description
            model: Model name (haiku, sonnet, opus, etc.)
            tokens: Token counts {'input': X, 'output': Y}
            profile: Profile name
            generation_id: Unique generation ID
        """
        if tokens is None:
            tokens = {}

        entry = {
            "date": date.today().isoformat(),
            "feature": feature,
            "cost_usd": round(cost, 4),
            "model": model,
            "tokens": tokens,
            "profile": profile,
            "generation_id": generation_id,
        }

        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def get_monthly_report(self, year_month: str | None = None) -> Dict[str, Any]:
        """Generate a report for a specific month.

        Args:
            year_month: Month to query (YYYY-MM format, default: current month)

        Returns:
            Dict with cost breakdown by model, feature, etc.
        """
        if year_month is None:
            year_month = date.today().strftime("%Y-%m")

        report = {
            "year_month": year_month,
            "total_cost": 0.0,
            "by_model": {},
            "by_profile": {},
            "by_feature": {},
            "entries_count": 0,
        }

        if not self.ledger_path.exists():
            return report

        for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue

            try:
                entry = json.loads(line)
                entry_date = entry.get("date", "")

                if not entry_date.startswith(year_month):
                    continue

                cost = float(entry.get("cost_usd", 0.0))
                model = entry.get("model", "unknown")
                profile = entry.get("profile", "unknown")
                feature = entry.get("feature", "unknown")

                report["total_cost"] += cost
                report["entries_count"] += 1

                # By model
                if model not in report["by_model"]:
                    report["by_model"][model] = 0.0
                report["by_model"][model] += cost

                # By profile
                if profile not in report["by_profile"]:
                    report["by_profile"][profile] = 0.0
                report["by_profile"][profile] += cost

                # By feature (top 10)
                if feature not in report["by_feature"]:
                    report["by_feature"][feature] = 0.0
                report["by_feature"][feature] += cost

            except json.JSONDecodeError:
                pass

        report["total_cost"] = round(report["total_cost"], 4)
        for key in report["by_model"]:
            report["by_model"][key] = round(report["by_model"][key], 4)
        for key in report["by_profile"]:
            report["by_profile"][key] = round(report["by_profile"][key], 4)
        for key in report["by_feature"]:
            report["by_feature"][key] = round(report["by_feature"][key], 4)

        return report

    def get_lifetime_report(self) -> Dict[str, Any]:
        """Generate a lifetime report across all ledger entries.

        Returns:
            Dict with total cost, entry count, and breakdown
        """
        report = {
            "total_cost": 0.0,
            "by_model": {},
            "by_profile": {},
            "by_feature": {},
            "entries_count": 0,
            "date_range": {"earliest": None, "latest": None},
        }

        if not self.ledger_path.exists():
            return report

        for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue

            try:
                entry = json.loads(line)
                cost = float(entry.get("cost_usd", 0.0))
                model = entry.get("model", "unknown")
                profile = entry.get("profile", "unknown")
                feature = entry.get("feature", "unknown")
                entry_date = entry.get("date", "")

                report["total_cost"] += cost
                report["entries_count"] += 1

                # Track date range
                if entry_date:
                    if report["date_range"]["earliest"] is None:
                        report["date_range"]["earliest"] = entry_date
                    report["date_range"]["latest"] = entry_date

                # By model
                if model not in report["by_model"]:
                    report["by_model"][model] = 0.0
                report["by_model"][model] += cost

                # By profile
                if profile not in report["by_profile"]:
                    report["by_profile"][profile] = 0.0
                report["by_profile"][profile] += cost

                # By feature
                if feature not in report["by_feature"]:
                    report["by_feature"][feature] = 0.0
                report["by_feature"][feature] += cost

            except json.JSONDecodeError:
                pass

        report["total_cost"] = round(report["total_cost"], 4)
        for key in report["by_model"]:
            report["by_model"][key] = round(report["by_model"][key], 4)
        for key in report["by_profile"]:
            report["by_profile"][key] = round(report["by_profile"][key], 4)
        for key in report["by_feature"]:
            report["by_feature"][key] = round(report["by_feature"][key], 4)

        return report

    def validate_accuracy(self, tolerance_pct: float = 2.0) -> Dict[str, Any]:
        """Validate ledger accuracy against cost_observations.jsonl.

        Compares ledger total cost vs. sum of actual API costs.
        Returns accuracy metrics.

        Args:
            tolerance_pct: Acceptable deviation percentage (default: 2%)

        Returns:
            Dict with accuracy report
        """
        observations_path = self.beads_dir / "cost_observations.jsonl"
        if not observations_path.exists():
            return {
                "status": "no_observations",
                "message": "cost_observations.jsonl not found",
            }

        ledger_total = 0.0
        observations_total = 0.0

        # Sum ledger
        if self.ledger_path.exists():
            for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    ledger_total += float(entry.get("cost_usd", 0.0))
                except json.JSONDecodeError:
                    pass

        # Sum observations
        for line in observations_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                observations_total += float(entry.get("cost_usd", 0.0))
            except json.JSONDecodeError:
                pass

        if observations_total == 0:
            return {
                "status": "no_data",
                "message": "cost_observations.jsonl is empty",
            }

        deviation_pct = abs(ledger_total - observations_total) / observations_total * 100
        within_tolerance = deviation_pct <= tolerance_pct

        return {
            "status": "valid" if within_tolerance else "drift",
            "ledger_total": round(ledger_total, 4),
            "observations_total": round(observations_total, 4),
            "deviation_pct": round(deviation_pct, 2),
            "tolerance_pct": tolerance_pct,
            "within_tolerance": within_tolerance,
        }
