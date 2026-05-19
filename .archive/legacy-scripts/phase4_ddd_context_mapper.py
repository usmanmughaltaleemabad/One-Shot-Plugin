#!/usr/bin/env python3
"""
Phase 4 DDD: Context Mapper - Maps Relationships Between Bounded Contexts

Generates context mapping for integration patterns between bounded contexts.
Supports: Upstream/Downstream, Shared Kernel, Open Host Service, Published Language.

Usage:
    python phase4_ddd_context_mapper.py --source Order --target Payment --pattern downstream

Input: Context names and integration pattern
Output: Mapping code with anti-corruption layers
"""

import argparse
import json


INTEGRATION_PATTERNS = {
    "upstream": "Source context depends on target (one-way dependency)",
    "downstream": "Target calls source (source provides service)",
    "shared_kernel": "Both contexts share common model (minimal)",
    "published_language": "Source publishes events, target subscribes (decoupled)",
    "open_host_service": "Source provides REST API for target consumers",
    "conformist": "Target accepts source model as-is (no translation)",
    "anti_corruption_layer": "Target has adapter protecting from source changes",
}


def generate_context_mapping(source: str, target: str, pattern: str) -> dict:
    """
    Generate context mapping between two bounded contexts.

    Args:
        source: Source context name (e.g., Order)
        target: Target context name (e.g., Payment)
        pattern: Integration pattern

    Returns:
        dict with mapping code and relationships
    """

    if pattern == "downstream":
        mapping_code = f'''
class {{source}}To{{target}}Mapping:
    """
    Downstream Mapping: {{source}} → {{target}}

    {{source}} context calls {{target}} context synchronously.
    {{target}} provides service, {{source}} consumes.

    Integration Points:
    - {{source}} calls {{target}} API to process{{target}}
    - {{target}} returns result
    - {{source}} handles {{target}} failures with fallback/retry
    """

    def __init__(self, {{target.lower()}}_client):
        self.{{target.lower()}}_client = {{target.lower()}}_client

    def request_{{target.lower()}}_action(self, request: dict) -> dict:
        \"\"\"
        Call {{target}} service (with ACL).

        {{source}} domain language → {{target}} domain language
        \"\"\"
        try:
            # Translate {{source}} request to {{target}} format
            {{target.lower()}}_request = self._translate_request(request)

            # Call {{target}} API
            result = self.{{target.lower()}}_client.process({{target.lower()}}_request)

            # Translate {{target}} response back to {{source}} format
            return self._translate_response(result)

        except {{target}}Error as e:
            # Handle {{target}} failures
            raise {{source}}{{target}}IntegrationError(str(e))

    def _translate_request(self, {{source.lower()}}_request: dict) -> dict:
        \"\"\"Translate {{source}} request to {{target}} API format\"\"\"
        return {{
            "transaction_id": {{source.lower()}}_request.get("id"),
            "amount": {{source.lower()}}_request.get("total"),
            # ...more fields
        }}

    def _translate_response(self, {{target.lower()}}_response: dict) -> dict:
        \"\"\"Translate {{target}} response to {{source}} domain language\"\"\"
        return {{
            "success": {{target.lower()}}_response.get("status") == "completed",
            "transaction_id": {{target.lower()}}_response.get("transaction_id"),
            # ...more fields
        }}
'''.replace("{{source}}", source).replace("{{target}}", target).replace("{{source.lower()}}", source.lower()).replace("{{target.lower()}}", target.lower())

    elif pattern == "published_language":
        mapping_code = f'''
class {{source}}{{target}}EventMapping:
    """
    Published Language Mapping: {{source}} → {{target}} (event-driven)

    {{source}} publishes domain events.
    {{target}} subscribes and reacts independently.
    Decoupled, asynchronous, eventual consistency.

    Integration Points:
    - {{source}} publishes {{source}}Event
    - Event Bus delivers to {{target}} subscribers
    - {{target}}EventHandler reacts and updates its state
    """

    def __init__(self, event_bus):
        self.event_bus = event_bus

        # {{target}} subscribes to {{source}} events
        self.event_bus.subscribe("{{source}}CreatedEvent", self._on_{{source.lower()}}_created)
        self.event_bus.subscribe("{{source}}UpdatedEvent", self._on_{{source.lower()}}_updated)

    def _on_{{source.lower()}}_created(self, event):
        \"\"\"Handle {{source}} created event\"\"\"
        # Translate event to {{target}} domain concepts
        {{target.lower()}}_data = self._translate_event(event)

        # {{target}} reacts: update read model, trigger action, etc.
        # Note: {{target}} is not aware of {{source}}

    def _on_{{source.lower()}}_updated(self, event):
        \"\"\"Handle {{source}} updated event\"\"\"
        {{target.lower()}}_data = self._translate_event(event)

    def _translate_event(self, {{source.lower()}}_event) -> dict:
        \"\"\"Translate {{source}} event to {{target}} understanding\"\"\"
        return {{
            "id": {{source.lower()}}_event.aggregate_id,
            "data": {{source.lower()}}_event.data,
            # {{target}} interprets in its own context
        }}
'''.replace("{{source}}", source).replace("{{target}}", target).replace("{{source.lower()}}", source.lower()).replace("{{target.lower()}}", target.lower())

    elif pattern == "shared_kernel":
        mapping_code = f'''
class {{source}}{{target}}SharedKernel:
    """
    Shared Kernel Mapping: {{source}} ↔ {{target}} (bidirectional)

    {{source}} and {{target}} share a minimal common model.
    Used sparingly—too much sharing creates coupling.

    Shared Types:
    - {{shared_type}} (use by both contexts)

    Guidelines:
    - Keep shared model minimal
    - Each context extends with domain-specific attributes
    - Changes to shared kernel affect both contexts
    - Document why sharing is necessary
    """

    # Shared model (minimal)
    class {{shared_type}}:
        def __init__(self, id: str, name: str):
            self.id = id
            self.name = name


# {{source}}-specific extension
class {{source}}{{shared_type}}({{source}}{{target}}SharedKernel.{{shared_type}}):
    def __init__(self, id: str, name: str, **{{source.lower()}}_fields):
        super().__init__(id, name)
        # {{source}}-specific attributes
        for key, value in {{source.lower()}}_fields.items():
            setattr(self, key, value)


# {{target}}-specific extension
class {{target}}{{shared_type}}({{source}}{{target}}SharedKernel.{{shared_type}}):
    def __init__(self, id: str, name: str, **{{target.lower()}}_fields):
        super().__init__(id, name)
        # {{target}}-specific attributes
        for key, value in {{target.lower()}}_fields.items():
            setattr(self, key, value)
'''.replace("{{source}}", source).replace("{{target}}", target).replace("{{source.lower()}}", source.lower()).replace("{{target.lower()}}", target.lower()).replace("{{shared_type}}", f"Shared{source}{target}")

    else:
        mapping_code = f"# {{pattern}} mapping for {{source}} → {{target}}".replace("{{pattern}}", pattern).replace("{{source}}", source).replace("{{target}}", target)

    return {
        "code": mapping_code,
        "source": source,
        "target": target,
        "pattern": pattern,
        "pattern_description": INTEGRATION_PATTERNS.get(pattern, ""),
    }


