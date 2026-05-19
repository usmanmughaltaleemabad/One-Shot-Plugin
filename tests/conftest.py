"""
Shared test helpers. Imported automatically by pytest.

pipeline_text() — read SKILL.md + all stages/*.md as one body.
Use instead of reading SKILL.md directly in tests so splits stay
transparent.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def pipeline_text() -> str:
    """Full pipeline text: SKILL.md dispatcher + all stages/*.md."""
    base = REPO_ROOT / "skills" / "one-shot-generate"
    parts = [base / "SKILL.md"]
    stages_dir = base / "stages"
    if stages_dir.exists():
        parts += sorted(stages_dir.glob("*.md"))
    return "\n".join(p.read_text(encoding="utf-8") for p in parts if p.exists())
