#!/usr/bin/env python3
"""
Existing Codebase Scanner — v0.8.0

Parses an existing project and returns a ``CodebaseGraph`` describing every
domain entity that already lives there, plus the conventions the project
uses. Generators consult this graph BEFORE producing new code, so they:

  * reuse existing model classes (no parallel duplicate ``Product`` models),
  * match the project's naming conventions (snake_case vs camelCase),
  * pick up the actual ``get_db`` import path (not the hardcoded one),
  * spot which router prefix style is in use.

The scanner is AST-based for Python files (Django models, FastAPI Pydantic
schemas, SQLAlchemy declarative classes) and regex-based as a fallback for
other languages.

Output JSON shape:

    {
        "language": "python",
        "framework": "fastapi",
        "entities": [
            {"name": "Product", "file": "models.py", "fields": [...],
             "kind": "sqlalchemy_model"}
        ],
        "imports": {
            "db_session_getter": {"name": "get_db", "module": "database"},
            "model_base": {"name": "Base", "module": "models"}
        },
        "router_style": "fastapi_apirouter",   # or django_urls
        "test_layout": "tests/",
        "conventions": {
            "naming": "snake_case",
            "schema_library": "pydantic",
            "orm": "sqlalchemy",
        }
    }
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Data shapes ─────────────────────────────────────────────────────────────

@dataclass
class ExistingField:
    name: str
    type_hint: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ExistingEntity:
    name: str                      # PascalCase class name as found
    file: str                      # relative path to source
    kind: str                      # sqlalchemy_model | django_model | pydantic_schema | unknown
    fields: List[ExistingField] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "file": self.file,
            "kind": self.kind,
            "fields": [f.to_dict() for f in self.fields],
            "base_classes": self.base_classes,
        }


@dataclass
class ImportRef:
    name: str
    module: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CodebaseGraph:
    project_path: str
    language: str
    framework: str
    entities: List[ExistingEntity] = field(default_factory=list)
    imports: Dict[str, ImportRef] = field(default_factory=dict)
    router_style: Optional[str] = None
    test_layout: Optional[str] = None
    conventions: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "project_path": self.project_path,
            "language": self.language,
            "framework": self.framework,
            "entities": [e.to_dict() for e in self.entities],
            "imports": {k: v.to_dict() for k, v in self.imports.items()},
            "router_style": self.router_style,
            "test_layout": self.test_layout,
            "conventions": self.conventions,
        }

    def find_entity(self, name: str) -> Optional[ExistingEntity]:
        """Return existing entity with matching PascalCase or snake_case name."""
        target = name.lower().replace("_", "")
        for ent in self.entities:
            if ent.name.lower() == target:
                return ent
        return None


# ─── Detection helpers ───────────────────────────────────────────────────────

PYTHON_FRAMEWORK_MARKERS = {
    "django": ["django", "manage.py"],
    "fastapi": ["fastapi"],
    "flask": ["flask"],
}


def _detect_language_and_framework(project: Path) -> Tuple[str, str]:
    if (project / "requirements.txt").exists() or (project / "pyproject.toml").exists() \
            or list(project.rglob("*.py"))[:1]:
        # Python project
        manifest = ""
        for name in ("requirements.txt", "pyproject.toml", "setup.py", "setup.cfg"):
            p = project / name
            if p.exists():
                manifest += p.read_text(encoding="utf-8", errors="ignore").lower()
        for framework, markers in PYTHON_FRAMEWORK_MARKERS.items():
            if any(m in manifest for m in markers):
                return "python", framework
        # Manage.py is the unique Django marker even without manifest
        if (project / "manage.py").exists():
            return "python", "django"
        # Fall through: Python but framework unknown
        return "python", "unknown"
    if (project / "package.json").exists():
        return "typescript", "unknown"
    if (project / "go.mod").exists():
        return "go", "unknown"
    if (project / "pom.xml").exists() or (project / "build.gradle").exists():
        return "java", "spring"
    return "unknown", "unknown"


# ─── Python AST walker ───────────────────────────────────────────────────────

class _PythonEntityVisitor(ast.NodeVisitor):
    """Walk a Python module collecting ORM/schema class definitions."""

    SQLALCHEMY_BASES = {"Base", "DeclarativeBase", "db.Model"}
    DJANGO_BASES = {"models.Model", "Model", "AbstractUser", "AbstractBaseUser"}
    PYDANTIC_BASES = {"BaseModel", "Schema", "SQLModel"}

    def __init__(self, source_file: str):
        self.source_file = source_file
        self.entities: List[ExistingEntity] = []
        # Track top-level Name → module aliasing for type hints
        self.imports_by_alias: Dict[str, str] = {}

    # ── Imports ──────────────────────────────────────────────────────────
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports_by_alias[alias.asname or alias.name] = alias.name

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            self.imports_by_alias[alias.asname or alias.name] = f"{module}.{alias.name}"

    # ── Classes ──────────────────────────────────────────────────────────
    def visit_ClassDef(self, node: ast.ClassDef):
        base_names = [self._base_name(b) for b in node.bases]
        kind = self._classify(base_names)
        if kind == "unknown":
            return  # only record domain-ish classes
        fields = self._extract_fields(node)
        self.entities.append(ExistingEntity(
            name=node.name,
            file=self.source_file,
            kind=kind,
            fields=fields,
            base_classes=base_names,
        ))

    # ── Internal helpers ─────────────────────────────────────────────────
    @staticmethod
    def _base_name(base: ast.expr) -> str:
        if isinstance(base, ast.Name):
            return base.id
        if isinstance(base, ast.Attribute):
            return f"{_PythonEntityVisitor._dotted(base)}"
        return "<unknown>"

    @staticmethod
    def _dotted(node: ast.Attribute) -> str:
        parts: List[str] = [node.attr]
        cur = node.value
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))

    def _classify(self, bases: List[str]) -> str:
        bases_set = set(bases)
        if bases_set & self.SQLALCHEMY_BASES or any(
                b.endswith(".Base") for b in bases):
            return "sqlalchemy_model"
        if bases_set & self.DJANGO_BASES or any(
                b == "models.Model" for b in bases):
            return "django_model"
        if bases_set & self.PYDANTIC_BASES:
            return "pydantic_schema"
        return "unknown"

    def _extract_fields(self, node: ast.ClassDef) -> List[ExistingField]:
        out: List[ExistingField] = []
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                out.append(ExistingField(stmt.target.id,
                                          self._unparse_safe(stmt.annotation)))
            elif isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        # Skip dunder / private
                        if target.id.startswith("_"):
                            continue
                        out.append(ExistingField(target.id, None))
        return out

    @staticmethod
    def _unparse_safe(node) -> Optional[str]:
        try:
            return ast.unparse(node)
        except Exception:
            return None


def _scan_python_file(path: Path, project_root: Path) -> List[ExistingEntity]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"),
                         filename=str(path))
    except SyntaxError as exc:
        logger.debug("Skipping %s: %s", path, exc)
        return []
    relative = str(path.relative_to(project_root)).replace("\\", "/")
    visitor = _PythonEntityVisitor(relative)
    visitor.visit(tree)
    return visitor.entities


# ─── Convention + import detection ───────────────────────────────────────────

_GET_DB_PATTERN = re.compile(r"def\s+get_db\s*\(")
_BASE_PATTERN = re.compile(r"\bBase\s*=\s*declarative_base|\bclass\s+Base\b")
_APIROUTER_PATTERN = re.compile(r"APIRouter\s*\(")
_DJANGO_URLS_PATTERN = re.compile(r"urlpatterns\s*=\s*\[")


def _detect_conventions(project: Path, language: str, framework: str,
                        py_files: List[Path]) -> Tuple[Dict[str, ImportRef],
                                                       Optional[str],
                                                       Dict[str, str]]:
    imports: Dict[str, ImportRef] = {}
    router_style: Optional[str] = None
    conventions: Dict[str, str] = {"naming": "snake_case"}

    if language == "python":
        for path in py_files:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            rel_module = (str(path.relative_to(project))
                          .replace("\\", "/")
                          .replace("/", ".")
                          .removesuffix(".py"))
            if _GET_DB_PATTERN.search(text):
                imports.setdefault("db_session_getter",
                                   ImportRef("get_db", rel_module))
            if _BASE_PATTERN.search(text):
                imports.setdefault("model_base",
                                   ImportRef("Base", rel_module))
            if _APIROUTER_PATTERN.search(text):
                router_style = router_style or "fastapi_apirouter"
            if _DJANGO_URLS_PATTERN.search(text):
                router_style = router_style or "django_urls"

        # Convention enrichments
        if any("pydantic" in p.read_text(encoding="utf-8", errors="ignore").lower()[:2000]
               for p in py_files[:15]):
            conventions["schema_library"] = "pydantic"
        if any("sqlalchemy" in p.read_text(encoding="utf-8", errors="ignore").lower()[:2000]
               for p in py_files[:15]):
            conventions["orm"] = "sqlalchemy"
        elif framework == "django":
            conventions["orm"] = "django_orm"

    return imports, router_style, conventions


def _detect_test_layout(project: Path) -> Optional[str]:
    for candidate in ("tests", "test", "spec", "__tests__"):
        if (project / candidate).is_dir():
            return f"{candidate}/"
    return None


# ─── Public entry ────────────────────────────────────────────────────────────

def scan(project_path: str | Path) -> CodebaseGraph:
    project = Path(project_path).expanduser().resolve()
    if not project.is_dir():
        logger.warning("Project path does not exist: %s", project)
        return CodebaseGraph(
            project_path=str(project),
            language="unknown",
            framework="unknown",
        )

    language, framework = _detect_language_and_framework(project)
    entities: List[ExistingEntity] = []
    py_files: List[Path] = []
    if language == "python":
        py_files = [p for p in project.rglob("*.py")
                    if "venv" not in p.parts
                    and ".venv" not in p.parts
                    and "site-packages" not in p.parts
                    and "__pycache__" not in p.parts]
        # Keep scan bounded for very large repos
        for path in py_files[:300]:
            entities.extend(_scan_python_file(path, project))

    imports, router_style, conventions = _detect_conventions(
        project, language, framework, py_files)
    test_layout = _detect_test_layout(project)

    return CodebaseGraph(
        project_path=str(project),
        language=language,
        framework=framework,
        entities=entities,
        imports=imports,
        router_style=router_style,
        test_layout=test_layout,
        conventions=conventions,
    )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Scan an existing codebase and emit a domain graph as JSON"
    )
    parser.add_argument("project", help="Path to project root")
    parser.add_argument("--summary", action="store_true",
                        help="Emit a human-readable summary instead of JSON")
    args = parser.parse_args()

    graph = scan(args.project)
    if args.summary:
        print("CODEBASE GRAPH")
        print("─" * 60)
        print(f"  Path:        {graph.project_path}")
        print(f"  Language:    {graph.language}")
        print(f"  Framework:   {graph.framework}")
        print(f"  Router:      {graph.router_style or '—'}")
        print(f"  Tests in:    {graph.test_layout or '—'}")
        print()
        if graph.entities:
            print(f"EXISTING ENTITIES ({len(graph.entities)})")
            for ent in graph.entities[:20]:
                fields = ", ".join(f.name for f in ent.fields[:6])
                if len(ent.fields) > 6:
                    fields += f", … (+{len(ent.fields) - 6})"
                print(f"  • {ent.name:<20} [{ent.kind:<18}] {ent.file}  ({fields})")
            if len(graph.entities) > 20:
                print(f"  … (+{len(graph.entities) - 20} more)")
        else:
            print("EXISTING ENTITIES: none detected")
        if graph.imports:
            print()
            print("IMPORT CONTRACTS")
            for key, ref in graph.imports.items():
                print(f"  • {key:<20} {ref.name} from {ref.module}")
        return
    print(json.dumps(graph.to_dict(), indent=2))


if __name__ == "__main__":
    main()
