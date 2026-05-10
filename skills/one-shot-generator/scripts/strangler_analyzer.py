#!/usr/bin/env python3
"""
Strangler Analyzer — v1.0.0 (Feature Extraction Detection)

Identifies extractable features (potential microservices) from a monolith.
Analyzes coupling, dependencies, and data boundaries.
Scores each feature by extraction difficulty (GREEN/YELLOW/RED).

Usage:
    python strangler_analyzer.py "analyze monolith @/path/to/project"

Output:
    EXTRACTABLE FEATURES TABLE:
    - Feature name, module count, coupling score, difficulty (GREEN/YELLOW/RED)
    - Extraction order recommendations
    - Risk assessment per feature

Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

# Shared library
sys.path.insert(0, str(Path(__file__).parent))
try:
    from lib.base_script import __version__, setup_logging, timed_run
except ImportError:
    __version__ = "1.0.0"
    def setup_logging(name): return None
    def timed_run(): return lambda f: f

logger = setup_logging(__name__)


# ─── Data Models ───────────────────────────────────────────────────────────

@dataclass
class CodeEntity:
    """Represents a function, class, or module."""
    name: str
    entity_type: str  # "function", "class", "module"
    file_path: str
    imports: Set[str] = field(default_factory=set)
    depends_on: Set[str] = field(default_factory=set)
    line_count: int = 0


@dataclass
class Feature:
    """Represents an extractable feature (potential microservice)."""
    name: str
    modules: List[str]
    entity_count: int
    functions: List[str]
    classes: List[str]
    internal_coupling: float  # 0-10, how tightly coupled internally
    external_coupling: float  # 0-10, how tightly coupled to rest of system
    imports_external: Set[str] = field(default_factory=set)
    exported_functions: List[str] = field(default_factory=list)
    data_models: List[str] = field(default_factory=list)

    @property
    def extraction_difficulty(self) -> str:
        """Score: GREEN (easy), YELLOW (medium), RED (hard)."""
        # Logic:
        # - external_coupling < 3 and < 5 functions = GREEN
        # - external_coupling < 6 and < 10 functions = YELLOW
        # - else RED
        if self.external_coupling < 3 and len(self.functions) < 5:
            return "GREEN"
        elif self.external_coupling < 6 and len(self.functions) < 10:
            return "YELLOW"
        else:
            return "RED"

    @property
    def score(self) -> int:
        """Extraction score 1-10 (10 = easy to extract)."""
        base = 10
        base -= min(int(self.external_coupling), 10)  # -0 to -10
        base -= min(len(self.functions) // 5, 3)  # -0 to -3 for many functions
        return max(1, base)


# ─── AST Visitor for Code Analysis ─────────────────────────────────────────

class CodeAnalyzer(ast.NodeVisitor):
    """Visits AST to extract functions, classes, imports."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.functions: Dict[str, CodeEntity] = {}
        self.classes: Dict[str, CodeEntity] = {}
        self.imports: Set[str] = set()
        self.dependencies: Set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        entity = CodeEntity(
            name=node.name,
            entity_type="function",
            file_path=self.file_path,
            line_count=node.end_lineno - node.lineno if node.end_lineno else 0,
        )
        self.functions[node.name] = entity
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        entity = CodeEntity(
            name=node.name,
            entity_type="class",
            file_path=self.file_path,
            line_count=node.end_lineno - node.lineno if node.end_lineno else 0,
        )
        # Extract methods as functions
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method = CodeEntity(
                    name=f"{node.name}.{item.name}",
                    entity_type="method",
                    file_path=self.file_path,
                    line_count=item.end_lineno - item.lineno if item.end_lineno else 0,
                )
                self.functions[f"{node.name}.{item.name}"] = method
        self.classes[node.name] = entity
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.add(alias.name)
            self.dependencies.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            self.imports.add(node.module)
            self.dependencies.add(node.module)
        self.generic_visit(node)


# ─── Monolith Analysis ─────────────────────────────────────────────────────

