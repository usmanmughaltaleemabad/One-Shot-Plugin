#!/usr/bin/env python3
"""
Context Writer — v1.0.0  (CLAUDE.md skeleton generator)

The plugin's body_hints catalogue includes a `context_engineering`
ethos — "rules files first, persistent project conventions loaded
every session, selective loading over flooding." That ethos is
*implicit* in our internals but invisible to users adopting the
plugin into their own project.

This script makes it explicit: scan a project, detect the framework +
the relevant tooling already in use, and emit a CLAUDE.md skeleton
that captures the conventions a fresh Claude session needs to
behave consistently. Inspired by addyosmani/agent-skills'
context-engineering skill.

Output is a starting point, NOT a final document. The user should
edit it, add their team's conventions, then commit it.

CLI:
    context_writer.py --project <dir>                # emit to ./CLAUDE.md
    context_writer.py --project <dir> --out <path>   # custom output path
    context_writer.py --project <dir> --json         # emit JSON description only
    context_writer.py --project <dir> --force        # overwrite existing CLAUDE.md
    context_writer.py --project <dir> --append       # add to existing CLAUDE.md
                                                       (use when there's already one
                                                        and we want to enrich it)

Exit codes:
    0  CLAUDE.md emitted / would be emitted
    1  bad args / project missing
    2  CLAUDE.md already exists and neither --force nor --append passed
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
bootstrap_runtime()
logger = setup_logging(__name__)


# ─── Detection — framework + tooling already in the project ───────────────

@dataclass
class ProjectFingerprint:
    framework: Optional[str] = None
    framework_version: Optional[str] = None
    language: Optional[str] = None       # python | java | typescript | javascript | go
    orm: Optional[str] = None
    test_runner: Optional[str] = None
    linter: Optional[str] = None
    type_checker: Optional[str] = None
    formatter: Optional[str] = None
    migration_tool: Optional[str] = None
    has_dockerfile: bool = False
    has_ci: bool = False
    extras: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


_PYTHON_MARKERS = [
    (r"\bfastapi\b",          "framework", "fastapi"),
    (r"\bdjango\b",           "framework", "django"),
    (r"\bflask\b",            "framework", "flask"),
    (r"\bsqlalchemy\b",       "orm",       "sqlalchemy"),
    (r"\balembic\b",          "migration_tool", "alembic"),
    (r"\bpytest\b",           "test_runner", "pytest"),
    (r"\bruff\b",             "linter",    "ruff"),
    (r"\bblack\b",            "formatter", "black"),
    (r"\bmypy\b",             "type_checker", "mypy"),
    (r"\bpyright\b",          "type_checker", "pyright"),
]

_NODE_MARKERS = [
    (r'"@nestjs/core"',       "framework", "nestjs"),
    (r'"express"',            "framework", "express"),
    (r'"next"',               "framework", "next.js"),
    (r'"sequelize"',          "orm",       "sequelize"),
    (r'"typeorm"',             "orm",       "typeorm"),
    (r'"prisma"',             "orm",       "prisma"),
    (r'"jest"',               "test_runner", "jest"),
    (r'"vitest"',             "test_runner", "vitest"),
    (r'"eslint"',             "linter",    "eslint"),
    (r'"prettier"',           "formatter", "prettier"),
    (r'"typescript"',         "language",  "typescript"),
]

_GO_MARKERS = [
    (r"github\.com/.*?/gin",      "framework", "gin"),
    (r"github\.com/labstack/echo", "framework", "echo"),
    (r"gorm\.io/gorm",            "orm",        "gorm"),
    (r"github\.com/jmoiron/sqlx", "orm",        "sqlx"),
]


def _scan_file(content: str, markers, fingerprint: ProjectFingerprint) -> None:
    for pattern, slot, value in markers:
        if re.search(pattern, content, re.I):
            current = getattr(fingerprint, slot, None)
            if current is None:
                setattr(fingerprint, slot, value)


def _extract_version(content: str, package: str) -> Optional[str]:
    """Pull a version like `fastapi==0.115.6` or `"fastapi": "^0.115.6"`."""
    patterns = [
        rf"{re.escape(package)}\s*[=~><]+\s*(\d+\.\d+(?:\.\d+)?)",
        rf'"{re.escape(package)}"\s*:\s*"\^?(\d+\.\d+(?:\.\d+)?)"',
    ]
    for p in patterns:
        m = re.search(p, content, re.I)
        if m:
            return m.group(1)
    return None


def fingerprint_project(project: Path) -> ProjectFingerprint:
    fp = ProjectFingerprint()

    # Python project
    pyproject = project / "pyproject.toml"
    requirements = project / "requirements.txt"
    pipfile = project / "Pipfile"
    for path in (pyproject, requirements, pipfile):
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        fp.language = fp.language or "python"
        _scan_file(content, _PYTHON_MARKERS, fp)
        if fp.framework:
            fp.framework_version = _extract_version(content, fp.framework)
        break

    # Node project
    pkg = project / "package.json"
    if pkg.exists():
        try:
            content = pkg.read_text(encoding="utf-8", errors="replace")
        except OSError:
            content = ""
        if content:
            # Detect typescript BEFORE defaulting language to javascript —
            # otherwise the markers loop (which only sets non-set slots)
            # never gets to upgrade js→ts.
            if re.search(r'"typescript"', content, re.I):
                fp.language = fp.language or "typescript"
            else:
                fp.language = fp.language or "javascript"
            _scan_file(content, _NODE_MARKERS, fp)
            if fp.framework:
                _key = {"nestjs": "@nestjs/core", "express": "express",
                        "next.js": "next"}.get(fp.framework, fp.framework)
                fp.framework_version = _extract_version(content, _key)

    # Go project
    gomod = project / "go.mod"
    if gomod.exists():
        try:
            content = gomod.read_text(encoding="utf-8", errors="replace")
        except OSError:
            content = ""
        if content:
            fp.language = fp.language or "go"
            _scan_file(content, _GO_MARKERS, fp)

    # Spring / Java
    pom = project / "pom.xml"
    if pom.exists():
        try:
            content = pom.read_text(encoding="utf-8", errors="replace")
        except OSError:
            content = ""
        if "spring-boot" in content.lower():
            fp.language = fp.language or "java"
            fp.framework = "spring"
            m = re.search(
                r"spring-boot[^>]*</artifactId>\s*<version>\s*(\d+\.\d+(?:\.\d+)?)",
                content, re.I,
            )
            if m:
                fp.framework_version = m.group(1)
        fp.test_runner = fp.test_runner or "junit"
        fp.migration_tool = fp.migration_tool or "flyway"

    # Ambient signals
    fp.has_dockerfile = (project / "Dockerfile").exists()
    fp.has_ci = (
        (project / ".github" / "workflows").exists()
        or (project / ".gitlab-ci.yml").exists()
        or (project / "Jenkinsfile").exists()
    )

    # Migration tool inference for Python
    if fp.language == "python" and not fp.migration_tool:
        if (project / "alembic").is_dir():
            fp.migration_tool = "alembic"
        elif fp.framework == "django":
            fp.migration_tool = "django-migrations"

    return fp


# ─── Template ──────────────────────────────────────────────────────────────

def render_skeleton(fp: ProjectFingerprint, project_name: str) -> str:
    """Render a CLAUDE.md skeleton from the fingerprint. Sections the
    user is expected to fill in are marked with `(fill in)`."""
    fw = fp.framework or "(detect framework first)"
    version = f"=={fp.framework_version}" if fp.framework_version else "(version not detected)"
    orm = fp.orm or "(orm not detected — fill in)"
    tests = fp.test_runner or "(test runner not detected — fill in)"
    linter = fp.linter or "(linter not detected — fill in)"
    formatter = fp.formatter or "(formatter not detected — fill in)"
    type_checker = fp.type_checker or "(none detected)"
    migration_tool = fp.migration_tool or "(migration tool not detected — fill in)"

    lines = [
        "---",
        "type: router",
        f"last_verified: 2026-05-18",
        "owner: project",
        "---",
        "",
        f"# {project_name} — Project Context for Claude",
        "",
        "Auto-generated skeleton from `/context`. **Edit this file before",
        "checking it in** — replace `(fill in)` markers with team-specific",
        "conventions, and trim sections that don't apply.",
        "",
        "## Stack",
        "",
        f"- **Language**: {fp.language or '(fill in)'}",
        f"- **Framework**: {fw} `{version}`",
        f"- **ORM / DB layer**: {orm}",
        f"- **Test runner**: {tests}",
        f"- **Linter**: {linter}",
        f"- **Formatter**: {formatter}",
        f"- **Type checker**: {type_checker}",
        f"- **Migrations**: {migration_tool}",
        f"- **Docker**: {'yes' if fp.has_dockerfile else 'no'}",
        f"- **CI**: {'yes' if fp.has_ci else 'no'}",
        "",
        "## Conventions Claude MUST follow",
        "",
        "(Fill in your team's actual rules. Examples:)",
        "",
        "- Imports: absolute (not relative) for cross-module references",
        "- Naming: `snake_case` for modules + variables; `PascalCase` for classes",
        "- Error envelope: `{code, message, request_id}` — never raw HTTP status",
        "- Type hints required for all public function signatures",
        "- Never use `print()` in production code — use the logger",
        "",
        "## Conventions Claude must NEVER do",
        "",
        "(Anti-patterns specific to your team. Examples:)",
        "",
        "- No `*` imports",
        "- No `pickle` for persistence (security)",
        "- No HTTP exceptions in the service layer (only the router)",
        "- No silent `except: pass` — at minimum log",
        "",
        "## Where things live",
        "",
        "(Map your repo structure so Claude knows where to look. Examples:)",
        "",
        "```",
        "src/",
        "  features/   # one folder per business capability",
        "  common/     # shared utilities, errors, events",
        "  config/     # settings, env loading",
        "tests/",
        "  unit/",
        "  integration/",
        "```",
        "",
        "## How to run things",
        "",
        "```bash",
    ]

    # Framework-specific quick commands
    if fp.framework == "fastapi":
        lines += [
            "# Dev server",
            "uvicorn main:app --reload",
            "",
            "# Tests",
            f"{tests if tests != '(test runner not detected — fill in)' else 'pytest'} tests/",
            "",
            "# Migrations",
            "alembic upgrade head" if migration_tool == "alembic" else "(fill in)",
        ]
    elif fp.framework == "django":
        lines += [
            "# Dev server",
            "python manage.py runserver",
            "",
            "# Tests",
            "python manage.py test",
            "",
            "# Migrations",
            "python manage.py makemigrations",
            "python manage.py migrate",
        ]
    elif fp.framework == "spring":
        lines += [
            "# Build + test",
            "mvn verify",
            "",
            "# Dev server",
            "mvn spring-boot:run",
        ]
    elif fp.framework == "nestjs":
        lines += [
            "# Dev server",
            "npm run start:dev",
            "",
            "# Tests",
            "npm test",
        ]
    elif fp.framework in ("gin", "echo", None):
        lines += [
            "# Build + test",
            "go build ./...",
            "go test ./...",
        ]
    else:
        lines += [
            "# (fill in — dev server, tests, migrations)",
        ]

    lines += [
        "```",
        "",
        "## What's risky / requires review",
        "",
        "(Things Claude should pause + confirm before changing:)",
        "",
        "- Anything in `migrations/` — production schema changes are irreversible",
        "- `settings.py` / `config/` — global behaviour",
        "- Files matching `*_test_helpers.py` — test infrastructure other tests depend on",
        "- (add team-specific examples)",
        "",
        "## Quick links",
        "",
        "- Architecture decisions: `docs/adr/`",
        "- API contract: `(fill in — OpenAPI URL or file path)`",
        "- Deployment runbook: `(fill in)`",
        "- On-call dashboard: `(fill in)`",
        "",
        "---",
        "",
        "_Generated by `/context` (one-shot-prompting plugin)._",
        "_Replace `(fill in)` markers and commit this file so future Claude_",
        "_sessions load it automatically._",
    ]

    return "\n".join(lines) + "\n"


# ─── CLI ───────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Generate a CLAUDE.md skeleton from a project's "
                    "detected stack + conventions."
    )
    p.add_argument("--project", required=True, type=Path)
    p.add_argument("--out", type=Path, default=None,
                   help="Output path (default: <project>/CLAUDE.md)")
    p.add_argument("--json", action="store_true",
                   help="Print the fingerprint JSON only (no write)")
    p.add_argument("--force", action="store_true",
                   help="Overwrite if CLAUDE.md already exists")
    p.add_argument("--append", action="store_true",
                   help="Append a fresh skeleton to existing CLAUDE.md")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.project.exists():
        print(f"project not found: {args.project}", file=sys.stderr)
        return 1

    fp = fingerprint_project(args.project.resolve())

    if args.json:
        print(json.dumps(fp.to_dict(), indent=2))
        return 0

    project_name = args.project.resolve().name
    skeleton = render_skeleton(fp, project_name)

    out_path = args.out or (args.project / "CLAUDE.md")
    if out_path.exists() and not args.force and not args.append:
        print(f"CLAUDE.md already exists at {out_path}. "
              f"Pass --force to overwrite or --append to add.",
              file=sys.stderr)
        return 2

    if args.append and out_path.exists():
        existing = out_path.read_text(encoding="utf-8")
        out_path.write_text(
            existing + "\n\n<!-- Auto-appended by /context -->\n\n" + skeleton,
            encoding="utf-8",
        )
    else:
        out_path.write_text(skeleton, encoding="utf-8")

    summary = {
        "status": "appended" if args.append else "written",
        "out_path": str(out_path),
        "fingerprint": fp.to_dict(),
        "skeleton_chars": len(skeleton),
        "next_steps": [
            "Open " + str(out_path) + " and replace '(fill in)' markers",
            "Add team-specific conventions in 'Conventions Claude MUST follow'",
            "Commit the file so future Claude sessions load it automatically",
        ],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
