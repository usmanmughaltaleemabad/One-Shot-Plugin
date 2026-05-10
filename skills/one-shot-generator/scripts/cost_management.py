#!/usr/bin/env python3
"""
v1.3.4: Enterprise Cost Management

Tracks token usage per generation, enforces a monthly budget, and emits
optimization suggestions. State is persisted as JSONL to keep the audit
trail immutable; budget config sits alongside.

Public API:
    cost = CostManager(state_dir='.claude-plugin')
    cost.set_budget(monthly_tokens=100_000)
    decision = cost.preflight(estimated_tokens=820, label='auth-endpoint')
    # decision = {'allow': True, 'remaining_after': 99_180, 'reason': '...'}
    cost.record(actual_tokens=900, label='auth-endpoint')
    print(cost.usage_report())
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class GenerationRecord:
    timestamp: str
    label: str
    tokens: int
    estimated: bool
    model: str = 'claude-opus-4-7'

    def to_dict(self) -> Dict:
        return asdict(self)


PRICE_PER_MTOK = {  # USD per million output tokens (rough)
    'claude-opus-4-7': 75.0,
    'claude-sonnet-4-6': 15.0,
    'claude-haiku-4-5': 1.0,
}


class CostManager:
    """Tracks usage, enforces budgets, suggests optimizations."""

    def __init__(self, state_dir: str = '.claude-plugin', model: str = 'claude-opus-4-7'):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.budget_path = self.state_dir / 'budget.json'
        self.usage_path = self.state_dir / 'usage-log.jsonl'
        self.model = model

    # ---- budget ------------------------------------------------------------

    def set_budget(self, monthly_tokens: int) -> None:
        cfg = {'monthly_tokens': int(monthly_tokens),
               'set_at': datetime.utcnow().isoformat()}
        self.budget_path.write_text(json.dumps(cfg, indent=2), encoding='utf-8')

    def get_budget(self) -> Optional[int]:
        if not self.budget_path.exists():
            return None
        try:
            return int(json.loads(self.budget_path.read_text(encoding='utf-8'))['monthly_tokens'])
        except Exception:
            return None

    # ---- preflight & record -----------------------------------------------

    def preflight(self, estimated_tokens: int, label: str = '') -> Dict:
        budget = self.get_budget()
        used = self.tokens_used_this_month()
        if budget is None:
            return {'allow': True, 'remaining_after': None, 'reason': 'no budget configured'}

        if used + estimated_tokens > budget:
            return {
                'allow': False,
                'remaining_after': budget - used,
                'reason': f'would exceed monthly budget ({used + estimated_tokens} > {budget})',
                'optimization_hints': self._optimization_hints(estimated_tokens, label),
            }

        return {
            'allow': True,
            'remaining_after': budget - used - estimated_tokens,
            'reason': 'within budget',
        }

    def record(self, actual_tokens: int, label: str = '', estimated: bool = False) -> None:
        rec = GenerationRecord(
            timestamp=datetime.utcnow().isoformat(),
            label=label or 'unnamed',
            tokens=int(actual_tokens),
            estimated=estimated,
            model=self.model,
        )
        with self.usage_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(rec.to_dict()) + '\n')

    # ---- reports -----------------------------------------------------------

    def tokens_used_this_month(self) -> int:
        if not self.usage_path.exists():
            return 0
        now = datetime.utcnow()
        prefix = f"{now.year:04d}-{now.month:02d}"
        total = 0
        with self.usage_path.open('r', encoding='utf-8') as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get('timestamp', '').startswith(prefix):
                    total += int(rec.get('tokens', 0))
        return total

    def usage_report(self) -> Dict:
        used = self.tokens_used_this_month()
        budget = self.get_budget()
        cost_per_mtok = PRICE_PER_MTOK.get(self.model, 30.0)
        cost_usd = used / 1_000_000.0 * cost_per_mtok

        report = {
            'tokens_used_this_month': used,
            'monthly_budget': budget,
            'percent_used': round(used / budget * 100, 1) if budget else None,
            'estimated_cost_usd': round(cost_usd, 2),
            'top_generations': self._top_generations(limit=5),
            'model': self.model,
        }
        return report

    # ---- internals ---------------------------------------------------------

    def _top_generations(self, limit: int = 5) -> List[Dict]:
        if not self.usage_path.exists():
            return []
        records: List[Dict] = []
        with self.usage_path.open('r', encoding='utf-8') as f:
            for line in f:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return sorted(records, key=lambda r: r.get('tokens', 0), reverse=True)[:limit]

    @staticmethod
    def _optimization_hints(tokens: int, label: str) -> List[str]:
        hints = []
        if tokens > 1500:
            hints.append('Generation is large (>1500 tokens). Consider splitting into smaller features.')
        if 'test' in label.lower():
            hints.append('Tests can usually share fixtures — request only the specific test cases you need.')
        if tokens > 500:
            hints.append('Use plain dataclasses instead of Pydantic models when validation is light (saves ~30% tokens).')
        if not hints:
            hints.append('No specific savings identified; verify you actually need every section requested.')
        return hints


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['set-budget', 'usage', 'preflight', 'record'])
    parser.add_argument('--monthly', type=int, default=None)
    parser.add_argument('--tokens', type=int, default=0)
    parser.add_argument('--label', default='')
    parser.add_argument('--state-dir', default='.claude-plugin')
    args = parser.parse_args()

    cm = CostManager(state_dir=args.state_dir)
    if args.command == 'set-budget':
        cm.set_budget(args.monthly or 100_000)
        print(f"Budget set: {args.monthly} tokens/month")
    elif args.command == 'usage':
        print(json.dumps(cm.usage_report(), indent=2))
    elif args.command == 'preflight':
        print(json.dumps(cm.preflight(args.tokens, args.label), indent=2))
    elif args.command == 'record':
        cm.record(args.tokens, args.label)
        print("Recorded.")


if __name__ == '__main__':
    main()
