#!/usr/bin/env python3
"""
v0.7.0-v0.8.0 Feature-Discovery: Health Check

Runs a capability scan over a project and emits a compact report telling
the user *what this plugin can do for them given their codebase*. Builds on
top of `detect_message_bus.py` and `analyze_codebase.py`.

Usage:
    python health_check.py /path/to/project

Public API:
    checker = HealthChecker(project_root)
    report = checker.scan()
    print(checker.format_report(report))
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from detect_message_bus import MessageBusDetector


@dataclass
class CapabilityRow:
    label: str
    status: str  # 'ok' | 'warn' | 'missing'
    detail: str = ''


SKIP_DIRS = {'.git', 'node_modules', '__pycache__', 'venv', '.venv', 'target', 'build', 'dist'}


class HealthChecker:
    """Capability scanner. Reports what this plugin can generate for the project."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)

    # ---- public API --------------------------------------------------------

    def scan(self) -> Dict:
        framework = self._detect_framework()
        bus_info = MessageBusDetector(str(self.project_root)).detect()
        testing = self._detect_testing()
        logging_lib = self._detect_logging()
        iac = self._detect_iac()
        migrations = self._detect_migrations()

        rows: List[CapabilityRow] = []
        rows.append(CapabilityRow('Framework', 'ok' if framework else 'warn',
                                  framework or 'not detected — defaulting to Django'))
        rows.append(CapabilityRow('Message bus', 'ok' if bus_info['primary_bus'] != 'none' else 'warn',
                                  f"{bus_info['primary_bus']} (runtime: {bus_info['runtime']})"))
        rows.append(CapabilityRow('Testing', 'ok' if testing else 'missing',
                                  testing or 'no test config detected'))
        rows.append(CapabilityRow('Logging', 'ok' if logging_lib else 'warn',
                                  logging_lib or 'stdlib logging assumed'))
        rows.append(CapabilityRow('IaC / deployment', 'ok' if iac else 'missing',
                                  ', '.join(iac) if iac else 'no Dockerfile / k8s / Terraform found'))
        rows.append(CapabilityRow('DB migrations', 'ok' if migrations else 'warn',
                                  migrations or 'no migration tool detected'))

        capabilities = self._capabilities_unlocked(framework, bus_info, testing, iac, migrations)

        return {
            'project_root': str(self.project_root),
            'framework': framework,
            'bus': bus_info,
            'testing': testing,
            'logging': logging_lib,
            'iac': iac,
            'migrations': migrations,
            'rows': [row.__dict__ for row in rows],
            'capabilities_unlocked': capabilities,
            'recommendations': self._recommendations(framework, bus_info, testing, logging_lib),
        }

    def format_report(self, report: Dict) -> str:
        lines = ["# Health Check Report\n",
                 f"Project: `{report['project_root']}`\n"]
        lines.append("## Capability Summary")
        for row in report['rows']:
            icon = {'ok': '[ok]', 'warn': '[warn]', 'missing': '[missing]'}[row['status']]
            lines.append(f"- {icon} {row['label']}: {row['detail']}")
        lines.append('')

        lines.append("## What this plugin can generate for you")
        for cap in report['capabilities_unlocked']:
            lines.append(f"- {cap}")
        lines.append('')

        if report['recommendations']:
            lines.append("## Recommendations")
            for rec in report['recommendations']:
                lines.append(f"- {rec}")
        return '\n'.join(lines)

    # ---- internals ---------------------------------------------------------

    def _detect_framework(self) -> str:
        signals = {
            'django':   ['manage.py', 'wsgi.py', 'asgi.py'],
            'fastapi':  ['main.py'],
            'spring':   ['pom.xml', 'build.gradle', 'application.properties'],
            'express':  ['package.json'],
            'go':       ['go.mod', 'main.go'],
        }

        for fw, files in signals.items():
            for f in files:
                if (self.project_root / f).exists():
                    if fw == 'fastapi':
                        # Distinguish FastAPI from generic main.py via content sniff
                        try:
                            text = (self.project_root / f).read_text(encoding='utf-8', errors='replace')
                            if 'fastapi' in text.lower():
                                return 'fastapi'
                        except Exception:
                            pass
                        continue
                    if fw == 'express':
                        try:
                            data = json.loads((self.project_root / f).read_text(encoding='utf-8'))
                            deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                            if 'express' in deps or '@nestjs/core' in deps:
                                return 'nestjs' if '@nestjs/core' in deps else 'express'
                        except Exception:
                            pass
                        continue
                    return fw
        return ''

    def _detect_testing(self) -> str:
        candidates = [
            ('pytest',   ['pytest.ini', 'pyproject.toml', 'conftest.py']),
            ('unittest', ['tests/__init__.py']),
            ('jest',     ['jest.config.js', 'jest.config.ts']),
            ('junit',    ['pom.xml', 'build.gradle']),
            ('go test',  ['go.mod']),
        ]
        for label, files in candidates:
            for f in files:
                path = self.project_root / f
                if path.exists():
                    try:
                        if label == 'pytest' and f == 'pyproject.toml':
                            text = path.read_text(encoding='utf-8', errors='replace')
                            if 'pytest' not in text:
                                continue
                    except Exception:
                        continue
                    return label
        return ''

    def _detect_logging(self) -> str:
        for path in self._iter_files(extensions={'.py', '.js', '.ts', '.go', '.java'}, limit=120):
            try:
                content = path.read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue
            if 'structlog' in content:
                return 'structlog'
            if 'loguru' in content:
                return 'loguru'
            if 'winston' in content:
                return 'winston'
            if 'pino' in content:
                return 'pino'
            if 'zap' in content and self._likely_go(path):
                return 'zap'
            if 'logrus' in content and self._likely_go(path):
                return 'logrus'
            if re.search(r'import\s+logging', content):
                return 'stdlib logging'
        return ''

    def _detect_iac(self) -> List[str]:
        out = []
        candidates = {
            'Dockerfile': ['Dockerfile'],
            'docker-compose': ['docker-compose.yml', 'docker-compose.yaml'],
            'kubernetes':    ['k8s/', 'kubernetes/'],
            'terraform':     ['terraform/', 'main.tf'],
            'github-actions':['.github/workflows/'],
            'gitlab-ci':     ['.gitlab-ci.yml'],
        }
        for label, paths in candidates.items():
            for p in paths:
                target = self.project_root / p
                if target.exists():
                    out.append(label)
                    break
        return out

    def _detect_migrations(self) -> str:
        if (self.project_root / 'manage.py').exists():
            return 'django migrations'
        if (self.project_root / 'alembic.ini').exists():
            return 'alembic'
        if any((self.project_root / d).exists() for d in ('migrations', 'db/migrations', 'src/main/resources/db/migration')):
            return 'flyway / generic'
        if (self.project_root / 'go.mod').exists() and any((self.project_root / 'migrations').glob('*.sql')):
            return 'golang-migrate'
        return ''

    def _capabilities_unlocked(self, framework, bus_info, testing, iac, migrations) -> List[str]:
        caps = ['Generate complete features (models + views + tests + README)']
        if framework:
            caps.append(f'Framework-correct {framework} code (matches your file layout)')
        if bus_info['primary_bus'] != 'none':
            caps.append(f'Event handlers for {bus_info["primary_bus"]} that wire into your existing bus')
        if testing:
            caps.append(f'Tests using your detected framework: {testing}')
        if iac:
            caps.append(f'Deployment artefacts ({", ".join(iac)})')
        if migrations:
            caps.append(f'Database migrations using {migrations}')
        caps.append('Optional automated review (--review) and TDD (--tdd) modes')
        caps.append('Optional preview (--preview) before committing to full generation')
        return caps

    def _recommendations(self, framework, bus_info, testing, logging_lib) -> List[str]:
        out = []
        if not framework:
            out.append('Run with `@/path/to/your/project` so the analyzer can pick up framework signals.')
        if not testing:
            out.append('No test config detected — generated tests will assume pytest by default.')
        if logging_lib in ('', 'stdlib logging'):
            out.append('Consider structlog for structured logging — improves observability for free.')
        if bus_info['primary_bus'] == 'none':
            out.append('No message bus detected — generated event handlers will use asyncio queues '
                       'as a placeholder; replace with Kafka / RabbitMQ before production.')
        return out

    def _iter_files(self, extensions, limit=200):
        count = 0
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in extensions:
                    count += 1
                    if count > limit:
                        return
                    yield Path(root) / f

    @staticmethod
    def _likely_go(path: Path) -> bool:
        return path.suffix == '.go'


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python health_check.py <project_root>")
        sys.exit(1)
    checker = HealthChecker(sys.argv[1])
    report = checker.scan()
    print(checker.format_report(report))


if __name__ == '__main__':
    main()
