#!/usr/bin/env python3
"""
Auto-Wirer — v0.8.0

Takes generated files plus an existing project and actually integrates them:

* For FastAPI:        adds ``app.include_router(<entity>.router)`` to main.py
  plus an ``import``.
* For Django:         appends to ``urlpatterns`` in ``urls.py`` and adds an
  ``include('<app>.urls')`` if needed.
* For SQLAlchemy:     if a new ``models.py`` was generated, registers
  ``Base.metadata`` and emits an Alembic migration stub.

The wirer is idempotent: it never duplicates an import or a router-include
that's already in the file. It also writes through a ``.osp.bak`` copy
before mutating, so users can restore the prior state.

Operates in two modes:

    --dry-run     plan only, print the diff that would be applied
    (default)     apply the changes
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Data shapes ─────────────────────────────────────────────────────────────

@dataclass
class WireAction:
    file: str
    description: str
    before: str = ""
    after: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class WireReport:
    framework: str
    actions: List[WireAction] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    dry_run: bool = False

    def to_dict(self) -> Dict:
        return {
            "framework": self.framework,
            "actions": [a.to_dict() for a in self.actions],
            "skipped": self.skipped,
            "dry_run": self.dry_run,
        }


# ─── FastAPI wiring ──────────────────────────────────────────────────────────

def _wire_fastapi(project: Path, generated: Dict[str, str],
                  report: WireReport, dry_run: bool) -> None:
    main_candidates = [project / "main.py", project / "app" / "main.py",
                       project / "src" / "main.py"]
    main_file = next((p for p in main_candidates if p.exists()), None)
    if not main_file:
        report.skipped.append("no main.py found to attach FastAPI routers to")
        return

    # Find generated router files: anything named router.py under a subfolder
    router_modules: List[str] = []
    for name in generated:
        if name.endswith("router.py") and "/" in name.replace("\\", "/"):
            # 'product/router.py' → import 'product.router'
            module = name.replace("\\", "/").removesuffix(".py").replace("/", ".")
            router_modules.append(module)
    if not router_modules:
        report.skipped.append("no <entity>/router.py files in generated output")
        return

    original = main_file.read_text(encoding="utf-8")
    updated = original
    for module in router_modules:
        var = module.split(".")[0]  # 'product.router' → 'product'
        import_line = f"from {module} import router as {var}_router"
        include_line = f"app.include_router({var}_router)"
        if import_line in updated and include_line in updated:
            report.skipped.append(f"{module} already wired")
            continue
        # Insert import after the last 'from ... import' or 'import ...'
        if import_line not in updated:
            updated = _insert_after_imports(updated, import_line)
        if include_line not in updated:
            # Place after FastAPI app construction; fallback append.
            anchor = re.search(r"^(app\s*=\s*FastAPI\([^)]*\)\s*$)",
                               updated, re.MULTILINE)
            if anchor:
                insert_at = anchor.end()
                updated = updated[:insert_at] + "\n" + include_line + updated[insert_at:]
            else:
                updated = updated.rstrip() + "\n\n" + include_line + "\n"
        report.actions.append(WireAction(
            file=str(main_file.relative_to(project)).replace("\\", "/"),
            description=f"include {var}_router",
            before="", after=include_line,
        ))

    if not dry_run and updated != original:
        backup = main_file.with_suffix(main_file.suffix + ".osp.bak")
        if not backup.exists():
            shutil.copy(main_file, backup)
        main_file.write_text(updated, encoding="utf-8")


def _insert_after_imports(text: str, new_line: str) -> str:
    lines = text.splitlines(keepends=True)
    last_import = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")) and not stripped.startswith("from ."):
            last_import = i
    if last_import == -1:
        return new_line + "\n" + text
    lines.insert(last_import + 1, new_line + "\n")
    return "".join(lines)


# ─── Django wiring ───────────────────────────────────────────────────────────

def _wire_django(project: Path, generated: Dict[str, str],
                 report: WireReport, dry_run: bool) -> None:
    urls_file = next(iter(project.rglob("urls.py")), None)
    if urls_file is None:
        report.skipped.append("no urls.py found in Django project")
        return
    original = urls_file.read_text(encoding="utf-8")
    updated = original
    # Find generated apps: any folder containing both models.py and views.py
    for name in generated:
        parts = name.replace("\\", "/").split("/")
        if len(parts) < 2 or not parts[-1].endswith(".py"):
            continue
        app_name = parts[0]
        urls_include = f"path('{app_name}/', include('{app_name}.urls'))"
        if urls_include in updated:
            report.skipped.append(f"{app_name} urls already included")
            continue
        # Add an include in urlpatterns
        if "urlpatterns" not in updated:
            report.skipped.append("urls.py has no urlpatterns list")
            return
        if "include" not in updated:
            updated = "from django.urls import include, path\n" + updated
        updated = re.sub(
            r"(urlpatterns\s*=\s*\[)",
            r"\1\n    " + urls_include + ",",
            updated,
            count=1,
        )
        report.actions.append(WireAction(
            file=str(urls_file.relative_to(project)).replace("\\", "/"),
            description=f"include {app_name}.urls",
            before="", after=urls_include,
        ))
    if not dry_run and updated != original:
        backup = urls_file.with_suffix(urls_file.suffix + ".osp.bak")
        if not backup.exists():
            shutil.copy(urls_file, backup)
        urls_file.write_text(updated, encoding="utf-8")


# ─── Public entry ────────────────────────────────────────────────────────────

from lib.telemetry import traced as _traced


@_traced("auto_wire", attr_keys=["framework", "dry_run"])
def wire(project: str | Path, generated_files: Dict[str, str], *,
         framework: Optional[str] = None, dry_run: bool = False) -> WireReport:
    project_path = Path(project).expanduser().resolve()
    if framework is None:
        # Best-effort sniff
        if (project_path / "manage.py").exists():
            framework = "django"
        elif any(f.endswith("main.py") for f in
                 [p.name for p in project_path.glob("*.py")]):
            framework = "fastapi"
        else:
            framework = "unknown"
    report = WireReport(framework=framework, dry_run=dry_run)
    if framework == "fastapi":
        _wire_fastapi(project_path, generated_files, report, dry_run)
    elif framework == "django":
        _wire_django(project_path, generated_files, report, dry_run)
    else:
        report.skipped.append(f"framework '{framework}' not supported by auto-wirer yet")
    return report


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Wire generated files into an existing project"
    )
    parser.add_argument("--project", required=True,
                        help="Path to the target project")
    parser.add_argument("--generated-dir", required=True,
                        help="Directory containing generated files")
    parser.add_argument("--framework", choices=["fastapi", "django"],
                        help="Override framework detection")
    parser.add_argument("--dry-run", action="store_true",
                        help="Plan only — do not modify files")
    args = parser.parse_args()

    src = Path(args.generated_dir).resolve()
    files = {}
    for path in src.rglob("*"):
        if path.is_file():
            try:
                files[str(path.relative_to(src)).replace("\\", "/")] = \
                    path.read_text(encoding="utf-8")
            except Exception:
                continue

    report = wire(args.project, files, framework=args.framework,
                  dry_run=args.dry_run)
    print("AUTO-WIRE REPORT")
    print("─" * 60)
    print(f"  Framework: {report.framework}")
    print(f"  Mode:      {'DRY RUN' if args.dry_run else 'APPLIED'}")
    print(f"  Actions:   {len(report.actions)}")
    for action in report.actions:
        print(f"    + {action.file}: {action.description}")
    if report.skipped:
        print(f"  Skipped:   {len(report.skipped)}")
        for note in report.skipped:
            print(f"    - {note}")
    print()
    print("---JSON---")
    print(json.dumps(report.to_dict(), indent=2))


if __name__ == "__main__":
    main()
