#!/usr/bin/env python3
"""Framework detection with harness awareness (Phase 2 enhancement)"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple


def detect_framework_from_harness(project_path: str) -> Tuple[str, Dict]:
    """
    Detect framework by reading harness config and project structure.

    Args:
        project_path: Root directory of project

    Returns:
        (framework_name, framework_info_dict)
        framework_name: 'django', 'fastapi', 'spring', 'go', 'node'
        framework_info: version, detected_patterns, standards_to_apply
    """

    # Step 1: Read .claude/CLAUDE.md for hints
    framework, version = _read_harness_hints(project_path)
    if framework:
        standards = _load_team_standards(project_path)
        return framework, {
            "name": framework,
            "version": version,
            "source": "harness",
            "standards": standards,
        }

    # Step 2: Detect from project files
    framework = _detect_from_files(project_path)
    if framework:
        version = _detect_version(project_path, framework)
        standards = _load_team_standards(project_path)
        return framework, {
            "name": framework,
            "version": version,
            "source": "project_structure",
            "standards": standards,
        }

    # Step 3: Fallback (shouldn't happen if project is valid)
    return "unknown", {}


def _read_harness_hints(project_path: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract framework hints from .claude/CLAUDE.md"""

    harness_file = Path(project_path) / ".claude" / "CLAUDE.md"
    if not harness_file.exists():
        return None, None

    content = harness_file.read_text()

    # Look for framework version lines like "Django 4.2+"
    frameworks = {
        "django": ("Django", "4.2"),
        "fastapi": ("FastAPI", "0.104"),
        "spring": ("Spring Boot", "3.2"),
        "go": ("Go", "1.21"),
        "node": ("Node", "18"),
    }

    for framework, (name_pattern, default_version) in frameworks.items():
        if name_pattern in content:
            # Try to extract version
            for line in content.split("\n"):
                if name_pattern in line:
                    # Parse "Django 4.2+" or similar
                    parts = line.split()
                    version = None
                    for i, part in enumerate(parts):
                        if name_pattern in part and i + 1 < len(parts):
                            version = parts[i + 1]
                            break
                    return framework, version or default_version

    return None, None


def _load_team_standards(project_path: str) -> Dict:
    """Load standards from .claude/standards/"""

    standards = {
        "code_style": None,
        "testing": None,
        "security": None,
    }

    standards_dir = Path(project_path) / ".claude" / "standards"
    if not standards_dir.exists():
        return standards

    # Code style
    code_style_file = standards_dir / "code-style-*.md"
    for file in standards_dir.glob("code-style-*.md"):
        standards["code_style"] = file.read_text()[:500]  # First 500 chars
        break

    # Testing rules
    testing_file = standards_dir / "testing-rules.md"
    if testing_file.exists():
        standards["testing"] = testing_file.read_text()[:500]

    # Security rules
    security_file = standards_dir / "security-rules.md"
    if security_file.exists():
        standards["security"] = security_file.read_text()[:500]

    return standards


def _detect_from_files(project_path: str) -> Optional[str]:
    """Detect framework from config files and structure"""

    project = Path(project_path)

    # Django: manage.py, settings.py
    if (project / "manage.py").exists() or (project / "settings.py").exists():
        return "django"

    # FastAPI: main.py with FastAPI import, or fastapi in requirements
    if (project / "main.py").exists():
        main_content = (project / "main.py").read_text()
        if "fastapi" in main_content.lower():
            return "fastapi"

    # Spring: pom.xml (Maven) or build.gradle
    if (project / "pom.xml").exists():
        return "spring"
    if (project / "build.gradle").exists():
        return "spring"

    # Go: go.mod
    if (project / "go.mod").exists():
        return "go"

    # Node: package.json
    if (project / "package.json").exists():
        return "node"

    # Fallback
    requirements = project / "requirements.txt"
    if requirements.exists():
        content = requirements.read_text()
        if "django" in content:
            return "django"
        if "fastapi" in content:
            return "fastapi"

    return None


def _detect_version(project_path: str, framework: str) -> Optional[str]:
    """Detect framework version from dependency files"""

    project = Path(project_path)

    if framework == "django":
        requirements = project / "requirements.txt"
        if requirements.exists():
            for line in requirements.read_text().split("\n"):
                if line.startswith("Django"):
                    return line.split("==")[1] if "==" in line else "latest"

    elif framework == "fastapi":
        requirements = project / "requirements.txt"
        if requirements.exists():
            for line in requirements.read_text().split("\n"):
                if line.startswith("fastapi"):
                    return line.split("==")[1] if "==" in line else "latest"

    elif framework == "go":
        go_mod = project / "go.mod"
        if go_mod.exists():
            for line in go_mod.read_text().split("\n"):
                if line.startswith("go "):
                    return line.split()[1]

    elif framework == "node":
        package_json = project / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                return data.get("engines", {}).get("node", "latest")
            except:
                pass

    return "latest"


if __name__ == "__main__":
    import sys
    project = sys.argv[1] if len(sys.argv) > 1 else "."
    framework, info = detect_framework_from_harness(project)
    print(f"Framework: {framework}")
    print(f"Info: {json.dumps(info, indent=2)}")

