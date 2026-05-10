#!/usr/bin/env python3
"""
Gap 1: Multi-File Output Formatter

Formats multiple generated files into a single, clear response with:
1. Clear file boundaries and paths
2. Syntax highlighting
3. Installation instructions
4. File ordering (models → views → tests, etc.)
5. Summary of what was generated

Input: Dict[filepath: str, code: str], framework, feature_name
Output: Formatted markdown with all files, instructions, integration guide
"""

import json
from typing import Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path
import sys

# Shared library imports
sys.path.insert(0, str(Path(__file__).parent))
from lib.base_script import __version__, setup_logging, timed_run

__version__ = "0.7.0"
logger = setup_logging(__name__)


@dataclass
class GeneratedFile:
    """Represents a generated file."""
    filepath: str
    content: str
    file_type: str  # 'model', 'view', 'test', 'config', 'migration', 'doc'
    language: str  # 'python', 'javascript', 'java', 'sql', 'yaml', 'markdown'


def detect_language(filepath: str) -> str:
    """Detect language from file extension."""
    ext_to_lang = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.sql': 'sql',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json',
        '.md': 'markdown',
        '.go': 'go',
    }
    ext = filepath.split('.')[-1].lower()
    return ext_to_lang.get(f'.{ext}', 'python')


def detect_file_type(filepath: str) -> str:
    """Detect file type from path/name."""
    path_lower = filepath.lower()

    if 'model' in path_lower or 'entity' in path_lower:
        return 'model'
    elif 'view' in path_lower or 'controller' in path_lower or 'handler' in path_lower:
        return 'view'
    elif 'test' in path_lower:
        return 'test'
    elif 'migration' in path_lower:
        return 'migration'
    elif 'config' in path_lower or 'settings' in path_lower:
        return 'config'
    elif 'readme' in path_lower:
        return 'doc'
    elif 'serializer' in path_lower or 'dto' in path_lower:
        return 'schema'
    elif 'router' in path_lower or 'url' in path_lower:
        return 'routing'
    else:
        return 'code'


def sort_files_by_dependency(files: Dict[str, str]) -> List[Tuple[str, str]]:
    """
    Sort files by dependency order:
    1. Models/Entities first
    2. Schemas/Serializers
    3. Services/Business logic
    4. Views/Handlers/Controllers
    5. Routers/URLs
    6. Tests
    7. Configs
    8. Docs
    """
    priority = {
        'model': 0,
        'schema': 1,
        'config': 2,
        'code': 3,
        'view': 4,
        'routing': 5,
        'migration': 6,
        'test': 7,
        'doc': 8,
    }

    sorted_files = []
    for filepath, content in files.items():
        file_type = detect_file_type(filepath)
        priority_val = priority.get(file_type, 5)
        sorted_files.append((priority_val, filepath, content))

    sorted_files.sort(key=lambda x: (x[0], x[1]))  # Sort by priority, then filename
    return [(f[1], f[2]) for f in sorted_files]


def format_file_block(filepath: str, content: str) -> str:
    """Format a single file with syntax highlighting."""
    language = detect_language(filepath)

    return f"""### {filepath}

```{language}
{content}
```
"""


def generate_install_instructions(framework: str, files: List[str]) -> str:
    """Generate install/migration instructions based on framework."""

    has_migration = any('migration' in f.lower() for f in files)
    has_models = any('model' in f.lower() or 'entity' in f.lower() for f in files)

    instructions = []

    if framework == 'django':
        if has_models and has_migration:
            instructions.append("```bash")
            instructions.append("python manage.py migrate")
            instructions.append("```")
        elif has_models:
            instructions.append("```bash")
            instructions.append("python manage.py makemigrations")
            instructions.append("python manage.py migrate")
            instructions.append("```")

    elif framework == 'fastapi':
        instructions.append("```bash")
        instructions.append("# Ensure dependencies are installed:")
        instructions.append("pip install fastapi sqlalchemy pydantic")
        instructions.append("```")

    elif framework == 'spring':
        instructions.append("```bash")
        instructions.append("# If using Flyway migrations:")
        instructions.append("mvn flyway:migrate")
        instructions.append("```")

    elif framework == 'go':
        instructions.append("```bash")
        instructions.append("# Update go.mod and go.sum:")
        instructions.append("go mod tidy")
        instructions.append("```")

    return '\n'.join(instructions) if instructions else ""


