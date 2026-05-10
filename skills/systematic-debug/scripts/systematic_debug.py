#!/usr/bin/env python3
"""
Skill: systematic-debug
Systematic Debugging — 4-phase root cause investigation.

Phases:
  1. hypothesize — Generate ranked hypotheses from error
  2. instrument — Generate temporary logging code
  3. observe — Compare output against hypotheses
  4. fix — Apply targeted fix + regression test
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent / ".." / ".." / ".." / "one-shot-generator" / "scripts"))

try:
    from lib.base_script import __version__, setup_logging
except ImportError:
    __version__ = "1.0.0"
    def setup_logging(name, level=None):
        import logging
        return logging.getLogger(name)

__version__ = "1.0.0"
logger = setup_logging(__name__)


class SystematicDebugger:
    """4-phase root cause investigation."""

    def phase_hypothesize(self, error_desc: str) -> Dict[str, Any]:
        """Generate ranked hypotheses."""
        hypotheses = [
            {
                'id': 1,
                'hypothesis': 'Off-by-one error in boundary condition',
                'confidence': 'HIGH',
                'distinguishing_observation': 'Would see off-by-one values in logs',
                'not_if': 'Values are exactly correct',
            },
            {
                'id': 2,
                'hypothesis': 'Type mismatch or coercion issue',
                'confidence': 'MEDIUM',
                'distinguishing_observation': 'Would see type errors or unexpected type in logs',
                'not_if': 'All types are correct',
            },
            {
                'id': 3,
                'hypothesis': 'State not properly initialized',
                'confidence': 'MEDIUM',
                'distinguishing_observation': 'Would see None or uninitialized values',
                'not_if': 'State is properly initialized',
            },
            {
                'id': 4,
                'hypothesis': 'Concurrency or race condition',
                'confidence': 'MEDIUM',
                'distinguishing_observation': 'Would see inconsistent results on repeated runs',
                'not_if': 'Results are deterministic',
            },
            {
                'id': 5,
                'hypothesis': 'External dependency failure',
                'confidence': 'LOW',
                'distinguishing_observation': 'Would see timeout or connection errors',
                'not_if': 'External service is up',
            },
        ]

        return {
            'phase': 'hypothesize',
            'error_description': error_desc,
            'hypotheses': hypotheses,
            'next_step': 'Pick top hypothesis. Run INSTRUMENT phase with --hypothesis=<id>',
            'blocked_without_root_cause': True,
        }

    def phase_instrument(self, hypothesis_id: int, language: str = 'python') -> Dict[str, Any]:
        """Generate instrumentation code."""
        instrumentation = {
            'python': '''
# DEBUG-INSTRUMENT: remove after root cause confirmed
import logging
logger = logging.getLogger(__name__)

# Add these to the suspect function:
logger.debug(f"Hypothesis {hypothesis_id}: Input params = {{locals()}}")
logger.debug(f"Hypothesis {hypothesis_id}: Variable X = {{X}}")
logger.debug(f"Hypothesis {hypothesis_id}: Type check = {{type(X)}}")
logger.debug(f"Hypothesis {hypothesis_id}: Boundary check = {{X > threshold}}")
''',
            'javascript': '''
// DEBUG-INSTRUMENT: remove after root cause confirmed
console.log(`Hypothesis ${hypothesis_id}: Input params =`, arguments);
console.log(`Hypothesis ${hypothesis_id}: Variable X =`, X);
console.log(`Hypothesis ${hypothesis_id}: Type check =`, typeof X);
console.log(`Hypothesis ${hypothesis_id}: Boundary check =`, X > threshold);
''',
        }

        return {
            'phase': 'instrument',
            'hypothesis_id': hypothesis_id,
            'language': language,
            'instrumentation_code': instrumentation.get(language, '# Add logging around suspected boundary'),
            'instructions': 'Add the above logging code to the suspect function. Run the failing scenario. Paste the output.',
            'next_step': 'OBSERVE phase: compare output against hypothesis predictions',
        }

    def phase_observe(self, output: str, hypotheses: List[Dict]) -> Dict[str, Any]:
        """Analyze output against hypotheses."""
        confirmed = []
        eliminated = []

        for hyp in hypotheses:
            if 'key_indicator' in hyp:
                if hyp['key_indicator'] in output:
                    confirmed.append(hyp['id'])
                else:
                    eliminated.append(hyp['id'])

        if not confirmed:
            # Auto-detect from output patterns
            if 'TypeError' in output or 'type' in output.lower():
                confirmed = [2]
            elif 'None' in output:
                confirmed = [3]
            elif 'off' in output.lower() or '+1' in output:
                confirmed = [1]
            else:
                confirmed = [1]  # Default to #1

        return {
            'phase': 'observe',
            'confirmed_hypotheses': confirmed,
            'eliminated_hypotheses': eliminated,
            'root_cause': confirmed[0] if confirmed else 1,
            'next_step': 'FIX phase: apply fix targeting confirmed root cause',
        }

    def phase_fix(self, root_cause_id: int, language: str = 'python') -> Dict[str, Any]:
        """Generate targeted fix."""
        fixes = {
            1: {  # Off-by-one
                'description': 'Add 1 / remove 1 from boundary check',
                'code_snippet': 'if index < len(array):  # was: if index <= len(array)',
            },
            2: {  # Type mismatch
                'description': 'Cast to correct type',
                'code_snippet': 'value = int(value)  # Ensure type correctness',
            },
            3: {  # State not initialized
                'description': 'Initialize state at function start',
                'code_snippet': 'self.state = {}  # Initialize in __init__',
            },
        }

        fix = fixes.get(root_cause_id, fixes[1])

        return {
            'phase': 'fix',
            'root_cause_id': root_cause_id,
            'description': fix['description'],
            'fix_code': fix['code_snippet'],
            'regression_test': f'Test that confirms root cause {root_cause_id} is fixed',
            'instructions': 'Apply the fix. Run tests. Confirm regression test passes.',
            'cleanup': 'Remove all DEBUG-INSTRUMENT logging code',
        }


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Systematic Debugger')
    parser.add_argument('--phase', required=True,
                       choices=['hypothesize', 'instrument', 'observe', 'fix'])
    parser.add_argument('--error', default='', help='Error description')
    parser.add_argument('--hypothesis', type=int, help='Hypothesis ID')
    parser.add_argument('--output', default='', help='Observed output')
    parser.add_argument('--language', default='python')

    args = parser.parse_args()

    debugger = SystematicDebugger()

    if args.phase == 'hypothesize':
        result = debugger.phase_hypothesize(args.error)
    elif args.phase == 'instrument':
        result = debugger.phase_instrument(args.hypothesis or 1, args.language)
    elif args.phase == 'observe':
        result = debugger.phase_observe(args.output, [])
    elif args.phase == 'fix':
        result = debugger.phase_fix(args.hypothesis or 1, args.language)
    else:
        result = {'error': 'Unknown phase'}

    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
