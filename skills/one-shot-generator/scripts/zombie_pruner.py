#!/usr/bin/env python3
"""
Zombie Code Pruner — v1.0.0  (Day-2 maintenance for /one-shot generations)

Multi-agent generations leave artifacts behind when users iterate. They
rename entities mid-development, change their mind about a structure,
or re-run /one-shot with a tweaked spec. The old files don't get
cleaned up automatically — they linger as "zombie code" with broken
import chains.

This tool finds + (optionally) deletes them. It builds the LIVE import
graph from the project's entrypoint(s) and flags any file that:

  - lives inside a feature directory (e.g. cart/, line_item/, discount/)
  - has zero incoming imports from anything reachable from main.py
  - is not itself a test file (tests are run by name; not graph-reachable)
  - is not a known framework convention file (__init__.py, manage.py, etc.)

The tool NEVER deletes by default. Default behaviour is to flag + print
a report. `--delete` actually removes the files (but stages them as a
separate git commit so the change is reviewable + reversible).

CLI:
    zombie_pruner.py scan --project <dir> [--entry main.py]
    zombie_pruner.py scan --project <dir> --json
    zombie_pruner.py delete --project <dir> --paths a.py b.py [--git-commit]

Exit codes:
    0  scan ran (verdict in output)
    1  bad args
    2  --strict + zombies found
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
              ".tmp", ".pytest_cache", ".mypy_cache", "dist", "build",
              "vendor", ".idea", ".vscode", ".osp", ".archive"}

# Files that are reachable by convention even without an import chain
KEEP_BY_CONVENTION = {
    "__init__.py", "manage.py", "wsgi.py", "asgi.py", "main.py",
    "app.py", "conftest.py", "setup.py", "settings.py",
    "alembic.ini", "package.json", "tsconfig.json", "go.mod",
}

# Path patterns that are reachable by convention (Django apps, Alembic, etc.)
KEEP_PATTERNS = [
    re.compile(r"alembic/versions/.*\.py$"),
    re.compile(r"migrations/[0-9].*\.py$"),
    re.compile(r"templates/.*"),
    re.compile(r"static/.*"),
]


@dataclass
class Zombie:
    path: str
    file_kind: str             # router / models / schemas / service / etc.
    reason: str                # WHY it's zombie
    safe_to_delete: bool       # heuristic
    line_count: int

    def to_dict(self) -> Dict:
        return asdict(self)


# ─── Entry-point detection ────────────────────────────────────────────────

_DEFAULT_ENTRIES = ["main.py", "app.py", "manage.py", "src/main.py",
                     "src/app.py", "cmd/server/main.go",
                     "src/main.ts", "src/main.js"]


def _find_entry_points(project: Path,
                        user_entries: Optional[List[str]] = None) -> List[Path]:
    if user_entries:
        return [project / e for e in user_entries
                 if (project / e).exists()]
    out: List[Path] = []
    for cand in _DEFAULT_ENTRIES:
        p = project / cand
        if p.exists():
            out.append(p)
    return out


# ─── Import graph traversal ───────────────────────────────────────────────

_PY_IMPORT = re.compile(
    r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.,\s]+))",
    re.M,
)
_TS_IMPORT = re.compile(r"""(?:import|require)\s*[(]?\s*['"]([^'"]+)['"]""")


_PY_FROM_IMPORT = re.compile(
    r"^\s*from\s+([\w.]+)\s+import\s+([\w, ]+)", re.M)


def _file_imports(path: Path) -> Set[str]:
    """Return both the imported MODULE paths AND the symbols imported
    from them. `from cart import router` produces both `cart` AND
    `cart.router` so we can resolve to either `cart/__init__.py` or
    `cart/router.py`."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    out: Set[str] = set()
    if path.suffix == ".py":
        # plain `import x, y, z` form
        for m in _PY_IMPORT.finditer(text):
            mod = m.group(1) or m.group(2) or ""
            for piece in mod.split(","):
                token = piece.strip().split(" as ")[0].strip()
                if token:
                    out.add(token)
        # `from X import Y, Z` — add `X.Y` and `X.Z` as candidates too,
        # since Y may be a submodule (e.g. `from cart import router`
        # could mean cart/router.py, not just cart/).
        for m in _PY_FROM_IMPORT.finditer(text):
            base = m.group(1).strip()
            symbols = m.group(2)
            for sym in symbols.split(","):
                name = sym.strip().split(" as ")[0].strip()
                if name and name != "*":
                    out.add(f"{base}.{name}")
    elif path.suffix in (".js", ".ts", ".jsx", ".tsx"):
        for m in _TS_IMPORT.finditer(text):
            out.add(m.group(1))
    return out


def _iter_source_files(project: Path) -> List[Path]:
    out: List[Path] = []
    for p in project.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix in (".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java"):
            out.append(p)
    return out


def _module_to_path(project: Path, mod: str) -> Optional[Path]:
    """Best-effort: convert dotted-import to a file path inside the project."""
    # Try as a Python module
    p = mod.replace(".", "/")
    candidates = [project / f"{p}.py", project / p / "__init__.py"]
    # JS relative-style
    if mod.startswith("."):
        candidates.append(project / mod.lstrip("."))
    for c in candidates:
        if c.exists():
            return c
    return None


def _reachable_files(project: Path, entries: List[Path]) -> Set[Path]:
    """BFS from entries; resolve each imported module to a project file."""
    reachable: Set[Path] = set(entries)
    frontier = list(entries)
    while frontier:
        current = frontier.pop()
        for mod in _file_imports(current):
            target = _module_to_path(project, mod)
            if target and target not in reachable:
                reachable.add(target)
                frontier.append(target)
    return reachable


# ─── Zombie classification ────────────────────────────────────────────────

def _is_test_file(path: Path) -> bool:
    name = path.name.lower()
    if name.startswith("test_") or name.endswith("_test.py"):
        return True
    if "tests" in path.parts or "test" in path.parts:
        return True
    if name.endswith(".test.ts") or name.endswith(".spec.ts"):
        return True
    return False


def _is_kept_by_convention(project: Path, path: Path) -> bool:
    if path.name in KEEP_BY_CONVENTION:
        return True
    try:
        rel = str(path.relative_to(project)).replace("\\", "/")
    except ValueError:
        return False
    return any(p.search(rel) for p in KEEP_PATTERNS)


def _classify_kind(path: Path) -> str:
    name = path.name
    if name in ("models.py", "model.py"):
        return "model"
    if name == "schemas.py":
        return "schema"
    if name in ("router.py", "views.py", "controllers.py"):
        return "router"
    if name in ("service.py", "services.py"):
        return "service"
    if name == "admin.py":
        return "admin"
    if name == "urls.py":
        return "urls"
    if name == "apps.py":
        return "appconfig"
    if name.endswith(".controller.ts") or name.endswith(".controller.js"):
        return "router"
    if name.endswith(".service.ts") or name.endswith(".service.js"):
        return "service"
    if name.endswith(".entity.ts"):
        return "model"
    return "other"


def _line_count(path: Path) -> int:
    try:
        return sum(1 for _ in path.read_text(encoding="utf-8",
                                              errors="replace").splitlines())
    except OSError:
        return 0


def find_zombies(project: Path, user_entries: Optional[List[str]] = None
                  ) -> Dict:
    entries = _find_entry_points(project, user_entries)
    if not entries:
        return {
            "verdict": "SKIPPED",
            "reason": "no entry points found",
            "zombies": [],
            "scanned_files": 0,
            "reachable_files": 0,
        }
    reachable = _reachable_files(project, entries)
    all_files = _iter_source_files(project)

    zombies: List[Zombie] = []
    for p in all_files:
        if p in reachable:
            continue
        if _is_test_file(p):
            continue
        if _is_kept_by_convention(project, p):
            continue
        # Restrict zombie detection to FEATURE-shaped directories:
        # a file is only zombie-suspect if it lives in a single-segment
        # directory containing typical /one-shot artifacts (models.py,
        # router.py, schemas.py, service.py, entity.ts, ...). This avoids
        # false-positives on user-written utility modules.
        parent_dir = p.parent
        sibling_names = {f.name for f in parent_dir.iterdir() if f.is_file()}
        feature_siblings = sibling_names & {
            "models.py", "schemas.py", "router.py", "service.py",
            "services.py", "views.py", "admin.py", "urls.py",
        }
        if not feature_siblings:
            continue   # not a /one-shot feature directory

        zombies.append(Zombie(
            path=str(p.relative_to(project)),
            file_kind=_classify_kind(p),
            reason="zero incoming imports + lives in a generated feature dir",
            safe_to_delete=True,
            line_count=_line_count(p),
        ))

    return {
        "verdict": "ZOMBIES_FOUND" if zombies else "CLEAN",
        "project": str(project),
        "entry_points": [str(e.relative_to(project)) for e in entries],
        "scanned_files": len(all_files),
        "reachable_files": len(reachable),
        "zombies": [z.to_dict() for z in zombies],
    }


# ─── Delete (optional) ────────────────────────────────────────────────────

def delete_zombies(project: Path, paths: List[str],
                    git_commit: bool = False) -> Dict:
    deleted: List[str] = []
    failed: List[Dict] = []
    for rel in paths:
        target = project / rel
        if not target.exists():
            failed.append({"path": rel, "reason": "not_found"})
            continue
        try:
            target.unlink()
            deleted.append(rel)
        except OSError as e:
            failed.append({"path": rel, "reason": f"unlink_failed: {e}"})

    commit_sha = None
    if git_commit and deleted:
        try:
            subprocess.run(["git", "add", "-A"], cwd=str(project),
                            check=True, capture_output=True)
            msg = (f"chore: prune {len(deleted)} zombie file(s) "
                    f"(zombie_pruner.py)\n\n"
                    f"Files removed:\n"
                    + "\n".join(f"  - {p}" for p in deleted))
            subprocess.run(["git", "commit", "-m", msg], cwd=str(project),
                            check=True, capture_output=True)
            r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(project),
                                 capture_output=True, text=True)
            commit_sha = r.stdout.strip() if r.returncode == 0 else None
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            # git not available or commit failed — keep the deletes but
            # warn that nothing got committed
            return {"deleted": deleted, "failed": failed,
                     "git_committed": False,
                     "git_error": str(e)[:200]}

    return {"deleted": deleted, "failed": failed,
             "git_committed": bool(commit_sha), "commit_sha": commit_sha}


