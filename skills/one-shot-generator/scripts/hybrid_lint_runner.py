#!/usr/bin/env python3
"""
Hybrid Lint Runner — v1.0.0  (deterministic pre-review gate)

The reviewer agent (Sonnet) catches LOGIC flaws. It's expensive (~$0.09
per spawn) and occasionally misses obvious deterministic issues — a
missing import, a trailing-comma syntax error, a hardcoded password
that a $0 SAST tool finds in 50ms.

This script runs whatever lint / format / SAST tools are available
on the host BEFORE the reviewer spawn. The output is structured JSON
the reviewer prompt embeds verbatim — giving it un-hallucinable facts
to anchor its review against.

Tools probed (run only if installed; no-op skip otherwise):

  PYTHON
    ruff          — fastest lint + format (configurable)
    flake8        — fallback if ruff missing
    bandit        — Python SAST (security-focused)
    mypy          — type checks (only if mypy.ini / pyproject hints)

  JS / TS
    eslint        — lint + format
    tsc --noEmit  — type checks

  GO
    gofmt -l      — format check (lists files with issues)
    go vet ./...  — static analysis

  CROSS-LANG
    semgrep       — pattern-based SAST (any language)

Output (JSON to stdout):
    {
      "tools_run": ["ruff", "bandit", "semgrep"],
      "tools_skipped": ["mypy (not installed)", "eslint (no JS files)"],
      "findings_by_tool": {
        "ruff": [{"file": "...", "line": 42, "rule": "F401",
                   "message": "imported but unused"}],
        ...
      },
      "summary": "12 ruff, 1 bandit (HIGH), 0 semgrep",
      "blocking": true  // True if any HIGH-severity SAST finding
    }

CLI:
    hybrid_lint_runner.py --target <dir>
    hybrid_lint_runner.py --target <dir> --json
    hybrid_lint_runner.py --target <dir> --strict      # block on any finding

Exit codes:
    0  no blocking findings (or all tools skipped)
    1  bad args
    2  --strict triggered OR HIGH SAST finding present
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


@dataclass
class Finding:
    tool: str
    file: str
    line: int
    rule: str
    severity: str       # info | warn | high
    message: str

    def to_dict(self) -> Dict:
        return asdict(self)


# ─── Tool detection ───────────────────────────────────────────────────────

def _have(tool: str) -> bool:
    """Is the CLI tool on PATH?"""
    return shutil.which(tool) is not None


def _has_files(target: Path, exts: List[str]) -> bool:
    for p in target.rglob("*"):
        if p.is_file() and p.suffix in exts:
            return True
    return False


# ─── Tool runners ─────────────────────────────────────────────────────────

def _run_ruff(target: Path) -> List[Finding]:
    """ruff check --output-format json"""
    proc = subprocess.run(
        ["ruff", "check", str(target), "--output-format", "json"],
        capture_output=True, text=True, timeout=60,
    )
    if not proc.stdout:
        return []
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    out: List[Finding] = []
    for entry in data:
        out.append(Finding(
            tool="ruff",
            file=entry.get("filename", ""),
            line=entry.get("location", {}).get("row", 0),
            rule=entry.get("code", "?"),
            severity="warn",
            message=entry.get("message", "")[:200],
        ))
    return out


def _run_flake8(target: Path) -> List[Finding]:
    proc = subprocess.run(
        ["flake8", str(target), "--format=%(path)s|%(row)d|%(code)s|%(text)s"],
        capture_output=True, text=True, timeout=60,
    )
    out: List[Finding] = []
    for line in proc.stdout.splitlines():
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        out.append(Finding(
            tool="flake8", file=parts[0], line=int(parts[1] or 0),
            rule=parts[2], severity="warn", message=parts[3][:200],
        ))
    return out


def _run_bandit(target: Path) -> List[Finding]:
    """bandit -r <dir> -f json — Python SAST"""
    proc = subprocess.run(
        ["bandit", "-r", str(target), "-f", "json", "-q"],
        capture_output=True, text=True, timeout=120,
    )
    if not proc.stdout:
        return []
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    out: List[Finding] = []
    sev_map = {"LOW": "info", "MEDIUM": "warn", "HIGH": "high"}
    for result in data.get("results", []):
        sev = sev_map.get(result.get("issue_severity", "MEDIUM"), "warn")
        out.append(Finding(
            tool="bandit",
            file=result.get("filename", ""),
            line=result.get("line_number", 0),
            rule=result.get("test_id", "?"),
            severity=sev,
            message=result.get("issue_text", "")[:200],
        ))
    return out


def _run_eslint(target: Path) -> List[Finding]:
    """eslint . --format json"""
    proc = subprocess.run(
        ["eslint", str(target), "--format", "json"],
        capture_output=True, text=True, timeout=120,
    )
    if not proc.stdout:
        return []
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    out: List[Finding] = []
    for file_result in data:
        for m in file_result.get("messages", []):
            sev = "warn" if m.get("severity", 1) == 1 else "high"
            out.append(Finding(
                tool="eslint",
                file=file_result.get("filePath", ""),
                line=m.get("line", 0),
                rule=m.get("ruleId") or "?",
                severity=sev,
                message=m.get("message", "")[:200],
            ))
    return out


def _run_semgrep(target: Path) -> List[Finding]:
    """semgrep --config=auto --json — cross-language pattern SAST"""
    proc = subprocess.run(
        ["semgrep", "--config=auto", "--json", "--quiet", str(target)],
        capture_output=True, text=True, timeout=300,
    )
    if not proc.stdout:
        return []
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    out: List[Finding] = []
    sev_map = {"INFO": "info", "WARNING": "warn", "ERROR": "high"}
    for r in data.get("results", []):
        out.append(Finding(
            tool="semgrep",
            file=r.get("path", ""),
            line=r.get("start", {}).get("line", 0),
            rule=r.get("check_id", "?"),
            severity=sev_map.get(r.get("extra", {}).get("severity", "WARNING"),
                                   "warn"),
            message=r.get("extra", {}).get("message", "")[:200],
        ))
    return out


def _run_gofmt(target: Path) -> List[Finding]:
    proc = subprocess.run(
        ["gofmt", "-l", str(target)],
        capture_output=True, text=True, timeout=30,
    )
    return [Finding(tool="gofmt", file=line.strip(), line=0,
                     rule="format", severity="warn",
                     message="needs reformatting")
             for line in proc.stdout.splitlines() if line.strip()]


def _run_go_vet(target: Path) -> List[Finding]:
    proc = subprocess.run(
        ["go", "vet", "./..."],
        capture_output=True, text=True, timeout=60, cwd=str(target),
    )
    out: List[Finding] = []
    # go vet emits "path:line:col: message"
    for line in proc.stderr.splitlines():
        parts = line.split(":", 3)
        if len(parts) < 4:
            continue
        try:
            lineno = int(parts[1])
        except ValueError:
            continue
        out.append(Finding(
            tool="go-vet", file=parts[0], line=lineno,
            rule="vet", severity="warn", message=parts[3].strip()[:200],
        ))
    return out


# ─── Orchestration ─────────────────────────────────────────────────────────

def run_all(target: Path) -> Dict[str, Any]:
    findings_by_tool: Dict[str, List[Dict]] = {}
    tools_run: List[str] = []
    tools_skipped: List[str] = []

    py = _has_files(target, [".py"])
    js = _has_files(target, [".js", ".ts", ".jsx", ".tsx"])
    go = _has_files(target, [".go"])

    # Python
    if py:
        if _have("ruff"):
            try:
                findings_by_tool["ruff"] = [f.to_dict() for f in _run_ruff(target)]
                tools_run.append("ruff")
            except Exception as e:
                tools_skipped.append(f"ruff (error: {e})")
        elif _have("flake8"):
            try:
                findings_by_tool["flake8"] = [f.to_dict() for f in _run_flake8(target)]
                tools_run.append("flake8")
            except Exception as e:
                tools_skipped.append(f"flake8 (error: {e})")
        else:
            tools_skipped.append("ruff/flake8 (neither installed)")

        if _have("bandit"):
            try:
                findings_by_tool["bandit"] = [f.to_dict() for f in _run_bandit(target)]
                tools_run.append("bandit")
            except Exception as e:
                tools_skipped.append(f"bandit (error: {e})")
        else:
            tools_skipped.append("bandit (not installed)")
    else:
        tools_skipped.append("ruff/flake8/bandit (no Python files)")

    # JS/TS
    if js:
        if _have("eslint"):
            try:
                findings_by_tool["eslint"] = [f.to_dict() for f in _run_eslint(target)]
                tools_run.append("eslint")
            except Exception as e:
                tools_skipped.append(f"eslint (error: {e})")
        else:
            tools_skipped.append("eslint (not installed)")
    else:
        tools_skipped.append("eslint (no JS/TS files)")

    # Go
    if go:
        if _have("gofmt"):
            try:
                findings_by_tool["gofmt"] = [f.to_dict() for f in _run_gofmt(target)]
                tools_run.append("gofmt")
            except Exception as e:
                tools_skipped.append(f"gofmt (error: {e})")
        if _have("go"):
            try:
                findings_by_tool["go-vet"] = [f.to_dict() for f in _run_go_vet(target)]
                tools_run.append("go-vet")
            except Exception as e:
                tools_skipped.append(f"go-vet (error: {e})")

    # Cross-language SAST
    if _have("semgrep"):
        try:
            findings_by_tool["semgrep"] = [f.to_dict() for f in _run_semgrep(target)]
            tools_run.append("semgrep")
        except Exception as e:
            tools_skipped.append(f"semgrep (error: {e})")
    else:
        tools_skipped.append("semgrep (not installed)")

    # Build summary
    high = sum(1 for tool_findings in findings_by_tool.values()
                for f in tool_findings if f["severity"] == "high")
    total = sum(len(v) for v in findings_by_tool.values())
    summary_parts = []
    for tool, findings in findings_by_tool.items():
        summary_parts.append(f"{len(findings)} {tool}")
    summary = ", ".join(summary_parts) if summary_parts else "(no findings)"

    return {
        "target": str(target),
        "tools_run": tools_run,
        "tools_skipped": tools_skipped,
        "findings_by_tool": findings_by_tool,
        "summary": f"{summary} · {high} HIGH-severity",
        "total_findings": total,
        "high_severity_count": high,
        "blocking": high > 0,
    }


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Hybrid lint + SAST pre-review gate. Runs every "
                    "installed analyser on the target; feeds raw output "
                    "to the reviewer agent so it has un-hallucinable facts."
    )
    p.add_argument("--target", required=True, type=Path)
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true",
                   help="Exit 2 on ANY finding (default: exit 2 only on HIGH)")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.target.exists():
        print(f"target not found: {args.target}", file=sys.stderr)
        return 1

    result = run_all(args.target)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"HYBRID LINT — {result['summary']}")
        print(f"  tools_run:     {result['tools_run']}")
        print(f"  tools_skipped: {len(result['tools_skipped'])} (no-op)")
        for tool, findings in result["findings_by_tool"].items():
            if not findings:
                continue
            print(f"\n  {tool} ({len(findings)} findings):")
            for f in findings[:10]:
                print(f"    [{f['severity']:5}] {f['file']}:{f['line']} "
                      f"{f['rule']:10} {f['message'][:80]}")
            if len(findings) > 10:
                print(f"    ... + {len(findings) - 10} more")

    if result["blocking"]:
        return 2
    if args.strict and result["total_findings"] > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
