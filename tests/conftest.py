"""
Shared test helpers. Imported automatically by pytest.

pipeline_text() — read SKILL.md + all stages/*.md as one body.
Use instead of reading SKILL.md directly in tests so splits stay
transparent.
"""
import json
from pathlib import Path
from unittest.mock import MagicMock
import sys

# Mock the Jaeger exporter to avoid environment variable import errors
sys.modules['opentelemetry.exporter.jaeger'] = MagicMock()
sys.modules['opentelemetry.exporter.jaeger.thrift'] = MagicMock()

REPO_ROOT = Path(__file__).parent.parent


def pipeline_text() -> str:
    """Full pipeline text: SKILL.md dispatcher + all stages/*.md."""
    base = REPO_ROOT / "skills" / "one-shot-generate"
    parts = [base / "SKILL.md"]
    stages_dir = base / "stages"
    if stages_dir.exists():
        parts += sorted(stages_dir.glob("*.md"))
    return "\n".join(p.read_text(encoding="utf-8") for p in parts if p.exists())


# Helper functions for docs-drift skill tests


def resolve_project_root(arg):
    """Convert @. argument to absolute path. Returns Path object."""
    if arg == "@.":
        return Path.cwd().resolve()

    path = Path(arg).resolve()
    if not path.is_dir():
        raise ValueError(f"Project root does not exist: {path}")
    return path


def load_json_safe(path, default=None):
    """Load JSON file with error handling. Returns dict or default."""
    if not path.exists():
        return default if default is not None else {}

    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"[WARN] Corrupt JSON at {path}: {e}. Using empty state.")
        return default if default is not None else {}


def detect_changes(old_state, new_state):
    """Detect changes between two codebase states. Returns dict."""
    changes = {
        "added_classes": [],
        "removed_classes": [],
        "added_functions": [],
        "removed_functions": [],
        "modified_classes": [],
    }

    old_classes = {e.get("name") for f in old_state.values() for e in f.get("classes", []) if e.get("name")}
    new_classes = {e.get("name") for f in new_state.values() for e in f.get("classes", []) if e.get("name")}

    changes["added_classes"] = sorted(list(new_classes - old_classes))
    changes["removed_classes"] = sorted(list(old_classes - new_classes))

    old_functions = {e.get("name") for f in old_state.values() for e in f.get("functions", []) if e.get("name")}
    new_functions = {e.get("name") for f in new_state.values() for e in f.get("functions", []) if e.get("name")}

    changes["added_functions"] = sorted(list(new_functions - old_functions))
    changes["removed_functions"] = sorted(list(old_functions - new_functions))

    return changes
