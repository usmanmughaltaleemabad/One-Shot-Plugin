import ast
import json
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


def extract_classes_and_functions(code: str) -> Dict:
    """Extract classes, functions, and imports from Python source code using AST."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {"classes": [], "functions": [], "imports": []}

    entities = {"classes": [], "functions": [], "imports": []}

    # Track which functions are methods (nested in classes)
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            entities["classes"].append({
                "name": node.name,
                "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                "bases": [ast.unparse(b) for b in node.bases],
            })
        elif isinstance(node, ast.FunctionDef):
            # Only include module-level functions (not methods or nested functions)
            parent_is_class_or_func = any(
                isinstance(parent, (ast.ClassDef, ast.FunctionDef))
                and node in ast.walk(parent)
                and parent is not node
                for parent in ast.walk(tree)
                if isinstance(parent, (ast.ClassDef, ast.FunctionDef))
            )
            if not parent_is_class_or_func:
                entities["functions"].append({
                    "name": node.name,
                    "params": [arg.arg for arg in node.args.args],
                })
        elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            entities["imports"].append(ast.unparse(node))

    return entities


def scan_codebase(root: Path) -> Dict:
    """Scan a directory and extract entities from all Python files."""
    all_entities = {}

    if not isinstance(root, Path):
        root = Path(root)

    for py_file in root.rglob("*.py"):
        try:
            code = py_file.read_text(encoding="utf-8")
            entities = extract_classes_and_functions(code)
            all_entities[str(py_file.relative_to(root))] = entities
        except (IOError, OSError, UnicodeDecodeError, SyntaxError) as e:
            logger.warning(f"Error parsing {py_file}: {e}")

    return all_entities


def detect_changes(old_state: Dict, new_state: Dict) -> Dict:
    """Detect changes between two codebase states."""
    changes = {
        "added_classes": [],
        "removed_classes": [],
        "added_functions": [],
        "removed_functions": [],
        "modified_classes": [],
    }

    # Extract class names from states
    old_classes = {e.get("name") for f in old_state.values() for e in f.get("classes", []) if e.get("name")}
    new_classes = {e.get("name") for f in new_state.values() for e in f.get("classes", []) if e.get("name")}

    changes["added_classes"] = list(new_classes - old_classes)
    changes["removed_classes"] = list(old_classes - new_classes)

    # Extract function names from states
    old_functions = {e.get("name") for f in old_state.values() for e in f.get("functions", []) if e.get("name")}
    new_functions = {e.get("name") for f in new_state.values() for e in f.get("functions", []) if e.get("name")}

    changes["added_functions"] = list(new_functions - old_functions)
    changes["removed_functions"] = list(old_functions - new_functions)

    return changes


if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    state = scan_codebase(root)
    print(json.dumps(state, indent=2))
