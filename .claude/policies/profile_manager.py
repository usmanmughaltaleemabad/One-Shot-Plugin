#!/usr/bin/env python3
"""
Profile Manager — v1.0.0 (Phase 3-T1: Policy Engine)

Load policy profiles from multiple sources with fallback hierarchy:
  1. CLI argument (--profile name)
  2. Environment variable (OSP_PROFILE)
  3. Config file (~/.claude/one-shot.policy.yml)
  4. Defaults (dev, ci, audit)

Validates and merges profiles according to hierarchy.

CLI:
    from profile_manager import ProfileManager
    mgr = ProfileManager()
    profile = mgr.resolve_profile(cli_arg="ci", env_vars=os.environ)
    print(f"Using profile: {profile.name}")
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

try:
    # Try relative import first (when imported as a package)
    from .policy_schema import PolicyProfile, BudgetConfig, PolicyEngine, DEFAULT_PROFILES
except (ImportError, ValueError):
    # Fall back to absolute import (when run directly)
    from policy_schema import PolicyProfile, BudgetConfig, PolicyEngine, DEFAULT_PROFILES  # type: ignore


class ProfileManager:
    """Load and resolve policy profiles from multiple sources."""

    def __init__(self):
        """Initialize profile manager."""
        self.engine = PolicyEngine()
        self._loaded_from_file: Dict[str, PolicyProfile] = {}

    def _load_yaml_file(self, path: Path) -> Dict[str, Any]:
        """Load YAML file; return empty dict if file missing or YAML unavailable."""
        if not path.exists():
            return {}

        if yaml is None:
            # Graceful fallback if PyYAML not installed
            print(f"[WARN] PyYAML not available. Skipping config file: {path}", file=sys.stderr)
            return {}

        try:
            with path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"[WARN] Failed to load {path}: {e}", file=sys.stderr)
            return {}

    def _parse_profiles_from_yaml(self, yaml_dict: Dict[str, Any]) -> Dict[str, PolicyProfile]:
        """Parse 'profiles' section from YAML config."""
        profiles = {}
        profiles_section = yaml_dict.get("profiles", {})

        if not isinstance(profiles_section, dict):
            return profiles

        for name, spec in profiles_section.items():
            if not isinstance(spec, dict):
                continue

            roles = spec.get("roles", [])
            budgets_spec = spec.get("budgets", {})
            autonomy = spec.get("autonomy", "high")
            description = spec.get("description", "")

            budgets = BudgetConfig(
                cost_per_generation=budgets_spec.get("cost_per_generation"),
                cost_per_month=budgets_spec.get("cost_per_month"),
            )

            profiles[name] = PolicyProfile(
                name=name,
                roles=roles,
                budgets=budgets,
                autonomy=autonomy,
                description=description,
            )

        return profiles

    def load_from_file(self, config_path: Path | None = None) -> Dict[str, PolicyProfile]:
        """Load profiles from YAML config file.

        Args:
            config_path: Path to config (default: ~/.claude/one-shot.policy.yml)

        Returns:
            Dict of loaded profiles
        """
        if config_path is None:
            config_path = Path.home() / ".claude" / "one-shot.policy.yml"

        yaml_dict = self._load_yaml_file(config_path)
        profiles = self._parse_profiles_from_yaml(yaml_dict)

        self._loaded_from_file = profiles
        for name, profile in profiles.items():
            self.engine.register_profile(profile)

        return profiles

    def resolve_profile(
        self,
        cli_arg: str | None = None,
        env_var: str | None = None,
        config_path: Path | None = None,
    ) -> PolicyProfile:
        """Resolve profile with fallback hierarchy.

        Priority (highest to lowest):
          1. cli_arg (--profile name)
          2. env_var (OSP_PROFILE)
          3. config_path (~/.claude/one-shot.policy.yml)
          4. defaults (dev)

        Args:
            cli_arg: Profile name from CLI argument
            env_var: Profile name from environment variable
            config_path: Path to policy config file

        Returns:
            Resolved PolicyProfile
        """
        # First, load from config file (if available)
        self.load_from_file(config_path)

        # Resolve hierarchy
        profile_name = cli_arg or env_var or "dev"

        profile = self.engine.load_profile(profile_name)
        return profile

    def get_all_profiles(self) -> Dict[str, PolicyProfile]:
        """Get all registered profiles (defaults + loaded)."""
        return self.engine.profiles.copy()

    def validate_profile(self, profile: PolicyProfile) -> List[str]:
        """Validate profile for consistency. Returns list of warnings."""
        warnings = []

        # Check autonomy level
        valid_autonomy = {"none", "low", "high"}
        if profile.autonomy not in valid_autonomy:
            warnings.append(
                f"Invalid autonomy level: {profile.autonomy}. "
                f"Must be one of {valid_autonomy}."
            )

        # Check roles
        valid_roles = {"architect", "implementer", "test-author", "reviewer", "critic", "wirer"}
        for role in profile.roles:
            if role not in valid_roles:
                warnings.append(
                    f"Invalid role: {role}. Must be one of {valid_roles}."
                )

        # Check budget consistency
        if profile.budgets.cost_per_generation is not None:
            if profile.budgets.cost_per_generation < 0:
                warnings.append(
                    f"cost_per_generation must be non-negative, got "
                    f"{profile.budgets.cost_per_generation}"
                )

        if profile.budgets.cost_per_month is not None:
            if profile.budgets.cost_per_month < 0:
                warnings.append(
                    f"cost_per_month must be non-negative, got "
                    f"{profile.budgets.cost_per_month}"
                )

        # Check autonomy vs roles consistency
        if profile.autonomy == "none" and len(profile.roles) > 1:
            warnings.append(
                f"Autonomy 'none' typically implies no generation (reviewer-only). "
                f"Profile has {len(profile.roles)} roles: {profile.roles}."
            )

        return warnings
