#!/usr/bin/env python3
"""
v0.7.0: Message Bus Auto-Detection

Scans a codebase to detect which message bus / async runtime is in use, so
generated event-driven code matches the existing infrastructure (asyncio,
tokio, kafka-python, aiokafka, RabbitMQ, NATS, Celery, NestJS event bus,
SQS, Pub/Sub, Redis Streams, Server-Sent Events).

Public API:
    detector = MessageBusDetector(project_root)
    result = detector.detect()
    # -> {
    #      'primary_bus': 'kafka',
    #      'runtime': 'asyncio',
    #      'libraries': ['aiokafka', 'asyncio'],
    #      'confidence': 0.92,
    #      'evidence': [...],
    #    }
"""

from __future__ import annotations

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional


BUS_SIGNATURES: Dict[str, List[str]] = {
    'kafka':   [r'\bkafka\b', r'aiokafka', r'confluent[_-]kafka', r'kafkajs', r'spring-kafka', r'KafkaTemplate'],
    'rabbitmq':[r'rabbitmq', r'\bpika\b', r'aio[_-]?pika', r'amqplib', r'spring-amqp', r'\baio_pika\b'],
    'sqs':     [r'\bsqs\b', r'amazon[_-]?sqs', r'aiobotocore', r'\bboto3\b.*sqs'],
    'pubsub':  [r'google[_-]?cloud[_-]?pubsub', r'\bpubsub\b', r'@google-cloud/pubsub'],
    'nats':    [r'\bnats\b', r'nats-py', r'nats\.connect'],
    'redis_streams': [r'XADD', r'redis\.streams', r'aioredis', r'XREADGROUP'],
    'celery':  [r'\bcelery\b', r'@shared_task', r'@app\.task'],
    'nestjs_eventbus': [r'@nestjs/cqrs', r'EventBus', r'@EventsHandler', r'commandBus'],
    'asyncio_queue': [r'asyncio\.Queue', r'asyncio\.create_task', r'asyncio\.gather'],
    'tokio_channel': [r'tokio::sync::mpsc', r'tokio::spawn', r'broadcast::channel'],
    'go_channels': [r'\bchan\s+\w+', r'select\s*{[^}]*case\s+<-', r'goroutine'],
    'mqtt':    [r'paho[_-]?mqtt', r'aiomqtt', r'\bmqtt\b'],
    'eventbridge': [r'eventbridge', r'aws-events', r'PutEvents'],
}


RUNTIME_SIGNATURES: Dict[str, List[str]] = {
    'asyncio':  [r'\basync\s+def\b', r'\bawait\b', r'asyncio\.run', r'asyncio\.gather'],
    'tokio':    [r'#\[tokio::main\]', r'tokio::spawn', r'use\s+tokio'],
    'goroutines': [r'\bgo\s+func\b', r'\bgoroutine\b', r'go\s+\w+\('],
    'spring_async': [r'@Async\b', r'CompletableFuture', r'@EnableAsync'],
    'nodejs_promises': [r'\.then\s*\(', r'async\s+function', r'\bawait\b.*\bnew Promise\b'],
    'rxjava':   [r'\bObservable\b', r'\bFlux\b', r'\bMono\b'],
    'sync':     [],
}


# Pre-compile patterns once. We use a single combined regex per bus / runtime
# so each file is scanned with O(buses) regex calls instead of O(buses*pats).
_COMPILED_BUS = {
    bus: re.compile('|'.join(f'(?:{p})' for p in pats), re.IGNORECASE | re.MULTILINE)
    for bus, pats in BUS_SIGNATURES.items()
}
_COMPILED_RUNTIME = {
    rt: re.compile('|'.join(f'(?:{p})' for p in pats), re.MULTILINE) if pats else None
    for rt, pats in RUNTIME_SIGNATURES.items()
}


SCANNABLE_EXTS = {'.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.java', '.rs', '.kt', '.scala'}
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', 'venv', '.venv', 'target', 'build', 'dist', '.idea', '.vscode'}


