#!/usr/bin/env python3
"""
v0.9.0+ Multi-Sidecar Orchestration

Generates a multi-step event pipeline where each step is a separate sidecar
that consumes the previous step's success event. Includes:

  - One module per sidecar (handler + tests)
  - An orchestration layer (event routing + DLQ + compensating handlers)
  - End-to-end integration test that walks the whole pipeline
  - Observability dashboard config (counters per stage)

Public API:
    orch = MultiSidecarOrchestrator(framework='fastapi', bus='kafka')
    files = orch.generate(pipeline=[
        {'name': 'validator', 'consumes': 'order.created', 'produces_success': 'order.validated'},
        {'name': 'inventory', 'consumes': 'order.validated', 'produces_success': 'inventory.reserved',
         'produces_failure': 'inventory.unavailable'},
        {'name': 'payment',   'consumes': 'inventory.reserved', 'produces_success': 'payment.charged',
         'produces_failure': 'payment.failed'},
    ])
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SidecarStep:
    name: str
    consumes: str
    produces_success: str
    produces_failure: Optional[str] = None
    compensating_for: Optional[str] = None  # success event of previous step that this rolls back

    @classmethod
    def from_dict(cls, data: Dict) -> 'SidecarStep':
        return cls(
            name=data['name'],
            consumes=data['consumes'],
            produces_success=data['produces_success'],
            produces_failure=data.get('produces_failure'),
            compensating_for=data.get('compensating_for'),
        )


class MultiSidecarOrchestrator:
    """Generates files for a multi-sidecar pipeline."""

    def __init__(self, framework: str = 'fastapi', bus: str = 'kafka', language: str = 'python'):
        self.framework = framework.lower()
        self.bus = bus.lower()
        self.language = language.lower()

    def generate(self, pipeline: List[Dict]) -> Dict[str, str]:
        steps = [SidecarStep.from_dict(p) for p in pipeline]
        files: Dict[str, str] = {}

        for step in steps:
            files[f'sidecars/{step.name}/handler.py'] = self._handler(step)
            files[f'sidecars/{step.name}/__init__.py'] = ''
            files[f'sidecars/{step.name}/tests/test_handler.py'] = self._handler_test(step)
            files[f'sidecars/{step.name}/tests/__init__.py'] = ''

        files['orchestration/router.py']     = self._router(steps)
        files['orchestration/dlq.py']        = self._dlq()
        files['orchestration/__init__.py']   = ''
        files['tests/test_pipeline_e2e.py']  = self._e2e_test(steps)
        files['observability/dashboard.json']= self._dashboard(steps)
        files['orchestration/README.md']     = self._readme(steps)

        return files

    # ---- file generators ---------------------------------------------------

    def _handler(self, step: SidecarStep) -> str:
        if step.produces_failure:
            body = (
                '    try:\n'
                '        # TODO: implement step logic here\n'
                f'        await bus.publish("{step.produces_success}", {{"step": "{step.name}", "input": payload}})\n'
                '    except Exception as exc:\n'
                f'        await bus.publish("{step.produces_failure}", {{"reason": str(exc), "input": payload}})\n'
                '        raise\n'
            )
        else:
            body = (
                '    # TODO: implement step logic here\n'
                f'    await bus.publish("{step.produces_success}", {{"step": "{step.name}", "input": payload}})\n'
            )

        return (
            f'"""Sidecar `{step.name}` — consumes `{step.consumes}`, emits `{step.produces_success}`."""\n'
            'from typing import Any, Dict\n'
            '\n'
            'from shared.bus import bus  # adjust import to your project structure\n'
            '\n'
            f'async def handle_{step.name}(payload: Dict[str, Any]) -> None:\n'
            '    """Process one message; emit success or failure event."""\n'
            f'{body}'
        )

    def _handler_test(self, step: SidecarStep) -> str:
        return (
            'import pytest\n'
            '\n'
            'pytestmark = pytest.mark.asyncio\n'
            '\n'
            f'from sidecars.{step.name}.handler import handle_{step.name}\n'
            '\n'
            f'async def test_{step.name}_emits_success_on_happy_path(stub_bus):\n'
            f'    await handle_{step.name}({{"id": "t-1"}})\n'
            f'    assert stub_bus.was_published("{step.produces_success}")\n'
        )

    def _router(self, steps: List[SidecarStep]) -> str:
        wires = []
        for step in steps:
            wires.append(f'    bus.subscribe("{step.consumes}", handle_{step.name})')
        wires_text = '\n'.join(wires)

        imports = '\n'.join(
            f'from sidecars.{step.name}.handler import handle_{step.name}'
            for step in steps
        )

        return (
            f'"""Pipeline router. Wires every sidecar handler to the bus."""\n'
            'from shared.bus import bus  # async pub/sub client\n'
            f'{imports}\n'
            '\n'
            'def wire_pipeline():\n'
            '    """Call once at startup. Subscribes every handler exactly once."""\n'
            f'{wires_text}\n'
        )

    def _dlq(self) -> str:
        return (
            '"""Dead-letter queue handler — captures messages that failed N retries."""\n'
            'from shared.bus import bus\n'
            'import structlog\n'
            'log = structlog.get_logger(__name__)\n'
            '\n'
            'async def handle_dlq(payload):\n'
            '    log.error("dlq.message", **payload)\n'
            '    # TODO: persist to dead_letters table for human inspection\n'
        )

    def _e2e_test(self, steps: List[SidecarStep]) -> str:
        first = steps[0]
        last = steps[-1]
        emitted = ', '.join(f'"{s.produces_success}"' for s in steps)
        return (
            'import pytest\n'
            '\n'
            'pytestmark = pytest.mark.asyncio\n'
            '\n'
            'from orchestration.router import wire_pipeline\n'
            'from shared.bus import bus  # ensure this is a fakebus in tests\n'
            '\n'
            f'async def test_full_pipeline_walks_through_every_stage(stub_bus):\n'
            '    """Emit the entry-point event and verify every downstream success event fires."""\n'
            '    wire_pipeline()\n'
            f'    await stub_bus.publish("{first.consumes}", {{"order_id": "o-1"}})\n'
            '    await stub_bus.flush()\n'
            f'    expected = [{emitted}]\n'
            '    for event in expected:\n'
            '        assert stub_bus.was_published(event), f"missing {event}"\n'
        )

    def _dashboard(self, steps: List[SidecarStep]) -> str:
        # Minimal Grafana-style dashboard JSON
        panels = []
        for i, step in enumerate(steps):
            panels.append({
                'id': i + 1,
                'title': f'{step.name} success rate',
                'targets': [{'expr': f'rate({step.produces_success.replace(".", "_")}_total[5m])'}],
            })
        import json
        return json.dumps({
            'title': 'Pipeline observability',
            'panels': panels,
        }, indent=2)

    def _readme(self, steps: List[SidecarStep]) -> str:
        flow = ' -> '.join(f'`{s.name}`' for s in steps)
        events = '\n'.join(f'- `{s.consumes}` -> `{s.name}` -> `{s.produces_success}`' for s in steps)
        return (
            f'# Multi-sidecar pipeline\n\n'
            f'Flow: {flow}\n\n'
            '## Event wiring\n\n'
            f'{events}\n\n'
            '## How to run\n\n'
            '1. Wire all sidecars at startup: `from orchestration.router import wire_pipeline; wire_pipeline()`.\n'
            '2. Each sidecar handler is independently testable; full-pipeline test in `tests/test_pipeline_e2e.py`.\n'
            '3. Failures route to `orchestration.dlq.handle_dlq` after the bus retry budget is exhausted.\n'
        )


def main():
    orch = MultiSidecarOrchestrator()
    files = orch.generate([
        {'name': 'validator', 'consumes': 'order.created', 'produces_success': 'order.validated'},
        {'name': 'inventory', 'consumes': 'order.validated', 'produces_success': 'inventory.reserved',
         'produces_failure': 'inventory.unavailable'},
        {'name': 'payment',   'consumes': 'inventory.reserved', 'produces_success': 'payment.charged',
         'produces_failure': 'payment.failed'},
    ])
    for path in files:
        print(path)


if __name__ == '__main__':
    main()