# ─── CLI ───────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Find files inside generated feature dirs that have "
                    "zero incoming imports — 'zombie code' from past "
                    "/one-shot iterations the user forgot to clean up."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_s = sub.add_parser("scan", help="Find zombies (no deletes)")
    p_s.add_argument("--project", required=True, type=Path)
    p_s.add_argument("--entry", action="append", default=None,
                     help="Override default entry points (main.py, app.py, …)")
    p_s.add_argument("--json", action="store_true")
    p_s.add_argument("--strict", action="store_true",
                     help="Exit 2 if any zombies found")

    p_d = sub.add_parser("delete",
                          help="Delete the listed zombie files")
    p_d.add_argument("--project", required=True, type=Path)
    p_d.add_argument("--paths", nargs="+", required=True,
                     help="Project-relative paths to delete")
    p_d.add_argument("--git-commit", action="store_true",
                     help="Stage + commit the deletes (isolated commit)")
    p_d.add_argument("--json", action="store_true")

    args = p.parse_args(argv if argv is not None else sys.argv[1:])
    project = args.project.resolve()
    if not project.exists():
        print(f"project not found: {project}", file=sys.stderr)
        return 1

    if args.cmd == "scan":
        result = find_zombies(project, args.entry)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"ZOMBIE SCAN — {result['verdict']}")
            print(f"  project:         {result['project']}")
            print(f"  entry_points:    {result.get('entry_points', [])}")
            print(f"  scanned files:   {result['scanned_files']}")
            print(f"  reachable files: {result['reachable_files']}")
            print(f"  zombies:         {len(result['zombies'])}")
            print()
            for z in result["zombies"]:
                print(f"  [{z['file_kind']:8}] {z['path']:50} "
                      f"({z['line_count']} LOC)")
        if args.strict and result["zombies"]:
            return 2
        return 0

    if args.cmd == "delete":
        result = delete_zombies(project, args.paths, args.git_commit)
        print(json.dumps(result, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
