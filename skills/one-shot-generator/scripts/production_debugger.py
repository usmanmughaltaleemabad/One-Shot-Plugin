#!/usr/bin/env python3
"""
v1.3.3: Production Debugging Integration

Given production artefacts (error log, stack trace, recent traces) emit a
structured incident response: hypothesis, repro plan, hotfix vs. permanent
fix, monitoring additions. Builds on top of `debugging_helpers.py` but
operates at the *system* level, not the local-test level.

Public API:
    debugger = ProductionDebugger(framework='fastapi')
    response = debugger.respond(
        error_log=open('logs.txt').read(),
        stack_trace=open('trace.txt').read(),
        affected_service='payments',
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from debugging_helpers import DebuggingHelper


@dataclass
class IncidentResponse:
    severity: str  # P0..P3
    hypothesis: str
    repro_steps: List[str]
    hotfix: str
    permanent_fix: str
    monitoring_additions: List[str]
    rollback_plan: str

    def to_markdown(self) -> str:
        out = []
        out.append(f"# Incident Response — severity {self.severity}\n")
        out.append("## Hypothesis")
        out.append(self.hypothesis + "\n")
        out.append("## Reproduction (run in staging)")
        for i, step in enumerate(self.repro_steps, 1):
            out.append(f"{i}. {step}")
        out.append("")
        out.append("## Hotfix (minimal change to stop the bleeding)")
        out.append("```")
        out.append(self.hotfix)
        out.append("```\n")
        out.append("## Permanent fix (proper refactor + tests)")
        out.append("```")
        out.append(self.permanent_fix)
        out.append("```\n")
        out.append("## Monitoring to add")
        for m in self.monitoring_additions:
            out.append(f"- {m}")
        out.append("")
        out.append("## Rollback plan")
        out.append(self.rollback_plan)
        return "\n".join(out)


class ProductionDebugger:
    """Production-incident response builder."""

    def __init__(self, framework: str = 'fastapi', language: str = 'python'):
        self.framework = framework.lower()
        self.language = language.lower()
        self.helper = DebuggingHelper(framework=framework, language=language)

    def respond(self,
                error_log: str = '',
                stack_trace: str = '',
                affected_service: str = '',
                request_volume: int = 0) -> Dict:
        diag = self.helper.diagnose(error_text=error_log, stack_trace=stack_trace)

        severity = self._severity(error_log, request_volume)
        hypothesis = diag.get('root_cause', 'Unknown — no pattern matched.')
        top_fix = (diag.get('fixes') or [{'fix': 'investigate manually'}])[0]

        response = IncidentResponse(
            severity=severity,
            hypothesis=hypothesis,
            repro_steps=self._repro_steps(diag, affected_service),
            hotfix=self._hotfix_template(diag, top_fix['fix']),
            permanent_fix=self._permanent_fix_template(diag, affected_service),
            monitoring_additions=self._monitoring(diag, affected_service),
            rollback_plan=self._rollback(affected_service),
        )

        return {
            'severity': severity,
            'pattern': diag.get('pattern', 'unknown'),
            'response': response.to_markdown(),
            'structured': {
                'hypothesis': hypothesis,
                'repro_steps': response.repro_steps,
                'hotfix': response.hotfix,
                'permanent_fix': response.permanent_fix,
                'monitoring_additions': response.monitoring_additions,
            },
        }

    # ---- internals ---------------------------------------------------------

    @staticmethod
    def _severity(error_log: str, request_volume: int) -> str:
        text = (error_log or '').lower()
        if 'p0' in text or 'outage' in text or request_volume > 1000:
            return 'P0'
        if '5xx' in text or '500' in text or 'error rate' in text:
            return 'P1'
        if 'warning' in text:
            return 'P3'
        return 'P2'

    @staticmethod
    def _repro_steps(diag: Dict, service: str) -> List[str]:
        steps = [
            f'Open staging dashboard for `{service or "the affected service"}`.',
            'Replay the failing payload against the staging endpoint (use the trace ID from the error).',
            'Confirm the same exception class / status code reproduces.',
        ]
        repro = diag.get('repro')
        if repro:
            steps.append('Optional: run this minimal pytest reproduction:\n```python\n' + repro + '```')
        return steps

    @staticmethod
    def _hotfix_template(diag: Dict, suggested_fix: str) -> str:
        return ('# Hotfix — keep change tiny, ship behind a feature flag.\n'
                f'# Suggested mitigation: {suggested_fix}\n\n'
                '# pseudo-code:\n'
                'if FEATURE_FLAGS.enabled("hotfix-incident"):\n'
                '    # apply the mitigation\n'
                '    ...\n'
                'else:\n'
                '    # legacy behaviour\n'
                '    ...\n')

    @staticmethod
    def _permanent_fix_template(diag: Dict, service: str) -> str:
        return ('# Permanent fix — schedule for the next sprint.\n'
                f'# Service: {service or "<service>"}\n'
                '# 1. Reproduce the failure with a regression test (see repro_steps).\n'
                '# 2. Implement the fix in the handler that owns the failing path.\n'
                '# 3. Add monitoring (see monitoring_additions) so this surfaces sooner next time.\n'
                '# 4. Remove the feature flag once the fix has been live for 2 weeks.\n')

    @staticmethod
    def _monitoring(diag: Dict, service: str) -> List[str]:
        pat = diag.get('pattern', '')
        common = [
            'Add a Prometheus counter on the failing handler\'s exception class.',
            'Alert when error rate > legacy baseline + 10% over 5-minute window.',
        ]
        if pat == 'handler-timeout':
            common.append('Add p99 latency histogram on the handler; alert > 2× baseline.')
        if pat == 'queue-backpressure':
            common.append('Track consumer lag per partition; alert when lag > 1k for 1 minute.')
        if pat == 'retry-storm':
            common.append('Track retries-per-message; alert when avg > 3.')
        return common

    @staticmethod
    def _rollback(service: str) -> str:
        return ('1. Disable the feature flag that gates the hotfix.\n'
                f'2. Confirm `{service or "the service"}` returns to legacy behaviour.\n'
                '3. If symptoms persist, redeploy the previous revision (`git revert HEAD && deploy`).\n'
                '4. Open a follow-up ticket; do not retry without a fresh repro.')


def main():
    pd_ = ProductionDebugger()
    out = pd_.respond(
        error_log='asyncio.TimeoutError: handler timed out after 30s',
        stack_trace='File "payments/handler.py", line 42, in charge ...',
        affected_service='payments',
        request_volume=50,
    )
    print(out['response'])


if __name__ == '__main__':
    main()
