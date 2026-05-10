#!/usr/bin/env python3
"""
Integration tests for Superpowers skills.
Validates that all 5 new skills are properly wired and callable.
"""

import sys
import json
import subprocess
from pathlib import Path

# Add scripts to path
SCRIPTS_DIR = Path(__file__).parent.parent / "skills"


def test_python_scripts_exist():
    """Validate all Python scripts exist."""
    scripts = [
        "execute-plan/scripts/plan_executor.py",
        "verify-before-complete/scripts/completion_gate.py",
        "tdd-cycle/scripts/tdd_cycle_enforcer.py",
        "systematic-debug/scripts/systematic_debug.py",
        "write-plan/scripts/plan_writer.py",
    ]

    for script_path in scripts:
        full_path = SCRIPTS_DIR / script_path
        assert full_path.exists(), f"Missing: {script_path}"
        print(f"[OK] {script_path} exists")


def test_skill_md_files_exist():
    """Validate all SKILL.md files exist."""
    skills = [
        "write-plan/SKILL.md",
        "execute-plan/SKILL.md",
        "tdd-cycle/SKILL.md",
        "systematic-debug/SKILL.md",
        "verify-before-complete/SKILL.md",
    ]

    for skill_path in skills:
        full_path = SCRIPTS_DIR / skill_path
        assert full_path.exists(), f"Missing: {skill_path}"

        try:
            content = full_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = full_path.read_text(encoding='utf-8', errors='ignore')

        assert "---" in content, f"Missing frontmatter: {skill_path}"
        assert "name:" in content, f"Missing name field: {skill_path}"
        print(f"[OK] {skill_path} has valid structure")


def test_command_files_exist():
    """Validate all command files exist."""
    commands_dir = Path(__file__).parent.parent / "commands"
    commands = ["plan.md", "execute-plan.md", "tdd.md", "sys-debug.md"]

    for cmd in commands:
        cmd_file = commands_dir / cmd
        assert cmd_file.exists(), f"Missing: {cmd}"

        content = cmd_file.read_text()
        assert "/one-shot-prompting:" in content, f"Missing skill invocation: {cmd}"
        print(f"[OK] {cmd} valid")


def test_orchestrator_has_superpowers_flags():
    """Validate orchestrate_harness_modules.py has Superpowers flags."""
    orchestrator = (
        SCRIPTS_DIR / "one-shot-generator" / "scripts" / "orchestrate_harness_modules.py"
    )
    assert orchestrator.exists(), "orchestrator not found"

    content = orchestrator.read_text()
    required = ["sys_debug", "write_plan", "execute_plan", "verify_complete"]

    for flag in required:
        assert f"'{flag}'" in content, f"Flag {flag} not in orchestrator"
        print(f"[OK] Flag '{flag}' found in orchestrator")


def main():
    """Run all validation tests."""
    print("\n" + "=" * 60)
    print("SUPERPOWERS SKILLS - STRUCTURE VALIDATION")
    print("=" * 60 + "\n")

    tests = [
        ("Python Scripts", test_python_scripts_exist),
        ("SKILL.md Files", test_skill_md_files_exist),
        ("Command Files", test_command_files_exist),
        ("Orchestrator", test_orchestrator_has_superpowers_flags),
    ]

    passed = 0
    failed = 0

    for category, test_func in tests:
        print(f"\n{category}:")
        print("-" * 40)
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {str(e)}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            failed += 1

    print("\n" + "=" * 60)
    if failed == 0:
        print(f"SUCCESS: All {passed} validation checks passed")
    else:
        print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
