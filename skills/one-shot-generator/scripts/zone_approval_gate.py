#!/usr/bin/env python3
"""
Zone-Based Approval Gate — mandatory review between PLAN and BUILD zones.

Three zones:
  - Zone 0 (Research): Scan, extract, cost estimate — no mutations
  - Zone 1 (Plan): Architect designs spec.json — outputs for review
  - Zone 2 (Execute): Code generation + tests — assumes spec approved
  - **GATE**: Between Zone 1 and Zone 2. Spec must be approved before BUILD.

This gate enforces that the user explicitly approves the spec before
any code is generated. Bypass options:
  - `--force` (user explicitly opts out)
  - `--skip-approval` (in CI/automation, after prior approval)

Usage:

    python zone_approval_gate.py enforce \\
        --spec /tmp/osp-spec.json \\
        --arguments "<original cli arguments>" \\
        --force-bypass false

Returns JSON:
    {
      "zone": "PLAN_TO_BUILD_GATE",
      "status": "approved" | "denied" | "bypassed",
      "decision_time": "ISO8601",
      "bypass_reason": null | "force_flag" | "skip_approval_flag"
    }
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any


def enforce_zone_gate(
    spec_file: str,
    arguments: str,
    force_bypass: bool = False,
) -> dict[str, Any]:
    """
    Enforce approval gate between Zone 1 (PLAN) and Zone 2 (BUILD).

    Returns approval decision. Raises SystemExit if denied.
    """

    # Check bypass conditions
    if "--force" in arguments or "--skip-approval" in arguments:
        return {
            "zone": "PLAN_TO_BUILD_GATE",
            "status": "bypassed",
            "decision_time": datetime.now().isoformat(),
            "bypass_reason": "force_flag" if "--force" in arguments else "skip_approval_flag",
        }

    if force_bypass:
        return {
            "zone": "PLAN_TO_BUILD_GATE",
            "status": "bypassed",
            "decision_time": datetime.now().isoformat(),
            "bypass_reason": "programmatic_override",
        }

    # Enforce approval: read spec, emit summary, wait for user input
    try:
        with open(spec_file) as f:
            spec = json.load(f)
    except FileNotFoundError:
        print(f"Error: spec file not found: {spec_file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: spec file is malformed JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Emit human-readable spec summary
    print("\n" + "=" * 60)
    print("ZONE APPROVAL GATE — PLAN → BUILD TRANSITION")
    print("=" * 60)
    print(f"\nThe architect has generated a spec. Review it before code gen:")
    print("\nENTITIES:")
    for entity in spec.get("entities", []):
        print(f"  • {entity['name']} ({entity['table_name']})")
        if entity.get("fields"):
            for field in entity["fields"][:3]:  # Show first 3
                print(f"    - {field['name']}: {field['type']}")
            if len(entity["fields"]) > 3:
                print(f"    ... +{len(entity['fields']) - 3} more fields")

    print("\nRELATIONSHIPS:")
    for rel in spec.get("relationships", []):
        print(f"  • {rel['from']} ── {rel['relationship_type']} ──> {rel['to']}")

    print("\nAPI SURFACE:")
    for endpoint in spec.get("api_surface", [])[:5]:
        print(f"  • {endpoint['method']} {endpoint['path']}")
    if len(spec.get("api_surface", [])) > 5:
        print(f"  ... +{len(spec['api_surface']) - 5} more endpoints")

    print("\nProceed to code generation?")
    print("  [y]es — proceed to BUILD zone (code generation)")
    print("  [n]o  — abort this run")
    print("  [s]how — show full spec.json")

    while True:
        try:
            response = input("\nYour choice (y/n/s): ").strip().lower()
        except EOFError:
            print("(EOF — treating as 'no')", file=sys.stderr)
            response = "n"

        if response == "y":
            return {
                "zone": "PLAN_TO_BUILD_GATE",
                "status": "approved",
                "decision_time": datetime.now().isoformat(),
                "bypass_reason": None,
            }
        elif response == "n":
            print("\nAborted. The spec was not approved.", file=sys.stderr)
            sys.exit(1)
        elif response == "s":
            print("\n" + json.dumps(spec, indent=2))
            # Loop continues to re-ask
        else:
            print("Invalid response. Try again (y/n/s).")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: zone_approval_gate.py enforce --spec <file> --arguments '<args>' [--force-bypass]")
        sys.exit(1)

    if sys.argv[1] == "enforce":
        spec_file = None
        arguments = ""
        force_bypass = False

        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--spec" and i + 1 < len(sys.argv):
                spec_file = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--arguments" and i + 1 < len(sys.argv):
                arguments = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--force-bypass":
                force_bypass = True
                i += 1
            else:
                i += 1

        if not spec_file:
            print("Error: --spec is required", file=sys.stderr)
            sys.exit(1)

        result = enforce_zone_gate(spec_file, arguments, force_bypass)
        print(json.dumps(result, indent=2))
