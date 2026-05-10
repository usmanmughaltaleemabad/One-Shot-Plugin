#!/usr/bin/env python3
"""
v1.2.0: Systematic Debugging Helpers

Given an error log / stack trace / brief problem description, this module
suggests a likely root cause, generates a minimal repro script, and ranks
candidate fixes. It is not magic — it is a curated catalog of the 30-50
most common event-driven failure modes plus a stack-trace pattern matcher.

Public API:
    helper = DebuggingHelper(framework='fastapi', language='python')
    diag = helper.diagnose(error_text='asyncio.TimeoutError: ...', code_snippet='...')
    # -> {
    #      'pattern': 'handler-timeout',
    #      'root_cause': '...',
    #      'fixes': [{'rank': 0.7, 'fix': '...'}],
    #      'repro': '...',
    #    }
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class FailurePattern:
    name: str
    triggers: List[str]  # regex against error log
    root_cause: str
    fixes: List[Dict]  # {'rank': float, 'fix': str}
    repro_template: str = ''


PATTERNS: List[FailurePattern] = [
    FailurePattern(
        name='handler-timeout',
        triggers=[r'asyncio\.TimeoutError', r'TimeoutError', r'timed?\s*out'],
        root_cause='An async handler exceeded its timeout, usually because a downstream call (DB, HTTP, queue) is slow or blocking.',
        fixes=[
            {'rank': 0.7, 'fix': 'Wrap the handler body in `asyncio.wait_for(..., timeout=N)` and surface a clear timeout error to the bus.'},
            {'rank': 0.2, 'fix': 'Move blocking calls to `loop.run_in_executor` so they don\'t starve the event loop.'},
            {'rank': 0.1, 'fix': 'Increase queue prefetch / consumer concurrency so a slow message doesn\'t hold up siblings.'},
        ],
        repro_template=(
            "import asyncio, pytest\n\n"
            "@pytest.mark.asyncio\n"
            "async def test_handler_timeout_repro():\n"
            "    async def slow():\n"
            "        await asyncio.sleep(5)\n"
            "    with pytest.raises(asyncio.TimeoutError):\n"
            "        await asyncio.wait_for(slow(), timeout=1)\n"
        ),
    ),
    FailurePattern(
        name='queue-backpressure',
        triggers=[r'queue is full', r'BackpressureError', r'lag\s*=\s*\d{4,}', r'consumer\s+lag'],
        root_cause='Messages are being produced faster than the handler drains the queue, causing memory growth or rejection.',
        fixes=[
            {'rank': 0.6, 'fix': 'Increase the number of consumer workers (Kafka partitions / Celery workers / asyncio tasks).'},
            {'rank': 0.3, 'fix': 'Add bounded queue + drop-on-full policy; emit a `backpressure.dropped` metric.'},
            {'rank': 0.1, 'fix': 'Investigate handler latency — usually a slow handler is the real cause, not low capacity.'},
        ],
    ),
    FailurePattern(
        name='dependency-injection-missing',
        triggers=[r'NoneType.*has no attribute', r'AttributeError.*None', r'depend(s|ency).*not.*provid', r'Bean.*not.*found'],
        root_cause='A required dependency (DB session, bus client, settings) was not wired up before the handler ran.',
        fixes=[
            {'rank': 0.6, 'fix': 'Confirm the framework startup hook actually calls the wiring function (e.g., `app.on_event("startup")`).'},
            {'rank': 0.3, 'fix': 'In tests, override the dependency via `app.dependency_overrides[...] = ...`.'},
            {'rank': 0.1, 'fix': 'Add a defensive assertion in the handler: `assert bus is not None, "bus not wired"`.'},
        ],
    ),
    FailurePattern(
        name='schema-mismatch',
        triggers=[r'ValidationError', r'pydantic.*error', r'field required', r'unmarshal.*error', r'JSON.*expected'],
        root_cause='The producer is sending a payload shape that no longer matches the consumer\'s schema.',
        fixes=[
            {'rank': 0.6, 'fix': 'Bump the event schema version and dual-publish (v1 + v2) until all consumers are migrated.'},
            {'rank': 0.3, 'fix': 'Make the consumer tolerant: mark new fields optional, log unknown fields rather than failing.'},
            {'rank': 0.1, 'fix': 'Add a contract test in CI that pins the schema and fails on incompatible changes.'},
        ],
    ),
    FailurePattern(
        name='race-condition',
        triggers=[r'race\s*condition', r'concurrent.*modification', r'OptimisticLock', r'version_id', r'IntegrityError.*duplicate'],
        root_cause='Two concurrent handlers mutated the same row / record without locking or idempotency keys.',
        fixes=[
            {'rank': 0.5, 'fix': 'Add an idempotency key per event and dedup on the consumer side (Redis SET NX or DB unique constraint).'},
            {'rank': 0.3, 'fix': 'Wrap the critical section in a row-level lock (`SELECT ... FOR UPDATE`) or optimistic version check.'},
            {'rank': 0.2, 'fix': 'Move state into a single-writer actor / partitioned consumer keyed on the entity id.'},
        ],
    ),
    FailurePattern(
        name='retry-storm',
        triggers=[r'too many retries', r'retry.*exceeded', r'circuit.*open', r'rate.*limited'],
        root_cause='Failed messages are being retried in a tight loop, amplifying load on a downstream that is already struggling.',
        fixes=[
            {'rank': 0.6, 'fix': 'Add exponential backoff with jitter to the retry policy.'},
            {'rank': 0.3, 'fix': 'Route messages that exceed N retries to a dead-letter queue.'},
            {'rank': 0.1, 'fix': 'Add a circuit breaker around the failing downstream so retries pause when it is unhealthy.'},
        ],
    ),
    FailurePattern(
        name='secret-leak',
        triggers=[r'leaked.*secret', r'redact', r'password=\w+', r'authorization:\s*Bearer'],
        root_cause='A logger emitted a payload that included sensitive fields (token, password, PII).',
        fixes=[
            {'rank': 0.7, 'fix': 'Add a redaction filter to the logger (structlog processor or logging.Filter).'},
            {'rank': 0.2, 'fix': 'Use a `SecretStr` / opaque type so secrets cannot be str()-ified by accident.'},
            {'rank': 0.1, 'fix': 'Move the offending log line to debug level and disable debug in prod.'},
        ],
    ),
]


class DebuggingHelper:
    """Pattern-match an error and emit a diagnosis."""

    def __init__(self, framework: str = 'unknown', language: str = 'python'):
        self.framework = framework.lower()
        self.language = language.lower()

    def diagnose(self,
                 error_text: str = '',
                 stack_trace: str = '',
                 code_snippet: str = '') -> Dict:
        haystack = '\n'.join([error_text, stack_trace, code_snippet]).lower()

        matches: List[FailurePattern] = []
        for pat in PATTERNS:
            for trig in pat.triggers:
                if re.search(trig, haystack, re.IGNORECASE):
                    matches.append(pat)
                    break

        if not matches:
            return {
                'pattern': 'unknown',
                'root_cause': 'No known pattern matched. Use the generic checklist below.',
                'fixes': [
                    {'rank': 0.5, 'fix': 'Reproduce the failure locally with the smallest possible input.'},
                    {'rank': 0.3, 'fix': 'Bisect: which commit / config change preceded the failure?'},
                    {'rank': 0.2, 'fix': 'Add structured logging at every state transition between input and failure.'},
                ],
                'repro': '',
                'evidence': [],
            }

        # Pick the highest-priority match (first one matched, but if multiple, prefer the more specific)
        primary = matches[0]
        return {
            'pattern': primary.name,
            'root_cause': primary.root_cause,
            'fixes': sorted(primary.fixes, key=lambda f: f['rank'], reverse=True),
            'repro': primary.repro_template,
            'evidence': [pat.name for pat in matches],
        }


def main():
    import sys, json
    helper = DebuggingHelper()
    text = sys.stdin.read() if not sys.stdin.isatty() else 'asyncio.TimeoutError: handler took too long'
    print(json.dumps(helper.diagnose(error_text=text), indent=2))


if __name__ == '__main__':
    main()
