#!/usr/bin/env python3
"""
v0.7.0-v0.8.0 Feature-Discovery: Template Library

A curated set of 25+ proven prompts for one-shot-prompting, organised by
scenario. Users invoke this via:

    python template_library.py list                    # all templates
    python template_library.py list --tag messaging    # filter by tag
    python template_library.py show <id>               # full template
    python template_library.py search "kafka consumer" # keyword search

Public API:
    library = TemplateLibrary()
    templates = library.list(tag='messaging')
    one = library.get('msg-kafka-validate')
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class Template:
    id: str
    title: str
    tags: List[str]
    framework: str
    prompt: str
    notes: str = ''

    def to_dict(self) -> Dict:
        return asdict(self)


TEMPLATES: List[Template] = [
    # ----- Messaging --------------------------------------------------------
    Template(
        id='msg-kafka-validate',
        title='Kafka consumer that validates and re-emits',
        tags=['messaging', 'kafka', 'validation'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add Kafka consumer for user.signup events: validate email, emit user.validated '
                'or user.rejected, include DLQ routing after 3 retries. @./'),
    ),
    Template(
        id='msg-rmq-saga',
        title='RabbitMQ saga step with compensating action',
        tags=['messaging', 'rabbitmq', 'saga'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add RabbitMQ saga step that reserves inventory on order.placed, emits '
                'inventory.reserved on success or inventory.unavailable on failure, with a '
                'compensating handler for inventory.release. @./'),
    ),
    Template(
        id='msg-sqs-exactly-once',
        title='SQS consumer with exactly-once delivery',
        tags=['messaging', 'sqs', 'exactly-once'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add exactly-once SQS consumer for payment.received, charge customer via '
                'Stripe, emit charge.completed; include idempotency key based on payment_id. @./'),
    ),
    Template(
        id='msg-pubsub-fanout',
        title='Pub/Sub fan-out to N subscribers',
        tags=['messaging', 'pubsub', 'fanout'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add Google Pub/Sub fan-out: one publisher emits user.activity, three '
                'subscribers (analytics, audit, recommendation) consume independently. @./'),
    ),
    Template(
        id='msg-celery-tasks',
        title='Celery background tasks',
        tags=['messaging', 'celery', 'background'],
        framework='django',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add Celery tasks for sending welcome email, generating PDF receipt, and '
                'reindexing search; wire into Django signals on user.created. @./'),
    ),
    # ----- REST / GraphQL ---------------------------------------------------
    Template(
        id='api-rest-create-user',
        title='REST endpoint POST /users',
        tags=['api', 'rest', 'crud'],
        framework='fastapi',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add REST endpoint POST /users that validates payload, creates user, sends '
                'welcome email via background task, returns user with auth token. @./'),
    ),
    Template(
        id='api-graphql-subscription',
        title='GraphQL subscription for order updates',
        tags=['api', 'graphql', 'subscription'],
        framework='nestjs',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add GraphQL subscription for order status updates (order.created, '
                'order.shipped, order.delivered) with WebSocket transport. @./'),
    ),
    Template(
        id='api-rate-limited',
        title='Rate-limited endpoint',
        tags=['api', 'rate-limit', 'security'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add rate-limited endpoint POST /comments using sliding window log, drop '
                'requests above 10/min/user, emit rate.exceeded events. @./'),
    ),
    # ----- Deployment / CI/CD ----------------------------------------------
    Template(
        id='deploy-k8s-bundle',
        title='Kafka consumer + Dockerfile + k8s + GitHub Actions',
        tags=['deployment', 'kubernetes', 'ci'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add Kafka consumer for events, include Dockerfile, Kubernetes manifest with '
                'HPA, and GitHub Actions workflow that builds + tests + deploys. @./'),
    ),
    Template(
        id='deploy-terraform',
        title='Terraform module for SQS consumer',
        tags=['deployment', 'terraform', 'aws'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add SQS consumer with Terraform module that provisions queue + DLQ + '
                'IAM role + Lambda function. @./'),
    ),
    Template(
        id='deploy-integration-test',
        title='Integration test scaffold with testcontainers',
        tags=['deployment', 'testing', 'integration'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Generate integration test scaffold that spins up RabbitMQ via testcontainers, '
                'emits test events, validates handler response. @./'),
    ),
    # ----- Observability ---------------------------------------------------
    Template(
        id='obs-otel-prom',
        title='Handler with OpenTelemetry + Prometheus',
        tags=['observability', 'opentelemetry', 'prometheus'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add Kafka consumer for order.created with OpenTelemetry tracing, Prometheus '
                'metrics (latency histogram, error counter), and structlog. @./'),
    ),
    Template(
        id='obs-game-server',
        title='Game-server observability block',
        tags=['observability', 'games', 'domain'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add observability for game server event handler: frame timing histogram, '
                'event-queue depth gauge, p99 input-to-render latency. --observability games @./'),
    ),
    Template(
        id='obs-trading',
        title='Trading-bot observability',
        tags=['observability', 'trading', 'domain'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add observability for trade execution: order latency, fill rate gauge, '
                'cost-per-trade histogram in basis points. --observability trading @./'),
    ),
    # ----- Refactor / Migration --------------------------------------------
    Template(
        id='ref-exactly-once',
        title='Refactor handler to exactly-once delivery',
        tags=['refactor', 'exactly-once', 'idempotency'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Refactor user.created handler to exactly-once delivery using Redis SETNX '
                'as idempotency store; preserve current side effects. @./'),
    ),
    Template(
        id='ref-event-versioning',
        title='Backward-compatible v2 of an event',
        tags=['refactor', 'versioning', 'compat'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add user.created v2 handler with new fields, deprecate v1 with logged '
                'warning, dual-publish for 2 weeks. @./'),
    ),
    Template(
        id='ref-strangler-auth',
        title='Strangler migration of legacy auth',
        tags=['refactor', 'strangler', 'legacy'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                '--strangler --legacy legacy_auth.py --new auth_v2.py --flag AUTH_V2 @./'),
    ),
    # ----- Architecture & Discovery ----------------------------------------
    Template(
        id='arch-order-pipeline',
        title='Architecture blueprint for order pipeline',
        tags=['architecture', 'design'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                '--architecture "order pipeline with payments, inventory, notifications" '
                '--async --kafka'),
    ),
    Template(
        id='arch-ml-pipeline',
        title='Architecture blueprint for ML inference pipeline',
        tags=['architecture', 'ml'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                '--architecture "ML inference pipeline with feature fetch, model serve, '
                'observability" --async'),
    ),
    Template(
        id='ops-debug-prod',
        title='Production incident response',
        tags=['ops', 'debug'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator --debug-prod '
                '--service payments --error-log "asyncio.TimeoutError: ..."'),
    ),
    # ----- Quality gates ---------------------------------------------------
    Template(
        id='quality-tdd-rate-limiter',
        title='Rate limiter with --tdd',
        tags=['quality', 'tdd'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add rate limiter for message.received --tdd --explain-tdd @./'),
    ),
    Template(
        id='quality-review-gate',
        title='Generate with --review gate enabled',
        tags=['quality', 'review'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add OAuth2 password grant endpoint --review @./'),
    ),
    Template(
        id='quality-consistency-check',
        title='Cross-module consistency scan',
        tags=['quality', 'consistency'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator --check-consistency @./'),
    ),
    # ----- Cost & PR -------------------------------------------------------
    Template(
        id='cost-set-budget',
        title='Set monthly token budget',
        tags=['cost'],
        framework='any',
        prompt='/one-shot-prompting:one-shot-generator --budget 100000',
    ),
    Template(
        id='pr-bundle',
        title='Generate + open draft PR',
        tags=['pr', 'github'],
        framework='any',
        prompt=('/one-shot-prompting:one-shot-generator '
                'Add rate limiter --pr --provider github --repo org/repo @./'),
    ),
    Template(
        id='discover-health-check',
        title='Project health check',
        tags=['discovery'],
        framework='any',
        prompt='/one-shot-prompting:one-shot-generator --health-check @./',
    ),
]


class TemplateLibrary:
    """Read-only registry of curated prompts."""

    def __init__(self, templates: Optional[List[Template]] = None):
        self._templates = templates or TEMPLATES

    def list(self, tag: Optional[str] = None, framework: Optional[str] = None) -> List[Dict]:
        out = []
        for t in self._templates:
            if tag and tag not in t.tags:
                continue
            if framework and framework != t.framework and t.framework != 'any':
                continue
            out.append(t.to_dict())
        return out

    def get(self, template_id: str) -> Optional[Dict]:
        for t in self._templates:
            if t.id == template_id:
                return t.to_dict()
        return None

    def search(self, query: str) -> List[Dict]:
        q = query.lower()
        return [t.to_dict() for t in self._templates
                if q in t.id.lower() or q in t.title.lower() or q in t.prompt.lower()]

    def tags(self) -> List[str]:
        return sorted({tag for t in self._templates for tag in t.tags})


def main():
    library = TemplateLibrary()
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print("Usage: template_library.py {list|show|search|tags} [args...]")
        return

    cmd, *rest = args
    if cmd == 'list':
        tag = framework = None
        for i, a in enumerate(rest):
            if a == '--tag' and i + 1 < len(rest):
                tag = rest[i + 1]
            if a == '--framework' and i + 1 < len(rest):
                framework = rest[i + 1]
        rows = library.list(tag=tag, framework=framework)
        for r in rows:
            print(f"  {r['id']:30} {r['title']}")
        print(f"\n{len(rows)} template(s) shown.")
    elif cmd == 'show':
        if not rest:
            print('show requires a template id')
            sys.exit(1)
        t = library.get(rest[0])
        if not t:
            print(f"no template with id={rest[0]}")
            sys.exit(1)
        print(json.dumps(t, indent=2))
    elif cmd == 'search':
        if not rest:
            print('search requires a query')
            sys.exit(1)
        rows = library.search(' '.join(rest))
        for r in rows:
            print(f"  {r['id']:30} {r['title']}")
    elif cmd == 'tags':
        for tag in library.tags():
            print(f"  {tag}")
    else:
        print(f"unknown command: {cmd}")
        sys.exit(1)


if __name__ == '__main__':
    main()
