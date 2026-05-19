#!/usr/bin/env python3
"""
v0.9.0: Domain-Specific Observability

Generates an observability block tuned to the user's domain:

  - games:    frame timing, event-queue depth, latency percentiles
  - bots:     message round-trip, retry rate, cost per operation
  - ml:       feature freshness, inference latency, data quality
  - trading:  cost per trade, p99 latency, fill rate
  - generic:  request rate, error rate, p95 latency

Public API:
    obs = ObservabilityBuilder(domain='games', framework='fastapi')
    block = obs.build(feature_name='player.move')
    # block has 'metrics' (Prometheus), 'logs' (structured), 'tracing' (OTel) sections
"""

from __future__ import annotations

from typing import Dict, List


DOMAIN_METRICS = {
    'games': [
        ('frame_time_seconds', 'Histogram', 'Per-frame loop duration'),
        ('event_queue_depth',  'Gauge',     'Events waiting to be processed'),
        ('player_action_total', 'Counter',  'Player actions by type'),
        ('latency_p99_seconds','Histogram', 'p99 of input → render latency'),
    ],
    'bots': [
        ('message_roundtrip_seconds', 'Histogram', 'Time from send → ack'),
        ('retry_total',               'Counter',   'Retries by message kind'),
        ('cost_per_op_usd',           'Counter',   'Estimated cost per operation'),
        ('rate_limited_total',        'Counter',   'Rejections by upstream rate-limiter'),
    ],
    'ml': [
        ('feature_freshness_seconds', 'Gauge',     'Age of latest feature data'),
        ('inference_latency_seconds', 'Histogram', 'Model inference time'),
        ('data_quality_score',        'Gauge',     'Fraction of rows passing schema check'),
        ('predictions_total',         'Counter',   'Predictions emitted by class'),
    ],
    'trading': [
        ('order_latency_seconds',     'Histogram', 'Submit → ack'),
        ('fill_rate',                 'Gauge',     'Filled / submitted'),
        ('cost_per_trade_bps',        'Histogram', 'Slippage + fees, basis points'),
        ('p99_latency_seconds',       'Histogram', 'p99 wire latency'),
    ],
    'generic': [
        ('requests_total',  'Counter',   'Requests by endpoint + status'),
        ('errors_total',    'Counter',   'Unhandled exceptions by class'),
        ('latency_seconds', 'Histogram', 'p50/p95/p99 of handler duration'),
    ],
}


DOMAIN_LOGS = {
    'games':   ['frame_id', 'tick', 'player_id', 'action'],
    'bots':    ['message_id', 'kind', 'retry_count', 'cost_usd'],
    'ml':      ['model_version', 'feature_hash', 'data_quality_score'],
    'trading': ['order_id', 'symbol', 'side', 'price', 'size'],
    'generic': ['request_id', 'user_id', 'duration_ms'],
}


DOMAIN_TRACING = {
    'games':   ['game.tick', 'player.input', 'physics.step', 'render.frame'],
    'bots':    ['bot.poll', 'bot.handle', 'bot.respond'],
    'ml':      ['ml.feature_fetch', 'ml.predict', 'ml.emit'],
    'trading': ['trade.submit', 'trade.fill', 'trade.settle'],
    'generic': ['http.handle', 'db.query', 'bus.publish'],
}


class ObservabilityBuilder:
    """Compose Prometheus + structured logs + OTel snippets per domain."""

    def __init__(self, domain: str = 'generic', framework: str = 'fastapi', language: str = 'python'):
        self.domain = domain.lower()
        if self.domain not in DOMAIN_METRICS:
            self.domain = 'generic'
        self.framework = framework.lower()
        self.language = language.lower()

    def build(self, feature_name: str = 'feature') -> Dict:
        metrics_code = self._metrics_code(feature_name)
        logging_code = self._logging_code(feature_name)
        tracing_code = self._tracing_code(feature_name)
        return {
            'domain': self.domain,
            'metrics': metrics_code,
            'logs': logging_code,
            'tracing': tracing_code,
            'metric_names': [m[0] for m in DOMAIN_METRICS[self.domain]],
            'log_fields': DOMAIN_LOGS[self.domain],
            'span_names': DOMAIN_TRACING[self.domain],
        }

    # ---- internals ---------------------------------------------------------

    def _metrics_code(self, feature: str) -> str:
        if self.language != 'python':
            return self._metrics_pseudo(feature)

        lines = [
            'from prometheus_client import Counter, Gauge, Histogram',
            '',
        ]
        for name, kind, desc in DOMAIN_METRICS[self.domain]:
            ctor = {'Counter': 'Counter', 'Gauge': 'Gauge', 'Histogram': 'Histogram'}[kind]
            lines.append(f'{name.upper()} = {ctor}("{name}", "{desc}")')
        lines.append('')
        return '\n'.join(lines)

    def _metrics_pseudo(self, feature: str) -> str:
        return '\n'.join(
            f'# {kind} {name} — {desc}' for name, kind, desc in DOMAIN_METRICS[self.domain]
        )

    def _logging_code(self, feature: str) -> str:
        fields = DOMAIN_LOGS[self.domain]
        if self.language != 'python':
            return f'# Structured log fields per event: {", ".join(fields)}'
        return (
            'import structlog\n'
            'log = structlog.get_logger()\n'
            '\n'
            'def emit(event: str, **fields):\n'
            f'    """Always include domain fields: {", ".join(fields)}."""\n'
            '    log.info(event, **fields)\n'
        )

    def _tracing_code(self, feature: str) -> str:
        spans = DOMAIN_TRACING[self.domain]
        if self.language != 'python':
            return f'# OpenTelemetry spans to add: {", ".join(spans)}'
        return (
            'from opentelemetry import trace\n'
            'tracer = trace.get_tracer(__name__)\n'
            '\n'
            f'# Suggested spans for the {self.domain} domain:\n'
            + '\n'.join(f'#   - {s}' for s in spans) + '\n'
        )


def main():
    obs = ObservabilityBuilder(domain='games')
    block = obs.build(feature_name='player.move')
    print('METRICS:\n' + block['metrics'])
    print('\nLOGS:\n' + block['logs'])
    print('\nTRACING:\n' + block['tracing'])


if __name__ == '__main__':
    main()
