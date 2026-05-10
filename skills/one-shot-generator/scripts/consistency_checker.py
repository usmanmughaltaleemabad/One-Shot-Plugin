#!/usr/bin/env python3
"""
v1.4.1: Cross-Codebase Consistency Checker

Once a project has 5+ generated handlers, they tend to drift: handler A uses
Pydantic, B uses dataclass, error handling diverges, logging libraries
differ. This module scans a project, reports inconsistencies, and produces
a refactor proposal that pulls shared types/logging/error handling into a
common library.

Public API:
    checker = ConsistencyChecker(project_root='.')
    report = checker.check()
    plan = checker.standardize(target_library='shared_handlers')
"""

from __future__ import annotations

import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


SCANNABLE_EXTS = {'.py', '.ts', '.js', '.go', '.java'}
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', 'venv', '.venv', 'target', 'build', 'dist'}


SERIALIZER_PATTERNS = {
    'pydantic':   [r'from\s+pydantic\s+import', r'BaseModel\s*\)'],
    'dataclass':  [r'@dataclass', r'from\s+dataclasses\s+import'],
    'attrs':      [r'@attr\.', r'import\s+attrs'],
    'marshmallow':[r'from\s+marshmallow\s+import', r'\bSchema\b'],
}

LOGGING_PATTERNS = {
    'structlog':  [r'import\s+structlog', r'structlog\.get_logger'],
    'stdlib':     [r'import\s+logging', r'logging\.getLogger'],
    'loguru':     [r'from\s+loguru\s+import\s+logger'],
    'print':      [r'print\s*\('],
}

ERROR_HANDLING_PATTERNS = {
    'try_except': [r'try:\s*\n', r'except\s+\w+'],
    'result_obj': [r'Result\[', r'Either\['],
    'unhandled':  [r'raise\s+\w+'],
}


class ConsistencyChecker:
    """Scan a project for stylistic inconsistencies across modules."""

    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root)

    # ---- public API --------------------------------------------------------

    def check(self) -> Dict:
        files = list(self._iter_source_files())
        per_file = {f: self._inspect(f) for f in files}

        # Aggregate
        totals = {
            'serializers': Counter(),
            'logging':     Counter(),
            'error':       Counter(),
        }
        for fp, info in per_file.items():
            for axis, label in (('serializers', info['serializer']),
                                ('logging', info['logging']),
                                ('error', info['error'])):
                if label:
                    totals[axis][label] += 1

        inconsistencies = []
        for axis, counts in totals.items():
            if len(counts) > 1:
                top, top_count = counts.most_common(1)[0]
                others = {k: v for k, v in counts.items() if k != top}
                inconsistencies.append({
                    'axis': axis,
                    'dominant': top,
                    'dominant_count': top_count,
                    'minorities': others,
                    'severity': 'WARN' if top_count >= sum(others.values()) else 'BLOCK',
                })

        return {
            'files_scanned': len(files),
            'totals': {k: dict(v) for k, v in totals.items()},
            'inconsistencies': inconsistencies,
            'per_file': {str(p.relative_to(self.project_root)): info for p, info in per_file.items()},
        }

    def standardize(self, target_library: str = 'shared_handlers') -> Dict[str, str]:
        """Produce skeletons for the shared library + import-rewrite hints."""
        report = self.check()
        files: Dict[str, str] = {}

        files[f'{target_library}/__init__.py'] = (
            f'"""Shared library extracted by ConsistencyChecker."""\n'
            'from .dto import *  # noqa: F401,F403\n'
            'from .logging_config import get_logger  # noqa: F401\n'
            'from .errors import HandlerError  # noqa: F401\n'
        )

        files[f'{target_library}/dto.py'] = self._dto_module(report)
        files[f'{target_library}/logging_config.py'] = self._logging_module(report)
        files[f'{target_library}/errors.py'] = self._errors_module()
        files[f'{target_library}/MIGRATION_NOTES.md'] = self._migration_notes(report, target_library)
        return files

    # ---- internals ---------------------------------------------------------

    def _iter_source_files(self):
        for root, dirs, fnames in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in fnames:
                if os.path.splitext(f)[1].lower() in SCANNABLE_EXTS:
                    yield Path(root) / f

    def _inspect(self, path: Path) -> Dict:
        try:
            content = path.read_text(encoding='utf-8', errors='replace')
        except Exception:
            return {'serializer': None, 'logging': None, 'error': None}

        return {
            'serializer': self._first_match(content, SERIALIZER_PATTERNS),
            'logging':    self._first_match(content, LOGGING_PATTERNS),
            'error':      self._first_match(content, ERROR_HANDLING_PATTERNS),
        }

    @staticmethod
    def _first_match(text: str, patterns: Dict[str, List[str]]):
        for label, pats in patterns.items():
            if any(re.search(p, text) for p in pats):
                return label
        return None

    @staticmethod
    def _dto_module(report: Dict) -> str:
        ser = report['totals'].get('serializers', {})
        winner = max(ser, key=ser.get) if ser else 'pydantic'
        if winner == 'dataclass':
            return ('"""Canonical DTO base — dataclass."""\n'
                    'from dataclasses import dataclass\n\n'
                    '@dataclass\n'
                    'class BaseDTO:\n'
                    '    pass\n')
        # default to pydantic
        return ('"""Canonical DTO base — pydantic."""\n'
                'from pydantic import BaseModel\n\n'
                'class BaseDTO(BaseModel):\n'
                '    class Config:\n'
                '        extra = "forbid"\n')

    @staticmethod
    def _logging_module(report: Dict) -> str:
        lg = report['totals'].get('logging', {})
        winner = max(lg, key=lg.get) if lg else 'structlog'
        if winner == 'structlog':
            return ('"""Canonical logger factory — structlog."""\n'
                    'import structlog\n\n'
                    'def get_logger(name: str = "app"):\n'
                    '    return structlog.get_logger(name)\n')
        return ('"""Canonical logger factory — stdlib."""\n'
                'import logging\n\n'
                'def get_logger(name: str = "app") -> logging.Logger:\n'
                '    return logging.getLogger(name)\n')

    @staticmethod
    def _errors_module() -> str:
        return ('"""Canonical error hierarchy."""\n\n'
                'class HandlerError(Exception):\n'
                '    """Base class for all handler-level failures."""\n\n'
                'class ValidationError(HandlerError):\n'
                '    pass\n\n'
                'class TransientError(HandlerError):\n'
                '    """Worth retrying — downstream is temporarily unhealthy."""\n\n'
                'class FatalError(HandlerError):\n'
                '    """Stop processing — escalate to a human."""\n')

    @staticmethod
    def _migration_notes(report: Dict, target_library: str) -> str:
        lines = [f'# Migration notes — extracted by ConsistencyChecker',
                 '',
                 f'`{target_library}/` consolidates the dominant patterns.',
                 '',
                 '## Inconsistencies detected']
        for inc in report.get('inconsistencies', []):
            lines.append(f"- **{inc['axis']}**: dominant `{inc['dominant']}` ({inc['dominant_count']}); "
                         f"minorities {inc['minorities']}")
        lines.extend([
            '',
            '## Suggested rewrite',
            f'1. Replace ad-hoc imports with `from {target_library} import ...`.',
            f'2. Remove duplicated DTO base classes / loggers / error types.',
            '3. Run the parity test in `tests/test_strangler_parity.py` after rewriting.',
        ])
        return '\n'.join(lines)


def main():
    import json, sys
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    checker = ConsistencyChecker(root)
    print(json.dumps(checker.check(), indent=2, default=str))


if __name__ == '__main__':
    main()
