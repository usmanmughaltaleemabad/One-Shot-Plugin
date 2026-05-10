#!/usr/bin/env python3
"""
Format and order multi-file code output by dependency graph.

Organizes generated files respecting:
1. Layer ordering (models before views before tests)
2. Import dependencies (if detectable)
3. Framework conventions (Django, FastAPI, NestJS, Express, Spring)
"""

import re
from typing import Dict, List, Tuple, Set
from collections import defaultdict


class MultiFileFormatter:
    """Orders generated code files by dependency graph."""

    LAYER_ORDER = {
        'model': 0, 'models': 0, 'entity': 0, 'entities': 0,
        'schema': 1, 'dto': 1, 'types': 1,
        'config': 2, 'settings': 2,
        'service': 3, 'services': 3, 'handler': 3, 'handlers': 3,
        'route': 4, 'routes': 4, 'controller': 4, 'controllers': 4,
        'view': 4, 'views': 4, 'api': 4,
        'middleware': 5, 'interceptor': 5, 'filter': 5,
        'util': 6, 'utils': 6, 'helper': 6, 'helpers': 6,
        'test': 7, 'tests': 7, 'spec': 7,
        'migration': 8, 'migrations': 8,
    }

    def __init__(self, files: Dict[str, str], framework: str = 'django'):
        self.files = files
        self.framework = framework.lower()
        self.dependencies: Dict[str, Set[str]] = self._detect_dependencies()

    def _get_file_basename(self, filepath: str) -> str:
        """Get filename without path and extension."""
        name = filepath.split('/')[-1]  # Remove path
        name = name.split('.')[0]  # Remove extension
        return name

    def _detect_dependencies(self) -> Dict[str, Set[str]]:
        """Detect which files depend on which other files."""
        deps = defaultdict(set)
        files_list = list(self.files.keys())
        basenames = {f: self._get_file_basename(f) for f in files_list}

        for filepath, code in self.files.items():
            for other_file in files_list:
                if filepath == other_file:
                    continue

                other_basename = basenames[other_file]

                # Check if filepath imports from other_file
                patterns = [
                    rf'from .{other_basename} import',
                    rf'from {other_basename} import',
                    rf'import {other_basename}',
                    rf'require\([\'"].*{other_basename}',
                    rf'from.*{other_basename}',
                ]

                if any(re.search(pattern, code, re.IGNORECASE) for pattern in patterns):
                    deps[filepath].add(other_file)

        return dict(deps)

    def _get_layer_priority(self, filepath: str) -> int:
        """Get sort priority based on layer (lower = earlier)."""
        for keyword, priority in self.LAYER_ORDER.items():
            if keyword in filepath.lower():
                return priority
        return 999

    def _topological_sort(self) -> List[str]:
        """Sort files by dependency."""
        files = list(self.files.keys())

        # Build reverse dependency graph (what depends on me)
        reverse_deps = defaultdict(set)
        in_degree = defaultdict(int)

        for f in files:
            in_degree[f] = 0

        for file_a, deps in self.dependencies.items():
            for file_b in deps:
                reverse_deps[file_b].add(file_a)
                in_degree[file_a] += 1

        # Kahn's algorithm
        queue = [f for f in files if in_degree[f] == 0]
        sorted_files = []

        while queue:
            # Sort by layer priority within same level
            queue.sort(key=self._get_layer_priority)
            node = queue.pop(0)
            sorted_files.append(node)

            for dependent in reverse_deps.get(node, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(sorted_files) != len(files):
            # Circular dependency or issue - fall back to layer-based sorting
            return sorted(files, key=self._get_layer_priority)

        return sorted_files

    def format(self) -> List[Tuple[str, str]]:
        """Format files in dependency order."""
        if not self.files:
            return []

        sorted_files = self._topological_sort()
        return [(f, self.files[f]) for f in sorted_files]


def format_multifile_output(files: Dict[str, str], framework: str = 'django') -> List[Tuple[str, str]]:
    """Format generated files in dependency order."""
    formatter = MultiFileFormatter(files, framework)
    return formatter.format()
