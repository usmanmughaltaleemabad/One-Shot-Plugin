#!/usr/bin/env python3
"""
v0.10.0: Automated Code Review Gates

Runs lint / security / performance / type / test-coverage checks against
generated code and emits a report. The user can override with ``--force``,
but by default critical security findings block generation.

Public API:
    reviewer = CodeReviewer(framework='django', language='python')
    report = reviewer.review(code, filepath='users/views.py')
    # -> {
    #      'overall': 'PASS' | 'WARN' | 'BLOCK',
    #      'linting': {...},
    #      'security': {...},
    #      'performance': {...},
    #      'type_coverage': {...},
    #      'test_coverage': {...},
    #    }
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Finding:
    rule: str
    severity: str  # 'block' | 'warn' | 'info'
    message: str
    line: Optional[int] = None


@dataclass
class ReviewSection:
    name: str
    status: str = 'PASS'  # PASS | WARN | BLOCK
    findings: List[Finding] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'status': self.status,
            'findings': [
                {'rule': f.rule, 'severity': f.severity, 'message': f.message, 'line': f.line}
                for f in self.findings
            ],
        }


SECRETS_PATTERNS = [
    (r'(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*[\'"][A-Za-z0-9_\-]{12,}[\'"]', 'hardcoded credential'),
    (r'AKIA[0-9A-Z]{16}', 'AWS access key id'),
    (r'(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}', 'bearer token literal'),
    (r'-----BEGIN (RSA |EC )?PRIVATE KEY-----', 'private key in source'),
]

SQL_INJECTION_PATTERNS = [
    (r'cursor\.execute\s*\(\s*[fF]?[\'"].*\{.*\}.*[\'"]', 'f-string used in SQL'),
    (r'cursor\.execute\s*\(\s*[\'"].*\%s.*[\'"]\s*\%\s*', '% string formatting in SQL'),
    (r'cursor\.execute\s*\(\s*[\'"][^\'"\)]*[\'"]\s*\+\s*\w', 'string concat in SQL'),
]

COMMAND_INJECTION_PATTERNS = [
    (r'os\.system\s*\(', 'os.system() — prefer subprocess with list args'),
    (r'subprocess\.\w+\([^)]*shell\s*=\s*True', 'subprocess shell=True'),
    (r'eval\s*\(', 'eval() — never on untrusted input'),
    (r'exec\s*\(', 'exec() — never on untrusted input'),
]

BLOCKING_IN_ASYNC_PATTERNS = [
    (r'async\s+def[\s\S]*?\btime\.sleep\(', 'time.sleep() inside async def'),
    (r'async\s+def[\s\S]*?\brequests\.(get|post|put|delete)\(', 'sync requests.* inside async def'),
    (r'async\s+def[\s\S]*?\.execute\(', 'sync DB execute inside async def (use async driver)'),
]


class CodeReviewer:
    """Runs review gates across security / performance / typing / linting."""

    def __init__(self, framework: str = 'unknown', language: str = 'python', strict: bool = False):
        self.framework = framework.lower()
        self.language = language.lower()
        self.strict = strict

    def review(self, code: str, filepath: str = '<generated>') -> Dict:
        sections = [
            self._linting(code),
            self._security(code),
            self._performance(code),
            self._type_coverage(code),
            self._test_coverage(code, filepath),
        ]

        # Roll up
        worst = 'PASS'
        for s in sections:
            if s.status == 'BLOCK':
                worst = 'BLOCK'
                break
            if s.status == 'WARN' and worst == 'PASS':
                worst = 'WARN'

        return {
            'overall': worst,
            'filepath': filepath,
            'framework': self.framework,
            'language': self.language,
            'sections': {s.name: s.to_dict() for s in sections},
        }

    # ---- gates -------------------------------------------------------------

    def _linting(self, code: str) -> ReviewSection:
        section = ReviewSection(name='linting')

        if self.language == 'python':
            for ln, line in enumerate(code.splitlines(), 1):
                if len(line) > 120:
                    section.findings.append(Finding('line-too-long', 'warn',
                                                    f'line exceeds 120 chars ({len(line)})', ln))
                if line.rstrip() != line and line.strip():
                    section.findings.append(Finding('trailing-whitespace', 'info',
                                                    'trailing whitespace', ln))
            # Mixed tabs/spaces
            if '\t' in code and re.search(r'^ +', code, re.MULTILINE):
                section.findings.append(Finding('mixed-indent', 'warn',
                                                'mixed tabs and spaces'))

        if any(f.severity == 'block' for f in section.findings):
            section.status = 'BLOCK'
        elif section.findings:
            section.status = 'WARN'
        return section

    def _security(self, code: str) -> ReviewSection:
        section = ReviewSection(name='security')

        for pattern, desc in SECRETS_PATTERNS:
            for m in re.finditer(pattern, code):
                section.findings.append(Finding('hardcoded-secret', 'block',
                                                f'{desc}: {m.group(0)[:40]}…',
                                                self._line_of(code, m.start())))

        for pattern, desc in SQL_INJECTION_PATTERNS:
            for m in re.finditer(pattern, code):
                section.findings.append(Finding('sql-injection', 'block', desc,
                                                self._line_of(code, m.start())))

        for pattern, desc in COMMAND_INJECTION_PATTERNS:
            for m in re.finditer(pattern, code):
                section.findings.append(Finding('command-injection', 'block', desc,
                                                self._line_of(code, m.start())))

        if any(f.severity == 'block' for f in section.findings):
            section.status = 'BLOCK'
        elif section.findings:
            section.status = 'WARN'
        return section

    def _performance(self, code: str) -> ReviewSection:
        section = ReviewSection(name='performance')

        for pattern, desc in BLOCKING_IN_ASYNC_PATTERNS:
            if re.search(pattern, code):
                section.findings.append(Finding('blocking-in-async', 'warn', desc))

        # N+1 heuristic: ORM call inside a loop
        if re.search(r'for\s+\w+\s+in\s+[^\n]+:\s*\n[^\n]*\.objects\.(get|filter|all)\(', code):
            section.findings.append(Finding('possible-n-plus-one', 'warn',
                                            'ORM call inside loop — consider select_related/prefetch_related'))

        if section.findings:
            section.status = 'WARN'
        return section

    def _type_coverage(self, code: str) -> ReviewSection:
        section = ReviewSection(name='type_coverage')

        if self.language != 'python':
            return section  # Only meaningful for Python here

        defs = re.findall(r'def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*[^:]+)?:', code)
        if not defs:
            return section

        annotated = 0
        for name, params in defs:
            # Treat `self`/`cls` as auto-typed
            param_list = [p.strip() for p in params.split(',') if p.strip() and p.strip() not in ('self', 'cls')]
            if not param_list:
                annotated += 1
                continue
            if all(':' in p or '=' in p for p in param_list):
                annotated += 1

        coverage = annotated / len(defs)
        if coverage < 0.6:
            section.findings.append(Finding('low-type-coverage', 'warn',
                                            f'only {coverage:.0%} of functions have annotations'))
            section.status = 'WARN'
        return section

    def _test_coverage(self, code: str, filepath: str) -> ReviewSection:
        section = ReviewSection(name='test_coverage')

        is_test_file = 'test' in filepath.lower()
        if is_test_file:
            n_tests = len(re.findall(r'def\s+test_\w+', code)) + len(re.findall(r'@Test\b', code))
            if n_tests < 2:
                section.findings.append(Finding('insufficient-tests', 'warn',
                                                f'only {n_tests} test(s) found; recommend ≥2'))
                section.status = 'WARN'
        return section

    @staticmethod
    def _line_of(code: str, offset: int) -> int:
        return code.count('\n', 0, offset) + 1


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python code_review_automation.py <file>")
        sys.exit(1)
    path = sys.argv[1]
    with open(path, 'r', encoding='utf-8') as f:
        code = f.read()
    reviewer = CodeReviewer()
    report = reviewer.review(code, filepath=path)
    import json
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