def generate_integration_guide(framework: str, files: List[str], feature_name: str) -> str:
    """Generate step-by-step integration guide."""

    guide = f"## Integration Steps\n\n"

    steps = [
        f"1. **Create Files** — Copy each file below to its specified location",
        f"2. **Install Dependencies** (if any new imports added)",
        f"3. **Run Migrations** (if database schema changed)",
        f"4. **Run Tests** — `pytest`, `npm test`, or `mvn test`",
        f"5. **Verify** — Start server and test endpoints",
    ]

    guide += '\n'.join(steps) + '\n'

    return guide


class MultiFileFormatter:
    """Public API for multi-file output formatting."""

    def __init__(self, framework):
        """Initialize formatter for a specific framework."""
        self.framework = framework.lower()

    def format_multifile_response(self, files: Dict[str, str], feature_name: str = "Feature") -> str:
        """Format multiple generated files into a response."""
        return format_multifile_response(files, self.framework, feature_name)


def _normalize_files(files) -> Dict[str, str]:
    """Accept either a dict {path: content} or a list of dicts with 'name'/'content'/'type'.

    Returns a normalized dict {filepath: content}.
    """
    if isinstance(files, dict):
        return files
    if isinstance(files, list):
        normalized = {}
        for entry in files:
            if isinstance(entry, dict):
                # Support several common key spellings
                path = entry.get('name') or entry.get('filepath') or entry.get('path')
                content = entry.get('content', '')
                if path is not None:
                    normalized[path] = content
            elif isinstance(entry, (tuple, list)) and len(entry) >= 2:
                normalized[entry[0]] = entry[1]
        return normalized
    raise TypeError(f"Unsupported files type: {type(files).__name__}")


def format_multifile_response(files, framework: str, feature_name: str = "Feature") -> str:
    """
    Format multiple generated files into a single response.

    Args:
        files: Either a dict[filepath, code_content] or a list of dicts with
               keys 'name'/'filepath' and 'content' (plus optional 'type').
        framework: 'django', 'fastapi', 'spring', 'go', 'nodejs', etc.
        feature_name: Feature name (e.g., "User Authentication")

    Returns:
        Formatted markdown response with all files, instructions, guides
    """

    files = _normalize_files(files)

    # Sort files by dependency
    sorted_files = sort_files_by_dependency(files)

    # Build response
    response = f"# Generated {feature_name} Feature\n\n"

    response += f"**Framework:** {framework.title()}\n"
    response += f"**Files Generated:** {len(files)}\n\n"

    # File summary table
    response += "## Files to Create\n\n"
    response += "| File | Type | Language |\n"
    response += "|------|------|----------|\n"
    for filepath, _ in sorted_files:
        file_type = detect_file_type(filepath)
        language = detect_language(filepath)
        response += f"| `{filepath}` | {file_type} | {language} |\n"

    response += "\n"

    # Integration guide
    response += generate_integration_guide(framework, list(files.keys()), feature_name)
    response += "\n"

    # All file blocks
    response += "## File Contents\n\n"
    for filepath, content in sorted_files:
        response += format_file_block(filepath, content)

    # Installation instructions
    install_inst = generate_install_instructions(framework, list(files.keys()))
    if install_inst:
        response += "## Installation\n\n"
        response += install_inst
        response += "\n"

    # Run instructions
    response += "## Run\n\n"
    if framework == 'django':
        response += "```bash\n"
        response += "python manage.py runserver\n"
        response += "```\n"
    elif framework == 'fastapi':
        response += "```bash\n"
        response += "uvicorn main:app --reload\n"
        response += "```\n"
    elif framework == 'spring':
        response += "```bash\n"
        response += "mvn spring-boot:run\n"
        response += "```\n"
    elif framework == 'go':
        response += "```bash\n"
        response += "go run main.go\n"
        response += "```\n"

    return response


def main():
    """Test the formatter."""
    with timed_run("format_multifile_output") as timer:
        logger.debug("Starting multi-file formatter test")
        test_files = {
            "models.py": "class User(models.Model):\n    name = models.CharField(max_length=100)",
            "views.py": "@api_view(['GET'])\ndef get_users(request):\n    return Response({'users': []})",
            "tests.py": "def test_get_users():\n    assert True",
            "migrations/0001_initial.py": "# Auto-generated migration",
            "README.md": "# User Feature\nComplete user management system",
        }

        logger.debug(f"Formatting {len(test_files)} test files")
        result = format_multifile_response(test_files, "django", "User Management")
        print(result)

    logger.debug(f"format_multifile_output completed in {timer.elapsed_ms:.0f}ms")


if __name__ == '__main__':
    main()
