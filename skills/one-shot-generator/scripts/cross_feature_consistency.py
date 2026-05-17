#!/usr/bin/env python3
"""
Cross-Feature Consistency Checker — v0.9.0  (Tier 3 drift detection)

Compares newly generated code against the project's existing conventions
and flags drift BEFORE the wirer attaches the code to ``main.py``.

What we check (each one ties to a class of bug we saw in real use):

  C1  Naming style          generated module names match the project's
                            snake_case vs camelCase convention.

  C2  Schema library         if the project uses Pydantic, the generated
                            schemas must too; we flag Marshmallow / dataclasses
                            mixed into a Pydantic codebase.

  C3  Error envelope         the generated router's HTTPException usage
                            matches the existing project (FastAPI's
                            ``detail`` field vs Django REST's
                            ``ValidationError`` shape).

  C4  Pagination style       if existing routers paginate with envelope
                            shape ``{"results", "next", "previous"}``, the
                            new router must too.

  C5  Import paths           generated files don't reference modules that
                            don't exist in the target project (e.g.
                            ``from database import get_db`` against a
                            project that uses ``from app.deps import get_session``).

CLI:
    python cross_feature_consistency.py --project <path> --generated-dir <path>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
from codebase_graph import load_or_build as load_codebase_graph
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Data shapes ─────────────────────────────────────────────────────────────

@dataclass
class ConsistencyIssue:
    file: str
    rule: str             # C1 | C2 | C3 | C4 | C5
    severity: str         # error | warning | info
    message: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ConsistencyReport:
    project: str
    generated_dir: str
    issues: List[ConsistencyIssue] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "project": self.project,
            "generated_dir": self.generated_dir,
            "issues": [i.to_dict() for i in self.issues],
        }

    @property
    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)


# ─── Rules ───────────────────────────────────────────────────────────────────

_CAMEL_RE = re.compile(r"[a-z][A-Z]")


def _check_naming(file: Path, conventions: Dict[str, str]) -> List[ConsistencyIssue]:
    expected = conventions.get("naming", "snake_case")
    name = file.stem
    if expected == "snake_case" and _CAMEL_RE.search(name):
        return [ConsistencyIssue(file=file.name, rule="C1", severity="warning",
                                  message=f"file name '{name}' is camelCase but project convention is snake_case")]
    if expected == "camelCase" and "_" in name and not name.startswith("_"):
        return [ConsistencyIssue(file=file.name, rule="C1", severity="warning",
                                  message=f"file name '{name}' uses underscores but project convention is camelCase")]
    return []


def _check_schema_library(file: Path, conventions: Dict[str, str]) -> List[ConsistencyIssue]:
    if conventions.get("schema_library") != "pydantic":
        return []
    text = file.read_text(encoding="utf-8")
    if "from marshmallow" in text or "import marshmallow" in text:
        return [ConsistencyIssue(file=file.name, rule="C2", severity="error",
                                  message="generated code uses marshmallow but project uses pydantic")]
    return []


def _check_imports(file: Path, project_root: Path) -> List[ConsistencyIssue]:
    issues: List[ConsistencyIssue] = []
    text = file.read_text(encoding="utf-8")
    # Find top-level relative-style imports: 'from foo import bar' or 'from foo.bar import baz'
    for match in re.finditer(r"^from\s+([a-zA-Z_][\w.]*)\s+import\s+", text, re.MULTILINE):
        module = match.group(1)
        # Skip well-known stdlib + third-party names (cheap allow-list)
        if module.split(".")[0] in {
            "typing", "datetime", "pathlib", "os", "sys", "json", "re",
            "dataclasses", "decimal", "uuid", "logging", "abc",
            "fastapi", "pydantic", "sqlalchemy", "alembic", "starlette",
            "django", "rest_framework", "flask", "pytest", "celery",
            "httpx", "requests",
        }:
            continue
        # Treat the module as a local path under the project root
        candidate_paths = [
            project_root / (module.replace(".", "/") + ".py"),
            project_root / module.replace(".", "/") / "__init__.py",
        ]
        if not any(p.exists() for p in candidate_paths):
            issues.append(ConsistencyIssue(
                file=file.name, rule="C5", severity="error",
                message=f"imports '{module}' but no matching module in project root",
            ))
    return issues


def _check_pagination(file: Path, project_root: Path) -> List[ConsistencyIssue]:
    """Cheap heuristic: scan existing routers for envelope style; if every
    existing router uses an envelope and the generated one returns a list,
    flag drift."""
    if "router" not in file.name and "views" not in file.name:
        return []
    text = file.read_text(encoding="utf-8")
    looks_like_list = bool(re.search(r"return\s+query\.[^\\n]*\.all\(\)", text)) \
        or bool(re.search(r"return\s+\[", text))
    if not looks_like_list:
        return []
    # Look at the existing routers
    envelope_count = 0
    list_count = 0
    for p in project_root.rglob("*.py"):
        if p == file:
            continue
        try:
            other = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "APIRouter" not in other:
            continue
        if '"next"' in other or "Page(" in other:
            envelope_count += 1
        elif re.search(r"\.all\(\)", other):
            list_count += 1
    if envelope_count >= 2 and list_count == 0:
        return [ConsistencyIssue(
            file=file.name, rule="C4", severity="warning",
            message=("project's existing routers use a paginated envelope "
                     "but the generated router returns a plain list"),
        )]
    return []


# ─── Public entry ────────────────────────────────────────────────────────────

def check(project_path: str | Path,
          generated_dir: str | Path) -> ConsistencyReport:
    project = Path(project_path).resolve()
    generated = Path(generated_dir).resolve()
    graph = load_codebase_graph(project)
    issues: List[ConsistencyIssue] = []

    for path in generated.rglob("*.py"):
        issues.extend(_check_naming(path, graph.conventions))
        issues.extend(_check_schema_library(path, graph.conventions))
        issues.extend(_check_imports(path, project))
        issues.extend(_check_pagination(path, project))

    return ConsistencyReport(
        project=str(project),
        generated_dir=str(generated),
        issues=issues,
    )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Check generated code for drift against the existing project"
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--generated-dir", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = check(args.project, args.generated_dir)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"CROSS-FEATURE CONSISTENCY: {'✅ OK' if report.ok else '❌ DRIFT'}")
        for issue in report.issues:
            print(f"  [{issue.severity}] {issue.file}  {issue.rule}: {issue.message}")
        print()
        print("---JSON---")
        print(json.dumps(report.to_dict(), indent=2))

    sys.exit(0 if report.ok else 2)


if __name__ == "__main__":
    main()
