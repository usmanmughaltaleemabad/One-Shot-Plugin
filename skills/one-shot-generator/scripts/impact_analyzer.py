#!/usr/bin/env python3
"""
Impact Analyzer — v1.0.0  (companion to legacy_guard.py for Risk #2)

Before /one-shot touches a single file in a large legacy codebase,
this script answers: **what else depends on what you're about to
change?** It builds a static import graph (Python AST + JS/TS regex)
and reports:

  - DIRECT IMPORTERS: files that import any of the target modules
  - TRANSITIVE FAN-OUT: files that import the direct importers
  - HEAT METRICS:
      - imports_in_count   (how many files import this module)
      - lines_count        (size of the file — proxy for blast radius)
      - test_coverage_proxy (count of test files mentioning the module)
      - last_modified_days (recently-changed = riskier to touch)

If the heat score is HIGH, /one-shot --legacy-safe refuses to mutate
the file automatically; it emits a runbook instead.

This is NOT a perfect call graph — that would need a full LSP / language
server. It's a fast first-line risk assessment good enough to flag
"this module is imported by 200 files, don't auto-mutate it."

CLI:
    impact_analyzer.py --project <dir> --targets a/b.py x/y/z.py
    impact_analyzer.py --project <dir> --targets ... --json
    impact_analyzer.py --project <dir> --targets ... --max-importers 50

Exit codes:
    0  analysis ran (read the verdict to act on it)
    1  bad args / project missing
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
              ".tmp", ".pytest_cache", ".mypy_cache", "dist", "build",
              "vendor", ".idea", ".vscode"}


@dataclass
class ImpactReport:
    target: str
    direct_importers: List[str]
    direct_importer_count: int
    transitive_fanout_count: int
    lines_count: int
    test_coverage_proxy: int
    last_modified_days: int
    heat_score: int           # 0-100; higher = riskier
    heat_verdict: str         # COOL | WARM | HOT | DO_NOT_TOUCH

    def to_dict(self) -> Dict:
        return asdict(self)


# ─── Python: AST-light module → file map ──────────────────────────────────

def _path_to_module(project: Path, path: Path) -> Optional[str]:
    """Convert project/foo/bar/baz.py -> foo.bar.baz (best-effort)."""
    try:
        rel = path.relative_to(project)
    except ValueError:
        return None
    parts = list(rel.parts)
    if not parts or not parts[-1].endswith(".py"):
        return None
    parts[-1] = parts[-1][:-3]  # strip .py
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts) if parts else None


_PY_IMPORT = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.,\s]+))",
                         re.M)
_TS_IMPORT = re.compile(r"""(?:import|require)\s*[(]?\s*['"]([^'"]+)['"]""")


def _scan_file_imports(path: Path) -> Set[str]:
    """Return set of bare imported modules (Python dotted paths or JS
    relative/package paths). Best-effort, no error on parse failure."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    out: Set[str] = set()
    suffix = path.suffix.lower()
    if suffix == ".py":
        for m in _PY_IMPORT.finditer(text):
            mod = m.group(1) or m.group(2) or ""
            # Handle `import a, b, c` — take each
            for piece in mod.split(","):
                token = piece.strip().split(" as ")[0].strip()
                if token:
                    out.add(token)
    elif suffix in (".js", ".ts", ".jsx", ".tsx"):
        for m in _TS_IMPORT.finditer(text):
            out.add(m.group(1))
    return out


def _iter_source_files(project: Path) -> List[Path]:
    out: List[Path] = []
    exts = {".py", ".js", ".ts", ".jsx", ".tsx"}
    for p in project.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in exts:
            out.append(p)
    return out


# ─── Impact computation ───────────────────────────────────────────────────

def _build_reverse_import_index(project: Path) -> Dict[str, List[Path]]:
    """{imported_module: [files that import it]}. Approximate; module
    keys are the bare path strings found in source — matching is
    substring-based for resilience."""
    out: Dict[str, List[Path]] = defaultdict(list)
    for src in _iter_source_files(project):
        for mod in _scan_file_imports(src):
            out[mod].append(src)
    return out


def _file_lines_count(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    return sum(1 for line in text.splitlines() if line.strip())


def _last_modified_days(path: Path) -> int:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return 365
    return int((time.time() - mtime) / 86400)


def _matches_target(imported_mod: str, target_module_candidates: Set[str]) -> bool:
    """The reverse index has tokens like 'foo.bar' / '.bar' / 'foo'.
    Match any of: exact, suffix, contained."""
    for cand in target_module_candidates:
        if imported_mod == cand:
            return True
        if imported_mod.endswith("." + cand):
            return True
        if "." + cand in imported_mod:
            return True
    return False


def _target_module_candidates(project: Path, target: Path) -> Set[str]:
    """Different import styles by which the target might be referenced."""
    mod = _path_to_module(project, target)
    out: Set[str] = set()
    if mod:
        out.add(mod)
        # 'foo.bar.baz' should match 'bar.baz', '.baz', 'baz'
        parts = mod.split(".")
        for i in range(len(parts)):
            out.add(".".join(parts[i:]))
        out.add(parts[-1])
    # JS/TS relative imports — use the stem
    out.add(target.stem)
    return {c for c in out if c}


def _heat_score(direct: int, transitive: int, lines: int,
                 test_coverage: int, days_since_mod: int) -> int:
    """0-100. Higher = riskier to auto-mutate."""
    score = 0
    # Direct importers — most weight
    if direct >= 100:
        score += 50
    elif direct >= 50:
        score += 35
    elif direct >= 20:
        score += 20
    elif direct >= 5:
        score += 10
    # Transitive fan-out — moderate
    if transitive >= 200:
        score += 25
    elif transitive >= 100:
        score += 15
    elif transitive >= 30:
        score += 8
    # File size — proxy for complexity
    if lines >= 1000:
        score += 15
    elif lines >= 300:
        score += 8
    elif lines >= 100:
        score += 3
    # Test coverage acts as RISK MITIGATION, not amplifier
    if test_coverage == 0 and direct >= 5:
        score += 10   # high-fanout file with no tests = scary
    # Recent change indicates active development → may be touched again,
    # but also indicates the team knows it — net-neutral; small bump
    if days_since_mod < 7:
        score += 2
    return min(score, 100)


def _heat_verdict(score: int) -> str:
    if score >= 70:
        return "DO_NOT_TOUCH"
    if score >= 40:
        return "HOT"
    if score >= 15:
        return "WARM"
    return "COOL"


def analyze(project: Path, targets: List[Path], *,
            max_importers: int = 50) -> Dict:
    reverse_idx = _build_reverse_import_index(project)
    reports: List[ImpactReport] = []
    for target in targets:
        if not target.exists():
            reports.append(ImpactReport(
                target=str(target), direct_importers=[],
                direct_importer_count=0, transitive_fanout_count=0,
                lines_count=0, test_coverage_proxy=0,
                last_modified_days=999,
                heat_score=0, heat_verdict="MISSING",
            ))
            continue
        candidates = _target_module_candidates(project, target)
        direct: Set[Path] = set()
        for mod, files in reverse_idx.items():
            if _matches_target(mod, candidates):
                direct.update(files)
        # Strip the target itself from importer set
        direct.discard(target)
        # Transitive — one more hop
        transitive: Set[Path] = set()
        for d in direct:
            d_candidates = _target_module_candidates(project, d)
            for mod, files in reverse_idx.items():
                if _matches_target(mod, d_candidates):
                    transitive.update(files)
        transitive -= direct
        transitive.discard(target)
        # Test coverage proxy
        test_cov = sum(1 for d in direct
                        if "test" in d.name.lower()
                        or "tests" in d.parts)
        # Stable string list of importers (trimmed)
        direct_strs = sorted(str(p.relative_to(project)) for p in direct)
        lines = _file_lines_count(target)
        days = _last_modified_days(target)
        score = _heat_score(len(direct), len(transitive),
                              lines, test_cov, days)
        reports.append(ImpactReport(
            target=str(target.relative_to(project)),
            direct_importers=direct_strs[:max_importers],
            direct_importer_count=len(direct),
            transitive_fanout_count=len(transitive),
            lines_count=lines,
            test_coverage_proxy=test_cov,
            last_modified_days=days,
            heat_score=score,
            heat_verdict=_heat_verdict(score),
        ))

    hot_count = sum(1 for r in reports
                     if r.heat_verdict in ("HOT", "DO_NOT_TOUCH"))
    return {
        "project": str(project),
        "targets_analyzed": len(targets),
        "hot_or_do_not_touch_count": hot_count,
        "reports": [r.to_dict() for r in reports],
    }


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Static-import impact analysis: what depends on the "
                    "files you're about to change?"
    )
    p.add_argument("--project", required=True, type=Path)
    p.add_argument("--targets", nargs="+", required=True, type=Path,
                   help="Paths to files /one-shot is about to modify")
    p.add_argument("--max-importers", type=int, default=50,
                   help="Cap on importer list per target (display only)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.project.exists():
        print(f"project not found: {args.project}", file=sys.stderr)
        return 1
    project = args.project.resolve()
    # Resolve targets relative to project
    targets = [project / t if not t.is_absolute() else t
                for t in args.targets]

    result = analyze(project, targets, max_importers=args.max_importers)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"IMPACT ANALYSIS — {result['project']}")
        print(f"  targets:   {result['targets_analyzed']}")
        print(f"  HOT/DO_NOT_TOUCH:  {result['hot_or_do_not_touch_count']}")
        print()
        for r in result["reports"]:
            print(f"  [{r['heat_verdict']:14}] score={r['heat_score']:3}  {r['target']}")
            print(f"     direct_importers: {r['direct_importer_count']:>4}    "
                  f"transitive_fanout: {r['transitive_fanout_count']:>4}    "
                  f"lines: {r['lines_count']:>4}    "
                  f"test_coverage: {r['test_coverage_proxy']:>2}    "
                  f"last_modified: {r['last_modified_days']}d")
    return 0


if __name__ == "__main__":
    sys.exit(main())
