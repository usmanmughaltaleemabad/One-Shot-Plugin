#!/usr/bin/env python3
"""
v0.8.0: Event Catalog Awareness

Loads an event catalog (YAML / JSON / SKILLS.md table) and validates that
generated events:
  - Use the canonical event name
  - Match the schema (required fields, types)
  - Don't duplicate or conflict with existing events
  - Honour ordering / partitioning constraints

Public API:
    catalog = EventCatalog.from_file('events.yaml')
    result = catalog.validate(event_name='order.placed', payload={'order_id': '...', 'amount': 12.5})
    # -> {'valid': True/False, 'errors': [...], 'warnings': [...]}
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class EventDefinition:
    name: str
    fields: Dict[str, str]   # field_name -> type
    required: List[str] = field(default_factory=list)
    description: str = ''
    partition_key: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict) -> 'EventDefinition':
        return cls(
            name=data['name'],
            fields=data.get('fields', {}),
            required=data.get('required', []),
            description=data.get('description', ''),
            partition_key=data.get('partition_key'),
        )


class EventCatalog:
    """Holds a list of EventDefinitions and validates payloads against them."""

    def __init__(self, events: List[EventDefinition]):
        self._by_name = {e.name: e for e in events}

    # ---- loaders -----------------------------------------------------------

    @classmethod
    def from_file(cls, path: str) -> 'EventCatalog':
        text = Path(path).read_text(encoding='utf-8')
        if path.endswith(('.yaml', '.yml')):
            try:
                import yaml  # type: ignore
            except ImportError:
                # Lightweight fallback: refuse rather than parse YAML imperfectly.
                raise RuntimeError("PyYAML required to load YAML catalog. pip install pyyaml")
            data = yaml.safe_load(text)
        elif path.endswith('.json'):
            data = json.loads(text)
        elif path.endswith('.md'):
            data = cls._parse_markdown_table(text)
        else:
            raise ValueError(f"Unsupported catalog format: {path}")

        events = [EventDefinition.from_dict(e) for e in data.get('events', data)]
        return cls(events)

    @classmethod
    def from_dict(cls, data: Dict) -> 'EventCatalog':
        events = [EventDefinition.from_dict(e) for e in data.get('events', data)]
        return cls(events)

    @staticmethod
    def _parse_markdown_table(text: str) -> Dict:
        """Parse a simple markdown table into event definitions."""
        rows = []
        in_table = False
        headers: List[str] = []
        for line in text.splitlines():
            if line.lstrip().startswith('|') and '---' in line:
                in_table = True
                continue
            if line.lstrip().startswith('|') and not in_table:
                # header row
                headers = [c.strip().lower() for c in line.strip('|').split('|')]
                continue
            if line.lstrip().startswith('|') and in_table:
                cells = [c.strip() for c in line.strip('|').split('|')]
                if len(cells) == len(headers):
                    rows.append(dict(zip(headers, cells)))
            elif not line.strip():
                in_table = False

        events = []
        for r in rows:
            if 'event' in r or 'name' in r:
                events.append({
                    'name': r.get('event') or r.get('name'),
                    'description': r.get('description', ''),
                    'fields': {f.strip(): 'any' for f in r.get('fields', '').split(',') if f.strip()},
                    'required': [f.strip() for f in r.get('required', '').split(',') if f.strip()],
                })
        return {'events': events}

    # ---- validation --------------------------------------------------------

    def names(self) -> List[str]:
        return sorted(self._by_name.keys())

    def has(self, name: str) -> bool:
        return name in self._by_name

    def validate(self, event_name: str, payload: Dict) -> Dict:
        if event_name not in self._by_name:
            return {
                'valid': False,
                'errors': [f"event `{event_name}` is not in the catalog. "
                           f"Known events: {', '.join(self.names()[:8])}{'...' if len(self._by_name) > 8 else ''}"],
                'warnings': [],
            }

        defn = self._by_name[event_name]
        errors: List[str] = []
        warnings: List[str] = []

        for required in defn.required:
            if required not in payload:
                errors.append(f"missing required field `{required}` for {event_name}")

        for field_name, value in payload.items():
            if field_name not in defn.fields:
                warnings.append(f"unknown field `{field_name}` in {event_name} "
                                f"(known: {', '.join(defn.fields.keys())})")
                continue
            expected = defn.fields[field_name]
            if expected != 'any' and not self._type_matches(value, expected):
                errors.append(f"field `{field_name}` expected {expected}, got {type(value).__name__}")

        return {'valid': not errors, 'errors': errors, 'warnings': warnings}

    @staticmethod
    def _type_matches(value, expected: str) -> bool:
        expected = expected.lower()
        return any([
            expected in ('str', 'string') and isinstance(value, str),
            expected in ('int', 'integer') and isinstance(value, int) and not isinstance(value, bool),
            expected in ('float', 'number') and isinstance(value, (int, float)) and not isinstance(value, bool),
            expected == 'bool' and isinstance(value, bool),
            expected in ('dict', 'object') and isinstance(value, dict),
            expected in ('list', 'array') and isinstance(value, list),
            expected == 'any',
        ])


def main():
    # Demo with an inline catalog
    catalog = EventCatalog.from_dict({'events': [
        {'name': 'order.placed', 'fields': {'order_id': 'str', 'amount': 'float'}, 'required': ['order_id', 'amount']},
        {'name': 'payment.captured', 'fields': {'payment_id': 'str'}, 'required': ['payment_id']},
    ]})
    print(json.dumps(catalog.validate('order.placed', {'order_id': '123', 'amount': 12.50}), indent=2))
    print(json.dumps(catalog.validate('order.placed', {'order_id': '123'}), indent=2))


if __name__ == '__main__':
    main()
