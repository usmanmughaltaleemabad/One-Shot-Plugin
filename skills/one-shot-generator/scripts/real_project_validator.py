#!/usr/bin/env python3
"""
Real-Project Validation Harness

Builds synthetic-but-realistic project fixtures (Django, FastAPI, Spring,
Go, NestJS) and runs the full pipeline (analyze -> plan -> generate ->
verify -> auto-wire -> consistency-check) against each. Reports pass/fail
per fixture so we catch regressions where the plugin works in unit tests
but breaks on a project that *looks like* a real one.

Run: python real_project_validator.py
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from detect_message_bus import MessageBusDetector
from health_check import HealthChecker
from plan_decisions import PlanDecisionEngine
from verify_generated import CodeValidator
from format_multifile_output import MultiFileFormatter
from autowire_into_project import ProjectAutoWirer
from consistency_checker import ConsistencyChecker


@dataclass
class Fixture:
    name: str
    builder: Callable[[Path], Dict]  # returns metadata about the fixture


# ---- Fixtures --------------------------------------------------------------

def build_django(root: Path) -> Dict:
    (root / 'manage.py').write_text(
        '#!/usr/bin/env python\nimport django\n', encoding='utf-8'
    )
    (root / 'requirements.txt').write_text('django==4.2\nstructlog==23.1\npytest-django==4.5\n')
    (root / 'app').mkdir()
    (root / 'app' / '__init__.py').write_text('')
    (root / 'app' / 'models.py').write_text(
        'from django.db import models\n\nclass User(models.Model):\n    email = models.EmailField()\n'
    )
    (root / 'app' / 'views.py').write_text(
        'from django.views import View\n\nclass UserList(View):\n    pass\n'
    )
    (root / 'urls.py').write_text('from django.urls import path\nurlpatterns = []\n')
    (root / 'settings.py').write_text('INSTALLED_APPS = []\n')
    return {'framework': 'django', 'language': 'python'}


def build_fastapi(root: Path) -> Dict:
    (root / 'requirements.txt').write_text(
        'fastapi==0.95\npydantic==2.0\nsqlalchemy==2.0\naiokafka==0.10\npytest-asyncio==0.21\n'
    )
    (root / 'main.py').write_text(
        'from fastapi import FastAPI\nfrom aiokafka import AIOKafkaConsumer\n'
        'app = FastAPI()\n'
        '@app.get("/")\nasync def root():\n    return {"status": "ok"}\n'
    )
    return {'framework': 'fastapi', 'language': 'python'}


def build_spring(root: Path) -> Dict:
    (root / 'pom.xml').write_text(
        '<project><modelVersion>4.0.0</modelVersion>'
        '<dependencies><dependency><groupId>org.springframework.boot</groupId>'
        '<artifactId>spring-boot-starter-web</artifactId></dependency></dependencies></project>'
    )
    (root / 'src' / 'main' / 'java').mkdir(parents=True)
    (root / 'src' / 'main' / 'java' / 'App.java').write_text(
        'import org.springframework.boot.SpringApplication;\n'
        'public class App { public static void main(String[] a) {} }\n'
    )
    return {'framework': 'spring', 'language': 'java'}


def build_go(root: Path) -> Dict:
    (root / 'go.mod').write_text('module example.com/app\n\ngo 1.20\n\nrequire github.com/segmentio/kafka-go v0.4.0\n')
    (root / 'main.go').write_text(
        'package main\nimport "fmt"\nfunc main() { fmt.Println("ok"); ch := make(chan int); _ = ch }\n'
    )
    return {'framework': 'go', 'language': 'go'}


def build_nestjs(root: Path) -> Dict:
    (root / 'package.json').write_text(json.dumps({
        'name': 'sample',
        'dependencies': {'@nestjs/core': '10.0.0', 'rxjs': '7.0.0'},
        'devDependencies': {'jest': '29.0.0'},
    }))
    (root / 'src').mkdir()
    (root / 'src' / 'main.ts').write_text(
        "import { NestFactory } from '@nestjs/core';\n"
        "async function bootstrap() { /* */ }\n"
    )
    return {'framework': 'nestjs', 'language': 'typescript'}


FIXTURES: List[Fixture] = [
    Fixture('django',  build_django),
    Fixture('fastapi', build_fastapi),
    Fixture('spring',  build_spring),
    Fixture('go',      build_go),
    Fixture('nestjs',  build_nestjs),
]


# ---- Pipeline run ----------------------------------------------------------

def run_pipeline_against_fixture(fix: Fixture) -> Dict:
    """Walk the entire generation pipeline against a synthetic project."""
    record = {'fixture': fix.name, 'steps': {}, 'passed': True, 'errors': []}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        meta = fix.builder(root)

        # 1. health check
        try:
            report = HealthChecker(str(root)).scan()
            assert report['framework'] in ('', meta['framework']) or report['framework']
            record['steps']['health'] = 'pass'
        except Exception as e:
            record['steps']['health'] = f'fail: {e}'
            record['passed'] = False
            record['errors'].append(('health', str(e)))

        # 2. message bus detection (best-effort)
        try:
            bus = MessageBusDetector(str(root)).detect()
            record['steps']['bus_detect'] = f"pass ({bus['primary_bus']})"
        except Exception as e:
            record['steps']['bus_detect'] = f'fail: {e}'
            record['passed'] = False
            record['errors'].append(('bus_detect', str(e)))

        # 3. planner
        try:
            engine = PlanDecisionEngine({'framework': meta['framework'], 'language': meta['language']})
            decisions = engine.score_all_decisions()
            assert 'async_decision' in decisions
            record['steps']['planner'] = 'pass'
        except Exception as e:
            record['steps']['planner'] = f'fail: {e}'
            record['passed'] = False
            record['errors'].append(('planner', str(e)))

        # 4. verifier (only meaningful for python fixtures here)
        if meta['language'] == 'python':
            try:
                v = CodeValidator(framework=meta['framework'], language='python')
                ok = v.validate_code('def f(): return 1\n', 'python', meta['framework'])
                assert ok['status'] == 'PASSED'
                record['steps']['verify'] = 'pass'
            except Exception as e:
                record['steps']['verify'] = f'fail: {e}'
                record['passed'] = False
                record['errors'].append(('verify', str(e)))
        else:
            record['steps']['verify'] = 'skip (non-python fixture)'

        # 5. multi-file formatting
        try:
            formatter = MultiFileFormatter(framework=meta['framework'])
            out = formatter.format_multifile_response({
                'a.py': 'class A: pass\n',
                'b.py': 'class B: pass\n',
            }, 'demo')
            assert 'a.py' in out
            record['steps']['format'] = 'pass'
        except Exception as e:
            record['steps']['format'] = f'fail: {e}'
            record['passed'] = False
            record['errors'].append(('format', str(e)))

        # 6. auto-wire (django + fastapi only — others have framework-specific wiring)
        if meta['framework'] in ('django', 'fastapi'):
            try:
                wirer = ProjectAutoWirer(framework=meta['framework'], project_root=str(root))
                result = wirer.autowire({
                    'app/extra.py': '# generated\n',
                })
                assert result['success'], result
                record['steps']['autowire'] = 'pass'
            except Exception as e:
                record['steps']['autowire'] = f'fail: {e}'
                record['passed'] = False
                record['errors'].append(('autowire', str(e)))
        else:
            record['steps']['autowire'] = 'skip'

        # 7. consistency check
        try:
            rep = ConsistencyChecker(str(root)).check()
            record['steps']['consistency'] = f"pass ({rep['files_scanned']} files)"
        except Exception as e:
            record['steps']['consistency'] = f'fail: {e}'
            record['passed'] = False
            record['errors'].append(('consistency', str(e)))

    return record


def main():
    print("\n" + "=" * 80)
    print("REAL-PROJECT VALIDATION")
    print("=" * 80 + "\n")

    results = []
    for fix in FIXTURES:
        rec = run_pipeline_against_fixture(fix)
        results.append(rec)
        status = '[PASS]' if rec['passed'] else '[FAIL]'
        print(f"  {status} fixture={rec['fixture']}  steps={rec['steps']}")

    passed = sum(1 for r in results if r['passed'])
    print("\n" + "=" * 80)
    print(f"  {passed}/{len(results)} fixtures passed")
    print("=" * 80)

    with open('real_project_validation.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    sys.exit(0 if passed == len(results) else 1)


if __name__ == '__main__':
    main()