def generate_context_map_documentation(mappings: list) -> str:
    """Generate overall context map documentation."""

    doc = '''
# Context Map

Visual representation of bounded contexts and their relationships.

```
   ┌──────────┐
   │ Context1 │
   └────┬─────┘
        │ Downstream
        │ (calls API)
        │
   ┌────▼─────┐
   │ Context2 │
   └──────────┘


   ┌──────────┐
   │ Context3 │  → Published Language
   └──────────┘
        │
        │ Events
        ▼
   [Event Bus]
        │
        ▼
   ┌──────────┐
   │ Context4 │  (subscribes)
   └──────────┘
```

## Relationships

| Source | Target | Pattern | Sync | ACL | Details |
|--------|--------|---------|------|-----|---------|
| Order | Payment | Downstream | Yes | Yes | Order calls Payment API |
| Order | Shipping | Published Language | No | Yes | OrderShipped event |
| User | Order | Upstream | Yes | No | Order reads User |

## Integration Principles

1. **Minimize Coupling**: Each context owns its data
2. **Explicit Boundaries**: Clear API/event contracts
3. **Translate at Boundaries**: ACL protects domain logic
4. **Async When Possible**: Use events over synchronous calls
5. **Document Relationships**: Keep map up-to-date
'''

    return doc


def main():
    parser = argparse.ArgumentParser(
        description="Map relationships between bounded contexts"
    )
    parser.add_argument(
        "--source", required=True,
        help="Source context name (e.g., Order)"
    )
    parser.add_argument(
        "--target", required=True,
        help="Target context name (e.g., Payment)"
    )
    parser.add_argument(
        "--pattern", choices=list(INTEGRATION_PATTERNS.keys()), default="downstream",
        help="Integration pattern"
    )
    parser.add_argument(
        "--output", choices=["json", "code"], default="code",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_context_mapping(args.source, args.target, args.pattern)

    if args.output == "json":
        print(json.dumps(result, indent=2))
    else:
        print(result["code"])
        print("\n# Metadata")
        print(json.dumps({k: v for k, v in result.items() if k != "code"}, indent=2))
        print("\n# Context Map")
        print(generate_context_map_documentation([result]))


if __name__ == "__main__":
    main()
