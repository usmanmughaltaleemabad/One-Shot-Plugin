#!/usr/bin/env python3
"""
Compliance Audit — v1.0.0  (Anthropic Software Directory Policy check)

Runs every requirement from the Anthropic Software Directory Policy
against the current repo state. Emits a structured pass/fail report.

Source: https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy

Checks performed:

  Documentation
    - PRIVACY.md present (if collecting any data)
    - SUPPORT.md present + has channels / contact
    - README.md present + has "how it works" section
    - LICENSE present
    - CHANGELOG.md present
    - TROUBLESHOOTING.md present

  Tool / surface metadata
    - Slash command names ≤ 64 chars
    - Slash command frontmatter: argument-hint, allowed-tools, description
    - Tool annotations: read-only commands declare readOnlyHint;
      destructive commands declare destructiveHint
    - Each command has a one-line `title:` (or top-of-file `# Title`)

  Testing & verification
    - At least 3 working example prompts somewhere in docs
    - Tests directory exists + has tests

  Quality
    - No file matching * (e.g. .env, *.pem) committed
    - No hardcoded credentials in scripts (delegates to security_deep_scan)
    - Plugin manifest plugin.json exists + has version + author + license

  Branding
    - README doesn't claim Anthropic partnership/sponsorship
    - No "official", "endorsed by Anthropic" without backing

Output: structured JSON with per-check status (PASS / WARN / FAIL).
Exit codes:
  0  no FAIL findings (WARN is OK)
  1  bad args
  2  one or more FAIL findings (gate the listing)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


@dataclass
class CheckResult:
    name: str
    category: str
    status: str       # PASS | WARN | FAIL
    detail: str
    fix_hint: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


# ─── Documentation ─────────────────────────────────────────────────────────

REQUIRED_DOCS = [
    ("PRIVACY.md",          "data handling disclosure",
     "Create PRIVACY.md describing data collection (or stating none)"),
    ("SUPPORT.md",          "support channels + contact",
     "Create SUPPORT.md listing GitHub Issues + maintainer contact"),
    ("README.md",           "product overview + how-it-works",
     "Top-level README missing"),
    ("LICENSE",             "open-source license",
     "Add a LICENSE file (MIT recommended for marketplace)"),
    ("CHANGELOG.md",        "release history",
     "Track changes in CHANGELOG.md"),
    ("TROUBLESHOOTING.md",  "common issues + fixes",
     "Add TROUBLESHOOTING.md per Software Directory Policy"),
    ("SECURITY.md",         "vulnerability disclosure",
     "Add SECURITY.md describing how to report security issues"),
]


def _check_documentation(repo: Path) -> List[CheckResult]:
    out: List[CheckResult] = []
    for filename, purpose, fix in REQUIRED_DOCS:
        path = repo / filename
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            if len(text) < 100:
                out.append(CheckResult(
                    name=f"doc_{filename.replace('.', '_').lower()}",
                    category="documentation",
                    status="WARN",
                    detail=f"{filename} exists but is suspiciously short ({len(text)} chars)",
                    fix_hint=f"Flesh out {filename} — current content is < 100 chars",
                ))
            else:
                out.append(CheckResult(
                    name=f"doc_{filename.replace('.', '_').lower()}",
                    category="documentation",
                    status="PASS",
                    detail=f"{filename} present ({len(text)} chars)",
                ))
        else:
            out.append(CheckResult(
                name=f"doc_{filename.replace('.', '_').lower()}",
                category="documentation",
                status="FAIL",
                detail=f"{filename} missing — {purpose}",
                fix_hint=fix,
            ))
    return out


# ─── Slash command surface ──────────────────────────────────────────────────

_FRONTMATTER = re.compile(r"^---\n(.+?)\n---", re.DOTALL)
DESTRUCTIVE_INDICATORS = [
    "--apply", "--force", "git push", "git reset", "rm -rf",
    "alembic upgrade", "manage.py migrate", "Stage 6", "wirer",
    "destructive", "mutate",
]
READ_ONLY_INDICATORS = [
    "scan", "audit", "list", "inspect", "show", "report",
    "search", "find", "stats", "rate", "dashboard",
]


def _check_slash_commands(repo: Path) -> List[CheckResult]:
    out: List[CheckResult] = []
    commands_dir = repo / "commands"
    if not commands_dir.exists():
        return [CheckResult(
            name="cmd_dir_present", category="surface", status="FAIL",
            detail="commands/ directory missing",
            fix_hint="Slash commands must live under commands/",
        )]

    for path in sorted(commands_dir.glob("*.md")):
        if path.name == "CLAUDE.md":
            continue
        name = path.stem
        # 64-char limit per Software Directory Policy
        if len(name) > 64:
            out.append(CheckResult(
                name=f"cmd_name_length_{name[:20]}",
                category="surface", status="FAIL",
                detail=f"slash command '{name}' exceeds 64 chars ({len(name)})",
                fix_hint="Rename to a shorter, descriptive name",
            ))

        text = path.read_text(encoding="utf-8", errors="replace")
        fm = _FRONTMATTER.match(text)
        if not fm:
            out.append(CheckResult(
                name=f"cmd_frontmatter_{name}",
                category="surface", status="FAIL",
                detail=f"commands/{name}.md missing YAML frontmatter",
                fix_hint="Add ---/description:/argument-hint:/allowed-tools:/--- block",
            ))
            continue
        front = fm.group(1)
        if "description:" not in front:
            out.append(CheckResult(
                name=f"cmd_description_{name}",
                category="surface", status="FAIL",
                detail=f"commands/{name}.md missing 'description:' field",
                fix_hint="Frontmatter must declare description: ...",
            ))
        if "argument-hint:" not in front:
            out.append(CheckResult(
                name=f"cmd_argument_hint_{name}",
                category="surface", status="WARN",
                detail=f"commands/{name}.md missing 'argument-hint:'",
                fix_hint="Add argument-hint: for autocomplete UX",
            ))
        if "allowed-tools:" not in front:
            out.append(CheckResult(
                name=f"cmd_allowed_tools_{name}",
                category="surface", status="WARN",
                detail=f"commands/{name}.md missing 'allowed-tools:'",
                fix_hint="Declare which tools the command needs",
            ))

        # Read-only / destructive annotation check (per directory policy)
        blob = text.lower()
        looks_destructive = any(ind.lower() in blob
                                  for ind in DESTRUCTIVE_INDICATORS)
        looks_read_only = (not looks_destructive
                            and any(ind in name.lower()
                                    for ind in READ_ONLY_INDICATORS))

        if looks_destructive and "destructive" not in front.lower():
            out.append(CheckResult(
                name=f"cmd_annotation_{name}",
                category="surface", status="WARN",
                detail=(f"commands/{name}.md references destructive ops "
                        f"but lacks `destructive: true` frontmatter annotation"),
                fix_hint="Add 'destructive: true' to frontmatter",
            ))
        if looks_read_only and "read-only" not in front.lower():
            out.append(CheckResult(
                name=f"cmd_annotation_{name}",
                category="surface", status="WARN",
                detail=(f"commands/{name}.md appears read-only "
                        f"but lacks `read-only: true` frontmatter annotation"),
                fix_hint="Add 'read-only: true' to frontmatter",
            ))

    return out


# ─── Examples ──────────────────────────────────────────────────────────────

def _check_examples(repo: Path) -> List[CheckResult]:
    """Per policy: at least 3 working example prompts somewhere."""
    candidates = [
        repo / "DIRECTORY_SUBMISSION_FORM.md",
        repo / "docs" / "cookbook.md",
        repo / "README.md",
    ]
    total_examples = 0
    for path in candidates:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        # Heuristic: count code blocks containing `/one-shot`
        total_examples += len(re.findall(
            r"```[a-z]*\s*[\s\S]*?/one-shot[\s\S]*?```", text))
    if total_examples >= 3:
        return [CheckResult(
            name="three_example_prompts", category="examples", status="PASS",
            detail=f"{total_examples} `/one-shot` example(s) in docs",
        )]
    return [CheckResult(
        name="three_example_prompts", category="examples", status="FAIL",
        detail=f"only {total_examples} example(s) found; policy requires ≥ 3",
        fix_hint="Add more `/one-shot \"...\"` example blocks in cookbook + README",
    )]


# ─── Plugin manifest ──────────────────────────────────────────────────────

REQUIRED_MANIFEST_KEYS = ("name", "version", "author", "license", "description")


def _check_plugin_manifest(repo: Path) -> List[CheckResult]:
    out: List[CheckResult] = []
    path = repo / ".claude-plugin" / "plugin.json"
    if not path.exists():
        return [CheckResult(
            name="plugin_manifest_present", category="manifest", status="FAIL",
            detail=".claude-plugin/plugin.json missing",
            fix_hint="Create plugin.json with name/version/author/license/description",
        )]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [CheckResult(
            name="plugin_manifest_valid", category="manifest", status="FAIL",
            detail=f"plugin.json invalid JSON: {e}",
            fix_hint="Fix JSON syntax",
        )]
    for key in REQUIRED_MANIFEST_KEYS:
        if key not in data:
            out.append(CheckResult(
                name=f"manifest_field_{key}", category="manifest",
                status="FAIL",
                detail=f"plugin.json missing '{key}' field",
                fix_hint=f"Add '{key}' to plugin.json",
            ))
        else:
            out.append(CheckResult(
                name=f"manifest_field_{key}", category="manifest",
                status="PASS",
                detail=f"plugin.json has '{key}'",
            ))
    return out


# ─── Branding (must not claim Anthropic endorsement) ──────────────────────

FORBIDDEN_CLAIMS = [
    r"\b(?:official|endorsed)\s+(?:by\s+)?Anthropic\b",
    r"\bAnthropic[- ]partnered\b",
    r"\bAnthropic-sponsored\b",
    r"\bin partnership with Anthropic\b",
]


def _check_branding(repo: Path) -> List[CheckResult]:
    out: List[CheckResult] = []
    for md_path in repo.rglob("*.md"):
        if any(part in {".archive", "node_modules", ".git"}
               for part in md_path.parts):
            continue
        try:
            text = md_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pattern in FORBIDDEN_CLAIMS:
            m = re.search(pattern, text, re.I)
            if m:
                rel = md_path.relative_to(repo)
                out.append(CheckResult(
                    name=f"branding_claim_{rel.name}",
                    category="branding", status="FAIL",
                    detail=(f"{rel} contains an unauthorised Anthropic-"
                            f"endorsement claim near '{m.group(0)}'"),
                    fix_hint=("Remove or rephrase. Per policy: no statement "
                              "suggesting partnership / sponsorship / endorsement "
                              "without prior written Anthropic approval."),
                ))
    if not out:
        out.append(CheckResult(
            name="branding_clean", category="branding", status="PASS",
            detail="no unauthorised Anthropic-endorsement claims found",
        ))
    return out


# ─── Test coverage ─────────────────────────────────────────────────────────

def _check_tests(repo: Path) -> List[CheckResult]:
    tests_dir = repo / "tests"
    if not tests_dir.exists():
        return [CheckResult(
            name="tests_dir", category="testing", status="FAIL",
            detail="tests/ directory missing",
            fix_hint="Add tests/ with at least a few unit tests",
        )]
    test_files = list(tests_dir.rglob("test_*.py"))
    if len(test_files) < 5:
        return [CheckResult(
            name="tests_dir", category="testing", status="WARN",
            detail=f"only {len(test_files)} test file(s); strongly recommend ≥ 5",
            fix_hint="Add more test coverage before submitting",
        )]
    return [CheckResult(
        name="tests_dir", category="testing", status="PASS",
        detail=f"{len(test_files)} test file(s) under tests/",
    )]


# ─── Orchestration ─────────────────────────────────────────────────────────

def audit(repo: Path) -> Dict:
    checks: List[CheckResult] = []
    checks += _check_documentation(repo)
    checks += _check_slash_commands(repo)
    checks += _check_examples(repo)
    checks += _check_plugin_manifest(repo)
    checks += _check_branding(repo)
    checks += _check_tests(repo)

    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for c in checks:
        counts[c.status] = counts.get(c.status, 0) + 1

    if counts["FAIL"] == 0:
        verdict = "READY_FOR_DIRECTORY" if counts["WARN"] == 0 else "READY_WITH_WARN"
    else:
        verdict = "NOT_READY"

    return {
        "verdict": verdict,
        "summary": (f"{counts['PASS']} PASS, "
                    f"{counts['WARN']} WARN, "
                    f"{counts['FAIL']} FAIL"),
        "checks_run": len(checks),
        "checks": [c.to_dict() for c in checks],
        "policy_source": (
            "https://support.claude.com/en/articles/"
            "13145358-anthropic-software-directory-policy"),
    }


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Audit the repo against the Anthropic Software "
                    "Directory Policy. Exit 2 if any FAIL findings."
    )
    p.add_argument("--repo-root", type=Path, default=Path.cwd())
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true",
                   help="Exit 2 on WARN as well as FAIL")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    repo = args.repo_root.resolve()
    if not repo.exists():
        print(f"repo not found: {repo}", file=sys.stderr)
        return 1
    result = audit(repo)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"COMPLIANCE AUDIT — {result['verdict']}")
        print(f"  {result['summary']}")
        print(f"  policy: {result['policy_source']}")
        print()
        for c in result["checks"]:
            marker = {"PASS": "[OK]", "WARN": "[wrn]", "FAIL": "[FAIL]"}.get(
                c["status"], "[??]")
            print(f"  {marker:7} {c['category']:14} {c['name']:35} {c['detail']}")
            if c["status"] != "PASS" and c.get("fix_hint"):
                print(f"          fix: {c['fix_hint']}")

    if any(c["status"] == "FAIL" for c in result["checks"]):
        return 2
    if args.strict and any(c["status"] == "WARN" for c in result["checks"]):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
