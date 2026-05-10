#!/usr/bin/env python3
"""
Auto-wire generated code into existing projects.

Injects generated files at correct locations respecting framework conventions.
Creates backups and flags merge conflicts.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


class ProjectAutowire:
    """Auto-inject generated code into projects."""

    FRAMEWORK_MARKERS = {
        'django': ['manage.py', 'settings.py', 'wsgi.py'],
        'fastapi': ['main.py', 'app/', 'fastapi'],
        'nestjs': ['package.json', 'src/', 'nest-cli.json'],
        'express': ['package.json', 'server.js', 'app.js', 'index.js'],
        'spring': ['pom.xml', 'build.gradle', 'src/main/java'],
    }

    PATHS = {
        'django': {
            'models': '{app}/models.py',
            'views': '{app}/views.py',
            'serializers': '{app}/serializers.py',
            'tests': '{app}/tests.py',
            'migrations': '{app}/migrations',
        },
        'fastapi': {
            'models': 'app/models.py',
            'routes': 'app/routes/',
            'schemas': 'app/schemas.py',
            'tests': 'tests/',
        },
        'nestjs': {
            'models': 'src/models/',
            'controllers': 'src/{module}/controllers/',
            'services': 'src/{module}/services/',
            'tests': 'src/{module}/*.spec.ts',
        },
        'express': {
            'models': 'src/models/',
            'routes': 'src/routes/',
            'middleware': 'src/middleware/',
            'tests': 'test/',
        },
        'spring': {
            'entities': 'src/main/java/entities/',
            'controllers': 'src/main/java/controllers/',
            'services': 'src/main/java/services/',
            'tests': 'src/test/java/',
        },
    }

    def __init__(self, project_root: str, framework: str = None):
        self.project_root = Path(project_root)
        self.framework = framework or self._detect_framework()
        self.backup_dir = self.project_root / '.backup'
        self.conflicts = []

    def _detect_framework(self) -> str:
        """Auto-detect framework from project markers."""
        for fw, markers in self.FRAMEWORK_MARKERS.items():
            for marker in markers:
                if (self.project_root / marker).exists():
                    return fw
        return 'django'  # default

    def _create_backup(self, filepath: Path) -> None:
        """Create backup of original file."""
        if not filepath.exists():
            return

        self.backup_dir.mkdir(exist_ok=True)
        rel_path = filepath.relative_to(self.project_root)
        backup_path = self.backup_dir / rel_path

        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(filepath, backup_path)

    def _merge_file(self, filepath: Path, new_content: str) -> bool:
        """
        Merge new content into existing file.

        Returns True if successful, False if conflict detected.
        """
        if not filepath.exists():
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(new_content)
            return True

        self._create_backup(filepath)
        existing = filepath.read_text()

        # Check if new content already exists
        if new_content in existing:
            return True  # Already present

        # Python files: append functions/classes
        if filepath.suffix == '.py':
            if existing.endswith('\n'):
                filepath.write_text(existing + '\n' + new_content)
            else:
                filepath.write_text(existing + '\n\n' + new_content)
            return True

        # JavaScript/TypeScript: append exports
        if filepath.suffix in ['.js', '.ts']:
            filepath.write_text(existing + '\n' + new_content)
            return True

        # Default: flag conflict
        self.conflicts.append(str(filepath))
        return False

    def autowire(self, files: Dict[str, str]) -> Dict[str, any]:
        """
        Auto-wire files into project.

        Args:
            files: Dict mapping filepath -> code content

        Returns:
            Report with success/conflict status
        """
        created = []
        updated = []
        conflicts = []

        for filepath, content in files.items():
            target_path = self.project_root / filepath

            target_path.parent.mkdir(parents=True, exist_ok=True)

            if target_path.exists():
                if self._merge_file(target_path, content):
                    updated.append(str(target_path))
                else:
                    conflicts.append(str(target_path))
            else:
                target_path.write_text(content)
                created.append(str(target_path))

        return {
            'framework': self.framework,
            'created': created,
            'updated': updated,
            'conflicts': conflicts,
            'backup_dir': str(self.backup_dir),
            'status': 'success' if not conflicts else 'partial',
        }


def autowire_into_project(
    project_root: str,
    files: Dict[str, str],
    framework: str = None
) -> Dict[str, any]:
    """Auto-wire files into project."""
    autowire = ProjectAutowire(project_root, framework)
    return autowire.autowire(files)
