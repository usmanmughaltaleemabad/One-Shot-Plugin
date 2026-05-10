#!/usr/bin/env python3
"""
v0.7.0-v0.8.0 Feature-Discovery: Interactive Tour

Drives a small state machine that recommends prompts / templates based on
what the user wants to build. Designed to run in two modes:

    1. As a one-shot from the SKILL.md prompt with `--tour` (the skill
       prints the JSON state and asks the user to pick a path).
    2. As a CLI helper (`python interactive_tour.py`) that walks the user
       through interactively from a terminal.

Public API:
    tour = InteractiveTour()
    state = tour.start()                    # initial state
    state = tour.choose(state, 'b')         # transition to 'consumers' state
    state = tour.choose(state, 'a')         # then to 'python' state
    # state['recommended_templates'] now has matching templates
"""

from __future__ import annotations

import json
import sys
from typing import Dict, List, Optional

from template_library import TemplateLibrary


# State machine ---------------------------------------------------------------

INITIAL = {
    'id': 'start',
    'prompt': 'What kind of feature do you want to build?',
    'options': [
        {'key': 'a', 'label': 'REST / GraphQL endpoint', 'next': 'apis'},
        {'key': 'b', 'label': 'Message queue consumer or producer', 'next': 'consumers'},
        {'key': 'c', 'label': 'Game-server event handler', 'next': 'games'},
        {'key': 'd', 'label': 'Trading-bot or financial system', 'next': 'trading'},
        {'key': 'e', 'label': 'Migrate / strangle a legacy module', 'next': 'legacy'},
        {'key': 'f', 'label': 'Just give me a project health check', 'next': 'discover'},
        {'key': 'g', 'label': 'Not sure — show me everything', 'next': 'browse'},
    ],
}


STATES = {
    'apis': {
        'id': 'apis',
        'prompt': 'Which framework?',
        'options': [
            {'key': 'a', 'label': 'FastAPI', 'tag_filter': {'api': True}, 'framework': 'fastapi'},
            {'key': 'b', 'label': 'Django REST Framework', 'tag_filter': {'api': True}, 'framework': 'django'},
            {'key': 'c', 'label': 'NestJS', 'tag_filter': {'api': True}, 'framework': 'nestjs'},
            {'key': 'd', 'label': 'Spring Boot', 'tag_filter': {'api': True}, 'framework': 'spring'},
            {'key': 'e', 'label': 'Go (net/http)', 'tag_filter': {'api': True}, 'framework': 'go'},
        ],
    },
    'consumers': {
        'id': 'consumers',
        'prompt': 'Which broker?',
        'options': [
            {'key': 'a', 'label': 'Kafka', 'tag_filter': {'kafka': True}},
            {'key': 'b', 'label': 'RabbitMQ', 'tag_filter': {'rabbitmq': True}},
            {'key': 'c', 'label': 'AWS SQS', 'tag_filter': {'sqs': True}},
            {'key': 'd', 'label': 'Google Pub/Sub', 'tag_filter': {'pubsub': True}},
            {'key': 'e', 'label': 'Celery (Redis/RabbitMQ task queue)', 'tag_filter': {'celery': True}},
        ],
    },
    'games': {
        'id': 'games',
        'prompt': 'Pick a starting template:',
        'options': [
            {'key': 'a', 'label': 'Game-server observability + handler', 'template_id': 'obs-game-server'},
            {'key': 'b', 'label': 'Multiplayer Tokio handler (Rust)', 'tag_filter': {'observability': True, 'games': True}},
        ],
    },
    'trading': {
        'id': 'trading',
        'prompt': 'Pick a starting template:',
        'options': [
            {'key': 'a', 'label': 'Trading-bot observability', 'template_id': 'obs-trading'},
            {'key': 'b', 'label': 'Architecture blueprint for ML+trading pipeline', 'template_id': 'arch-ml-pipeline'},
        ],
    },
    'legacy': {
        'id': 'legacy',
        'prompt': 'Pick a starting template:',
        'options': [
            {'key': 'a', 'label': 'Strangler migration of legacy auth', 'template_id': 'ref-strangler-auth'},
            {'key': 'b', 'label': 'Cross-module consistency check (after migration)', 'template_id': 'quality-consistency-check'},
        ],
    },
    'discover': {
        'id': 'discover',
        'prompt': 'Run a health check on your project:',
        'options': [
            {'key': 'a', 'label': 'Health check', 'template_id': 'discover-health-check'},
        ],
    },
    'browse': {
        'id': 'browse',
        'prompt': 'All available tags. Pick one to filter:',
        'options': [],  # populated dynamically
    },
}


class InteractiveTour:
    def __init__(self, library: Optional[TemplateLibrary] = None):
        self.library = library or TemplateLibrary()

    def start(self) -> Dict:
        return dict(INITIAL)

    def choose(self, state: Dict, key: str) -> Dict:
        for opt in state.get('options', []):
            if opt['key'] == key:
                return self._handle_option(opt)
        return self._error(state, key)

    # ---- internals ---------------------------------------------------------

    def _handle_option(self, option: Dict) -> Dict:
        # Direct template choice
        if 'template_id' in option:
            template = self.library.get(option['template_id'])
            return {
                'id': 'recommendation',
                'prompt': f"Recommended template: {template['title']}" if template else 'Template not found',
                'recommended_templates': [template] if template else [],
            }

        # Filter by tags
        if 'tag_filter' in option:
            tags = list(option['tag_filter'].keys())
            framework = option.get('framework')
            templates = []
            for tag in tags:
                templates.extend(self.library.list(tag=tag, framework=framework))
            # de-dupe
            seen = set(); uniq = []
            for t in templates:
                if t['id'] not in seen:
                    uniq.append(t); seen.add(t['id'])
            return {
                'id': 'recommendation',
                'prompt': f"Templates matching {tags}{' for ' + framework if framework else ''}",
                'recommended_templates': uniq,
            }

        # Transition
        if 'next' in option:
            next_state_id = option['next']
            if next_state_id == 'browse':
                state = dict(STATES['browse'])
                state['options'] = [
                    {'key': str(i + 1), 'label': tag, 'tag_filter': {tag: True}}
                    for i, tag in enumerate(self.library.tags())
                ]
                return state
            return dict(STATES[next_state_id])

        return self._error({}, option.get('key', '?'))

    @staticmethod
    def _error(state: Dict, key: str) -> Dict:
        return {
            'id': 'error',
            'prompt': f"unknown option `{key}`. Pick one from the options list.",
            'options': state.get('options', []),
        }


def _print_state(state: Dict):
    print(f"\n{state['prompt']}")
    if state.get('recommended_templates'):
        for t in state['recommended_templates']:
            print(f"\n  {t['id']}  -  {t['title']}")
            print(f"  $ {t['prompt']}")
        return
    for opt in state.get('options', []):
        print(f"  [{opt['key']}] {opt['label']}")


def main():
    tour = InteractiveTour()
    state = tour.start()
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        # one-shot JSON dump for SKILL.md to inject
        print(json.dumps(state, indent=2))
        return
    print("Welcome to the one-shot-prompting interactive tour. Type the option key, q to quit.")
    while True:
        _print_state(state)
        if not state.get('options') or state.get('id') == 'recommendation':
            return
        key = input('> ').strip()
        if key.lower() in ('q', 'quit', 'exit'):
            return
        state = tour.choose(state, key)


if __name__ == '__main__':
    main()
