#!/usr/bin/env python3
"""
Wrapper script: Runs analyzer and planner in sequence.
Outputs CODEBASE CONTEXT followed by PLAN DECISIONS JSON.

Usage: python analyze_and_plan.py "task description @/path/to/project"
"""

import subprocess
import sys
import json
import os

def main():
    """Run analyzer, capture output, pipe to planner, output both."""

    if not sys.argv[1:]:
        print("Usage: python analyze_and_plan.py 'task description @/path/to/project'")
        sys.exit(1)

    # Build analyzer command
    analyzer_script = os.path.join(os.path.dirname(__file__), 'analyze_codebase.py')
    planner_script = os.path.join(os.path.dirname(__file__), 'plan_decisions.py')

    arguments = ' '.join(sys.argv[1:])

    # Step 1: Run analyzer
    try:
        result = subprocess.run(
            ['python', analyzer_script, arguments],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            print(f"Analyzer error: {result.stderr}")
            sys.exit(1)

        codebase_context = result.stdout

    except subprocess.TimeoutExpired:
        print("Analyzer timed out")
        sys.exit(1)
    except Exception as e:
        print(f"Analyzer failed: {e}")
        sys.exit(1)

    # Step 2: Pipe analyzer output to planner
    try:
        result = subprocess.run(
            ['python', planner_script],
            input=codebase_context,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            print(f"Planner error: {result.stderr}")
            sys.exit(1)

        plan_decisions = result.stdout

    except subprocess.TimeoutExpired:
        print("Planner timed out")
        sys.exit(1)
    except Exception as e:
        print(f"Planner failed: {e}")
        sys.exit(1)

    # Step 3: Output both (context first, then decisions)
    print(codebase_context)
    print("\n---\n")
    print("## PLAN DECISIONS")
    print()

    # Parse JSON and format as table
    try:
        decisions = json.loads(plan_decisions)

        # Print table header
        print("| Decision | Choice | Score | Reasoning |")
        print("|----------|--------|-------|-----------|")

        # Decision labels (human-readable)
        labels = {
            'async_sync': 'Async/Sync',
            'persistence': 'Persistence',
            'testing': 'Testing',
            'error_handling': 'Error Handling',
            'logging': 'Logging',
            'validation': 'Validation'
        }

        # Print each decision as table row
        for key, label in labels.items():
            if key in decisions:
                d = decisions[key]
                choice = d.get('choice', 'unknown')
                score = d.get('score', 0)
                reasoning = '; '.join(d.get('reasoning', []))

                # Truncate reasoning if too long
                if len(reasoning) > 50:
                    reasoning = reasoning[:47] + '...'

                print(f"| {label} | {choice} | {score}/10 | {reasoning} |")

        # Show confidence level
        avg_score = sum(d.get('score', 0) for d in decisions.values()) / len(decisions)
        confidence = "High" if avg_score >= 8 else "Medium" if avg_score >= 6 else "Low"

        print()
        print(f"**Confidence:** {confidence} ({avg_score:.1f}/10 average)")

    except json.JSONDecodeError:
        # If JSON parsing fails, just output the raw output
        print(plan_decisions)


if __name__ == '__main__':
    main()