class MessageBusDetector:
    """Detects message bus and async runtime patterns in a codebase."""

    def __init__(self, project_root: str, max_files: int = 500):
        self.project_root = Path(project_root)
        self.max_files = max_files

    # ---- public API --------------------------------------------------------

    def detect(self) -> Dict:
        """Return detection result dict."""
        files_scanned = 0
        bus_hits: Dict[str, List[Dict]] = {bus: [] for bus in BUS_SIGNATURES}
        runtime_hits: Dict[str, int] = {rt: 0 for rt in RUNTIME_SIGNATURES}
        libraries: List[str] = []

        # Inspect manifests first (fast + high signal)
        libraries.extend(self._scan_manifests())

        for filepath in self._iter_source_files():
            files_scanned += 1
            if files_scanned > self.max_files:
                break

            try:
                content = filepath.read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue

            for bus, regex in _COMPILED_BUS.items():
                if regex.search(content):
                    bus_hits[bus].append({
                        'file': str(filepath.relative_to(self.project_root)),
                    })

            for rt, regex in _COMPILED_RUNTIME.items():
                if regex is not None and regex.search(content):
                    runtime_hits[rt] += 1

        # Pick winner
        primary_bus, bus_score = self._rank_bus(bus_hits)
        runtime, runtime_score = self._rank_runtime(runtime_hits)

        confidence = self._confidence(bus_score, runtime_score, files_scanned)

        return {
            'primary_bus': primary_bus,
            'runtime': runtime,
            'libraries': sorted(set(libraries)),
            'confidence': round(confidence, 2),
            'files_scanned': files_scanned,
            'bus_hits': {b: hits for b, hits in bus_hits.items() if hits},
            'runtime_hits': {r: c for r, c in runtime_hits.items() if c},
            'evidence': self._evidence_summary(bus_hits, runtime_hits),
        }

    # ---- internals ---------------------------------------------------------

    def _iter_source_files(self):
        """Yield source files under project_root, skipping noise dirs."""
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext in SCANNABLE_EXTS:
                    yield Path(root) / fname

    def _scan_manifests(self) -> List[str]:
        """Read package.json / requirements.txt / pom.xml / go.mod etc."""
        libs: List[str] = []
        manifests = {
            'package.json': self._parse_package_json,
            'requirements.txt': self._parse_requirements,
            'pyproject.toml': self._parse_pyproject,
            'pom.xml': self._parse_pom,
            'go.mod': self._parse_go_mod,
            'Cargo.toml': self._parse_cargo,
        }
        for name, parser in manifests.items():
            path = self.project_root / name
            if path.exists():
                try:
                    libs.extend(parser(path.read_text(encoding='utf-8', errors='replace')))
                except Exception:
                    continue
        return libs

    @staticmethod
    def _parse_package_json(text: str) -> List[str]:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []
        deps = {}
        deps.update(data.get('dependencies') or {})
        deps.update(data.get('devDependencies') or {})
        return list(deps.keys())

    @staticmethod
    def _parse_requirements(text: str) -> List[str]:
        out = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Strip version specifiers
            name = re.split(r'[<>=!~\[]', line, 1)[0].strip()
            if name:
                out.append(name)
        return out

    @staticmethod
    def _parse_pyproject(text: str) -> List[str]:
        # Lightweight: pull out anything under [tool.poetry.dependencies] or [project] dependencies
        out = []
        for m in re.finditer(r'^([\w\-\.]+)\s*=\s*[\"\']?[\w\^\>\<\=\.\-]+', text, re.MULTILINE):
            out.append(m.group(1))
        return out

    @staticmethod
    def _parse_pom(text: str) -> List[str]:
        return re.findall(r'<artifactId>([^<]+)</artifactId>', text)

    @staticmethod
    def _parse_go_mod(text: str) -> List[str]:
        out = []
        for m in re.finditer(r'^\s*([\w\.\-/]+)\s+v[\d\.]+', text, re.MULTILINE):
            out.append(m.group(1))
        return out

    @staticmethod
    def _parse_cargo(text: str) -> List[str]:
        out = []
        in_deps = False
        for line in text.splitlines():
            line = line.strip()
            if line.startswith('[dependencies'):
                in_deps = True
                continue
            if line.startswith('['):
                in_deps = False
                continue
            if in_deps and '=' in line:
                out.append(line.split('=', 1)[0].strip())
        return out

    @staticmethod
    def _rank_bus(bus_hits: Dict[str, List]) -> tuple:
        if not any(bus_hits.values()):
            return 'none', 0
        ranked = sorted(bus_hits.items(), key=lambda kv: len(kv[1]), reverse=True)
        return ranked[0][0], len(ranked[0][1])

    @staticmethod
    def _rank_runtime(runtime_hits: Dict[str, int]) -> tuple:
        if not any(runtime_hits.values()):
            return 'sync', 0
        ranked = sorted(runtime_hits.items(), key=lambda kv: kv[1], reverse=True)
        return ranked[0][0], ranked[0][1]

    @staticmethod
    def _confidence(bus_score: int, runtime_score: int, files_scanned: int) -> float:
        if files_scanned == 0:
            return 0.0
        # Heuristic: more hits → higher confidence, capped at 1.0
        combined = bus_score * 0.6 + runtime_score * 0.4
        # Normalize against scanned files
        return min(1.0, combined / max(files_scanned * 0.05, 1))

    @staticmethod
    def _evidence_summary(bus_hits: Dict, runtime_hits: Dict) -> List[str]:
        out = []
        for bus, hits in bus_hits.items():
            if hits:
                out.append(f"{bus}: {len(hits)} files (e.g., {hits[0]['file']})")
        for rt, count in runtime_hits.items():
            if count:
                out.append(f"runtime[{rt}]: {count} files")
        return out


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python detect_message_bus.py <project_root>")
        sys.exit(1)
    detector = MessageBusDetector(sys.argv[1])
    result = detector.detect()
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
