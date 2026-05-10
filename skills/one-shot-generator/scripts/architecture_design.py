#!/usr/bin/env python3
"""
v1.3.0: Lightweight Architecture Design Assistant

Given a one-paragraph problem statement, produces a quick architectural
blueprint:
  - Bounded contexts / services
  - Event flows (event names + producers + consumers)
  - Proposed file structure
  - Open questions / assumptions
  - A "ready-to-generate" instruction the user can hand to one-shot-generator.

This is intentionally small — it is NOT a 5-phase planning ritual. The goal
is a 5–10 minute blueprint that users can hand straight to
``/one-shot-prompting:one-shot-generator``.

Public API:
    arch = ArchitectureDesigner(framework='fastapi')
    blueprint = arch.design(
        problem='Order processing pipeline with payments and notifications',
        scale='small',
        constraints=['async', 'kafka'],
    )
    print(blueprint['markdown'])
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Service:
    name: str
    responsibility: str
    consumes: List[str] = field(default_factory=list)
    produces: List[str] = field(default_factory=list)


@dataclass
class Blueprint:
    services: List[Service]
    events: List[str]
    file_structure: List[str]
    assumptions: List[str]
    open_questions: List[str]
    next_command: str

    def to_markdown(self) -> str:
        out = ["# Architecture Blueprint\n"]
        out.append("## Services\n")
        for s in self.services:
            out.append(f"### `{s.name}`")
            out.append(f"- Responsibility: {s.responsibility}")
            if s.consumes:
                out.append(f"- Consumes: {', '.join(f'`{e}`' for e in s.consumes)}")
            if s.produces:
                out.append(f"- Produces: {', '.join(f'`{e}`' for e in s.produces)}")
            out.append("")

        out.append("## Event Flow\n")
        out.append("```")
        out.extend(self._render_event_flow())
        out.append("```\n")

        out.append("## Proposed File Structure\n")
        out.append("```")
        out.extend(self.file_structure)
        out.append("```\n")

        out.append("## Assumptions\n")
        for a in self.assumptions:
            out.append(f"- {a}")
        out.append("")

        if self.open_questions:
            out.append("## Open Questions (decide before generating)\n")
            for q in self.open_questions:
                out.append(f"- {q}")
            out.append("")

        out.append("## Ready to Generate\n")
        out.append("```bash")
        out.append(self.next_command)
        out.append("```\n")
        return "\n".join(out)

    def _render_event_flow(self) -> List[str]:
        rows = []
        for s in self.services:
            for produced in s.produces:
                consumers = [c.name for c in self.services if produced in c.consumes]
                target = ', '.join(consumers) if consumers else '(no consumers)'
                rows.append(f"  {s.name} ──{produced}──> {target}")
        if not rows:
            rows.append("  (no events declared)")
        return rows


class ArchitectureDesigner:
    """Produces lightweight architectural blueprints."""

    def __init__(self, framework: str = 'fastapi', language: str = 'python'):
        self.framework = framework.lower()
        self.language = language.lower()

    def design(self,
               problem: str,
               scale: str = 'small',
               constraints: Optional[List[str]] = None) -> Dict:
        constraints = constraints or []
        services = self._infer_services(problem, scale)
        events = sorted({e for s in services for e in (s.produces + s.consumes)})
        file_structure = self._propose_file_structure(services)
        assumptions = self._build_assumptions(problem, scale, constraints)
        open_questions = self._open_questions(services, constraints)
        next_command = self._next_command(problem, services, constraints)

        bp = Blueprint(
            services=services,
            events=events,
            file_structure=file_structure,
            assumptions=assumptions,
            open_questions=open_questions,
            next_command=next_command,
        )

        return {
            'markdown': bp.to_markdown(),
            'services': [s.__dict__ for s in services],
            'events': events,
            'next_command': next_command,
        }

    # ---- inference ---------------------------------------------------------

    def _infer_services(self, problem: str, scale: str) -> List[Service]:
        text = problem.lower()
        services: List[Service] = []

        # Heuristic mapping from keywords to candidate services
        if any(w in text for w in ['order', 'cart', 'checkout']):
            services.append(Service(
                name='orders',
                responsibility='accept and validate new orders',
                consumes=['order.requested'],
                produces=['order.placed', 'order.rejected'],
            ))
        if any(w in text for w in ['payment', 'charge', 'billing']):
            services.append(Service(
                name='payments',
                responsibility='charge a payment method and emit settlement events',
                consumes=['order.placed'],
                produces=['payment.captured', 'payment.failed'],
            ))
        if any(w in text for w in ['inventory', 'stock', 'warehouse']):
            services.append(Service(
                name='inventory',
                responsibility='reserve stock and emit availability events',
                consumes=['order.placed'],
                produces=['inventory.reserved', 'inventory.unavailable'],
            ))
        if any(w in text for w in ['notif', 'email', 'sms', 'push']):
            services.append(Service(
                name='notifications',
                responsibility='deliver outbound notifications (email / SMS / push)',
                consumes=['payment.captured', 'order.placed'],
                produces=['notification.sent', 'notification.failed'],
            ))
        if any(w in text for w in ['user', 'auth', 'login', 'signup']):
            services.append(Service(
                name='auth',
                responsibility='manage user identity, sessions, tokens',
                consumes=['user.signup_requested'],
                produces=['user.created', 'user.session_started'],
            ))
        if any(w in text for w in ['analytics', 'metric', 'tracking']):
            services.append(Service(
                name='analytics',
                responsibility='persist domain events for downstream BI',
                consumes=[],  # filled later
                produces=[],
            ))

        if not services:
            # Fallback minimal blueprint
            services.append(Service(
                name='core',
                responsibility=f'handle the core workflow described: {problem.strip()}',
                consumes=['request.received'],
                produces=['request.completed'],
            ))

        # Wire analytics to consume everything produced
        analytics = next((s for s in services if s.name == 'analytics'), None)
        if analytics:
            analytics.consumes = sorted({e for s in services if s is not analytics for e in s.produces})

        return services

    def _propose_file_structure(self, services: List[Service]) -> List[str]:
        lines = ['project/', '├── shared/', '│   ├── events.py        # event schemas (Pydantic)',
                 '│   └── bus.py           # async bus client']
        for s in services:
            lines.append(f'├── {s.name}/')
            lines.append(f'│   ├── handlers.py')
            lines.append(f'│   ├── service.py')
            lines.append(f'│   └── tests/')
        lines.append('├── docker-compose.yml')
        lines.append('└── README.md')
        return lines

    def _build_assumptions(self, problem: str, scale: str, constraints: List[str]) -> List[str]:
        out = [
            f'Framework: {self.framework} ({self.language})',
            f'Scale: {scale} (≤10 services, ≤1k events/sec)',
        ]
        if 'kafka' in [c.lower() for c in constraints]:
            out.append('Bus: Kafka (partitioned by entity id for ordering)')
        elif 'rabbitmq' in [c.lower() for c in constraints]:
            out.append('Bus: RabbitMQ (topic exchange + DLQ per consumer)')
        else:
            out.append('Bus: asyncio in-process queue (replace with Kafka/RabbitMQ before prod)')
        if 'async' in [c.lower() for c in constraints]:
            out.append('Concurrency: asyncio (handlers must be `async def`)')
        out.append('Persistence: PostgreSQL with one schema per service')
        out.append('Observability: structured logs + Prometheus counters per event type')
        return out

    def _open_questions(self, services: List[Service], constraints: List[str]) -> List[str]:
        q = []
        if any(s.name == 'payments' for s in services):
            q.append('Which payment provider — Stripe, Adyen, in-house? Affects idempotency strategy.')
        if any(s.name == 'inventory' for s in services):
            q.append('Single warehouse or multi-warehouse? Single is simpler; multi needs allocation rules.')
        if not constraints:
            q.append('Confirm the message bus before generation — choice changes handler shape significantly.')
        q.append('Retry / DLQ policy: bounded retries (3 attempts) or per-event tuning?')
        q.append('Schema evolution: dual-publish v1+v2 during migrations, or hard cutover?')
        return q

    def _next_command(self, problem: str, services: List[Service], constraints: List[str]) -> str:
        feature = services[0].name if services else 'core'
        cons = ' '.join(f'--{c}' for c in constraints) if constraints else ''
        return (f"/one-shot-prompting:one-shot-generator "
                f"build {feature} service for: {problem.strip()} {cons}")


def main():
    import json, sys
    arch = ArchitectureDesigner()
    problem = ' '.join(sys.argv[1:]) or 'order processing pipeline with payments and notifications'
    out = arch.design(problem, constraints=['async', 'kafka'])
    print(out['markdown'])


if __name__ == '__main__':
    main()
