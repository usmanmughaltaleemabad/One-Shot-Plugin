#!/usr/bin/env python3
"""
Skill: write-plan
Plan Writer — Generate zero-ambiguity implementation plans.

Phases:
  1. analyze — Extract codebase context for Claude
  2. validate — Check plan structure for completeness
  3. estimate — Estimate time to execute plan
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent / ".." / ".." / ".." / "one-shot-generator" / "scripts"))

try:
    from lib.base_script import __version__, setup_logging
    from analyze_codebase import CodebaseAnalyzer
    from plan_decisions import PlanDecisionMaker
except ImportError:
    __version__ = "1.0.0"
    def setup_logging(name, level=None):
        import logging
        return logging.getLogger(name)

    class CodebaseAnalyzer:
        def analyze(self, path): return {}

    class PlanDecisionMaker:
        def make_decisions(self, context): return {}

__version__ = "1.0.0"
logger = setup_logging(__name__)


class PlanWriter:
    """Plan writing orchestrator."""

    def phase_analyze(self, project_path: str) -> Dict[str, Any]:
        """Extract codebase context for plan writing."""
        try:
            analyzer = CodebaseAnalyzer()
            context = analyzer.analyze(project_path)

            return {
                'phase': 'analyze',
                'project_path': project_path,
                'framework': context.get('framework', 'unknown'),
                'language': context.get('language', 'python'),
                'testing_framework': context.get('testing_framework', 'pytest'),
                'patterns_detected': context.get('patterns', []),
                'instructions': 'Use this context in your plan. Claude will now write the plan with full codebase awareness.',
            }
        except Exception as e:
            return {'error': f'Analysis failed: {e}'}

    def phase_validate(self, plan_text: str) -> Dict[str, Any]:
        """Validate plan structure."""
        errors = []
        ambiguous_tasks = []

        # Check for required markdown structure
        tasks = re.split(r'^#### Task \d+:', plan_text, flags=re.MULTILINE)[1:]

        if not tasks:
            errors.append('No tasks found. Plan must have "#### Task N: Name" headers.')
            return {
                'phase': 'validate',
                'valid': False,
                'errors': errors,
                'ambiguous_tasks': [],
                'total_tasks': 0,
            }

        for i, task_block in enumerate(tasks, 1):
            required_fields = {
                'goal': r'^\*\*Goal:\*\*\s+(.+)$',
                'file': r'^\*\*File:\*\*\s+(.+)$',
                'code': r'^\*\*Code:\*\*\s*\n```[\w]*\n([\s\S]*?)\n```',
                'verify': r'^\*\*Verify:\*\*\s+(.+)$',
                'checkpoint': r'^\*\*Checkpoint:\*\*\s+(.+)$',
            }

            missing = []
            for field, pattern in required_fields.items():
                if not re.search(pattern, task_block, re.MULTILINE):
                    missing.append(field)

            if missing:
                errors.append(f'Task {i}: Missing fields {missing}')

            # Check for placeholders
            code_match = re.search(r'```[\w]*\n([\s\S]*?)\n```', task_block)
            if code_match:
                code = code_match.group(1)
                if re.search(r'(\.\.\.|TBD|\[placeholder\]|\[TODO\])', code, re.IGNORECASE):
                    ambiguous_tasks.append(i)

        valid = len(errors) == 0

        return {
            'phase': 'validate',
            'valid': valid,
            'total_tasks': len(tasks),
            'errors': errors,
            'ambiguous_tasks': ambiguous_tasks,
            'message': 'Plan is valid' if valid else 'Fix errors before executing',
        }

    def phase_estimate(self, plan_text: str) -> Dict[str, Any]:
        """Estimate execution time."""
        tasks = re.split(r'^#### Task \d+:', plan_text, flags=re.MULTILINE)[1:]
        total_tasks = len(tasks)
        estimated_minutes = total_tasks * 5  # 5 min per task

        return {
            'phase': 'estimate',
            'total_tasks': total_tasks,
            'minutes_per_task': 5,
            'estimated_total_minutes': estimated_minutes,
            'estimated_total_hours': round(estimated_minutes / 60, 1),
        }


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Plan Writer')
    parser.add_argument('--phase', required=True,
                       choices=['analyze', 'validate', 'estimate'])
    parser.add_argument('--project', default='.', help='Project root')
    parser.add_argument('--plan', default='', help='Plan text to validate/estimate')

    args = parser.parse_args()

    writer = PlanWriter()

    if args.phase == 'analyze':
        result = writer.phase_analyze(args.project)
    elif args.phase == 'validate':
        result = writer.phase_validate(args.plan)
    elif args.phase == 'estimate':
        result = writer.phase_estimate(args.plan)
    else:
        result = {'error': 'Unknown phase'}

    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
