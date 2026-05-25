#!/usr/bin/env python3
"""
Bump the plugin version in .claude-plugin/plugin.json and sync
.claude-plugin/marketplace.json SHA to the current HEAD.

Usage:
    python scripts/bump_version.py patch   # 1.2.2 -> 1.2.3
    python scripts/bump_version.py minor   # 1.2.2 -> 1.3.0
    python scripts/bump_version.py major   # 1.2.2 -> 2.0.0
    python scripts/bump_version.py <full>  # e.g. "1.5.0" to set explicitly

Also reads bump type from last commit message using conventional commits:
    feat:           -> minor
    BREAKING CHANGE -> major
    anything else   -> patch

Returns the new version string on stdout.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PLUGIN_JSON   = Path(".claude-plugin/plugin.json")
MARKETPLACE_JSON = Path(".claude-plugin/marketplace.json")


def current_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"],
                                   text=True).strip()


def bump(version: str, kind: str) -> str:
    major, minor, patch = (int(x) for x in version.split("."))
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    if kind == "patch":
        return f"{major}.{minor}.{patch + 1}"
    # explicit version string passed
    if re.match(r"^\d+\.\d+\.\d+$", kind):
        return kind
    raise ValueError(f"Unknown bump kind: {kind!r}")


def bump_type_from_commit() -> str:
    """Infer bump type from the most recent commit message."""
    msg = subprocess.check_output(
        ["git", "log", "-1", "--pretty=%B"], text=True
    ).strip()
    if "BREAKING CHANGE" in msg or re.search(r"^feat!|^fix!|^\w+!:", msg, re.M):
        return "major"
    if re.search(r"^feat(\(|:)", msg, re.M):
        return "minor"
    return "patch"


def main() -> None:
    kind = sys.argv[1] if len(sys.argv) > 1 else bump_type_from_commit()

    # --- plugin.json ---
    plugin = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    old_version = plugin.get("version", "0.0.0")
    new_version = bump(old_version, kind)
    plugin["version"] = new_version
    PLUGIN_JSON.write_text(json.dumps(plugin, indent=2) + "\n", encoding="utf-8")

    # --- marketplace.json ---
    sha = current_sha()
    marketplace = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    for entry in marketplace.get("plugins", []):
        if entry.get("name") == plugin.get("name"):
            src = entry.get("source", {})
            if isinstance(src, dict):
                src["sha"] = sha
            break
    MARKETPLACE_JSON.write_text(json.dumps(marketplace, indent=2) + "\n",
                                encoding="utf-8")

    print(new_version)  # consumed by the GitHub Action


if __name__ == "__main__":
    main()