class MonolithAnalyzer:
    """Analyzes a monolith and identifies extractable features."""

    def __init__(self, root_path: str, framework: str = "django"):
        self.root_path = Path(root_path)
        self.framework = framework.lower()
        self.python_files: List[Path] = []
        self.modules: Dict[str, List[CodeEntity]] = defaultdict(list)
        self.all_functions: Dict[str, CodeEntity] = {}
        self.all_classes: Dict[str, CodeEntity] = {}
        self.all_imports: Set[str] = set()
        self.features: Dict[str, Feature] = {}

    def scan(self) -> Dict[str, Feature]:
        """Scan monolith and return extractable features."""
        self._find_python_files()
        self._analyze_files()
        self._identify_features()
        self._calculate_coupling()
        return self.features

    def _find_python_files(self):
        """Find all .py files except tests, migrations, venv."""
        exclude = {'.venv', 'venv', '__pycache__', '.pytest', 'migrations', 'tests'}
        for f in self.root_path.rglob('*.py'):
            parts = f.parts
            if any(exc in parts for exc in exclude):
                continue
            self.python_files.append(f)

    def _analyze_files(self):
        """Parse each Python file and extract entities."""
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                tree = ast.parse(content)
                analyzer = CodeAnalyzer(str(file_path))
                analyzer.visit(tree)

                # Store entities
                self.all_functions.update(analyzer.functions)
                self.all_classes.update(analyzer.classes)
                self.all_imports.update(analyzer.imports)

                # Group by module
                module_name = file_path.stem
                self.modules[module_name].extend(analyzer.functions.values())
                self.modules[module_name].extend(analyzer.classes.values())
            except (SyntaxError, UnicodeDecodeError):
                continue

    def _identify_features(self):
        """Group modules into logical features."""
        # Strategy: Group by common module prefixes
        # e.g., auth/, payment/, order/ = separate features

        feature_groups: Dict[str, Set[str]] = defaultdict(set)

        for module_name in self.modules.keys():
            # Extract feature prefix (first part of module name)
            parts = module_name.split('_')
            feature_prefix = parts[0]  # e.g., "auth", "payment", "user"
            feature_groups[feature_prefix].add(module_name)

        # Create Feature objects
        for feature_name, modules in feature_groups.items():
            functions = []
            classes = []
            imports = set()

            for module_name in modules:
                for entity in self.modules[module_name]:
                    if entity.entity_type == "function":
                        functions.append(entity.name)
                    elif entity.entity_type in ("class", "method"):
                        classes.append(entity.name)
                    imports.update(entity.imports)

            if functions or classes:  # Only create if non-empty
                self.features[feature_name] = Feature(
                    name=feature_name,
                    modules=sorted(modules),
                    entity_count=len(functions) + len(classes),
                    functions=sorted(functions)[:10],  # Top 10
                    classes=sorted(classes)[:10],  # Top 10
                    imports_external=imports,
                    internal_coupling=0.0,  # Will be calculated
                    external_coupling=0.0,  # Will be calculated
                )

    def _calculate_coupling(self):
        """Calculate internal and external coupling for each feature."""
        for feature_name, feature in self.features.items():
            # Count external imports
            external_imports = 0
            for imp in feature.imports_external:
                # If import is not in any module of this feature, it's external
                if not any(imp in m for m in feature.modules):
                    external_imports += 1

            # External coupling: how many imports point outside this feature
            feature.external_coupling = min(external_imports / max(1, len(feature.imports_external)) * 10, 10)

            # Internal coupling: how tightly coupled are modules within feature
            # Higher = more tightly coupled = harder to extract
            feature.internal_coupling = min(len(feature.modules) * 0.5, 5)

    def get_extraction_order(self) -> List[Tuple[str, str, int]]:
        """Return features sorted by extraction difficulty (easiest first)."""
        return sorted(
            ((f.name, f.extraction_difficulty, f.score) for f in self.features.values()),
            key=lambda x: -x[2]  # Sort by score descending (10 = easiest)
        )

    def to_table(self) -> str:
        """Format as markdown table for output."""
        rows = []
        for name, difficulty, score in self.get_extraction_order():
            feature = self.features[name]
            rows.append(
                f"| {name:20} | {len(feature.modules):3} | {feature.external_coupling:4.1f}/10 | "
                f"{len(feature.functions):3} | {difficulty:6} | {score:2}/10 |"
            )

        header = "| Feature | Modules | Coupling | Funcs | Difficulty | Score |\n"
        separator = "|---------|---------|----------|-------|------------|-------|\n"
        return header + separator + "\n".join(rows)


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    """Entry point for ! injection from SKILL.md."""
    arguments = sys.argv[1] if len(sys.argv) > 1 else ""

    # Parse @path from arguments
    path_match = re.search(r'@(\S+)', arguments)
    if not path_match:
        print("[ERROR] No path provided. Usage: strangler_analyzer.py 'analyze @/path/to/project'")
        sys.exit(1)

    project_path = path_match.group(1)
    if not Path(project_path).exists():
        print("[ERROR] Path does not exist: {}".format(project_path))
        sys.exit(1)

    # Detect framework
    framework = "django"  # default
    if Path(project_path, "go.mod").exists():
        framework = "go"
    elif Path(project_path, "pom.xml").exists():
        framework = "spring"
    elif Path(project_path, "package.json").exists():
        framework = "node"

    print("\n[STRANGLER ANALYSIS]")
    print("-" * 60)
    print("Project: {}".format(project_path))
    print("Framework: {}".format(framework))
    print("")

    # Analyze
    analyzer = MonolithAnalyzer(project_path, framework)
    features = analyzer.scan()

    if features:
        print("[EXTRACTABLE FEATURES] ({} found)\n".format(len(features)))
        print(analyzer.to_table())

        print("\n[EXTRACTION ORDER] (Easiest to Hardest)\n")
        for i, (name, difficulty, score) in enumerate(analyzer.get_extraction_order(), 1):
            feature = features[name]
            print("{}. {:20} [{}] Score: {}/10".format(i, name, difficulty, score))
            print("   Modules: {}".format(', '.join(feature.modules[:3])))
            print("   Functions: {}, Classes: {}".format(len(feature.functions), len(feature.classes)))
            print("   External Coupling: {:.1f}/10".format(feature.external_coupling))
            print("")
    else:
        print("[SKIP] No Python features found (non-Python project or empty codebase)")

    # JSON output for machine parsing
    output = {
        "framework": framework,
        "feature_count": len(features),
        "features": [
            {
                "name": f.name,
                "difficulty": f.extraction_difficulty,
                "score": f.score,
                "modules": f.modules,
                "entity_count": f.entity_count,
                "external_coupling": f.external_coupling,
            }
            for f in sorted(features.values(), key=lambda x: -x.score)
        ]
    }

    print("-" * 60)
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
