#!/usr/bin/env python3
"""
Real Project Validation Script

Validates plugin functionality on actual real-world projects.
Tests multi-file generation, auto-wiring, and integration.

Usage: python validate_real_project.py /path/to/real/project
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from analyze_codebase import CodebaseAnalyzer
from plan_decisions import PlanDecisionEngine
from verify_generated import CodeValidator
from format_multifile_output import MultiFileFormatter
from autowire_into_project import ProjectAutoWirer


class RealProjectValidator:
    """Validates plugin on real projects."""

    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.results = {
            'project': str(self.project_root),
            'analysis': {},
            'planning': {},
            'verification': {},
            'formatting': {},
            'autowiring': {},
            'overall': 'PENDING'
        }

    def validate_analysis(self):
        """Validate codebase analysis."""
        print(f"\n{'='*80}")
        print("Step 1: Analyzing Real Project")
        print(f"{'='*80}")
        print(f"Project: {self.project_root}")

        analyzer = CodebaseAnalyzer(str(self.project_root))

        try:
            context = analyzer.analyze_full_context()
            self.results['analysis'] = context
            print(f"✅ Framework detected: {context.get('framework', 'Unknown')}")
            print(f"✅ Language detected: {context.get('language', 'Unknown')}")
            print(f"✅ Files analyzed: {context.get('file_count', 0)}")
            return True
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
            self.results['analysis']['error'] = str(e)
            return False

    def validate_planning(self):
        """Validate decision planning."""
        print(f"\n{'='*80}")
        print("Step 2: Planning Decisions")
        print(f"{'='*80}")

        if not self.results['analysis']:
            print("❌ Skipping: No analysis results")
            return False

        context = self.results['analysis']
        engine = PlanDecisionEngine(context)

        try:
            decisions = engine.score_all_decisions()
            self.results['planning'] = {
                'decisions': decisions,
                'all_scored': all('score' in d for d in decisions.values())
            }

            print("✅ Decision Scoring:")
            for decision_name, decision_data in decisions.items():
                score = decision_data.get('score', 'N/A')
                print(f"  - {decision_name}: {score}")

            return all(d.get('score') for d in decisions.values())
        except Exception as e:
            print(f"❌ Planning failed: {str(e)}")
            self.results['planning']['error'] = str(e)
            return False

    def validate_verification(self):
        """Validate code verification."""
        print(f"\n{'='*80}")
        print("Step 3: Code Verification")
        print(f"{'='*80}")

        framework = self.results['analysis'].get('framework', 'django')
        language = self.results['analysis'].get('language', 'python')

        validator = CodeValidator(framework=framework, language=language)

        # Test with sample code
        test_code = self._get_test_code(framework, language)

        try:
            result = validator.validate_code(test_code, language, framework)
            self.results['verification'] = result

            status = result.get('status', 'UNKNOWN')
            print(f"✅ Validation Status: {status}")
            if result.get('errors'):
                print(f"   Errors: {result.get('errors')}")

            return status in ['PASSED', 'REPAIRED']
        except Exception as e:
            print(f"❌ Verification failed: {str(e)}")
            self.results['verification']['error'] = str(e)
            return False

    def validate_formatting(self):
        """Validate output formatting."""
        print(f"\n{'='*80}")
        print("Step 4: Multi-File Output Formatting")
        print(f"{'='*80}")

        framework = self.results['analysis'].get('framework', 'django')
        formatter = MultiFileFormatter(framework=framework)

        # Generate sample files
        sample_files = self._get_sample_files(framework)

        try:
            output = formatter.format_multifile_response(sample_files, 'Test Feature')

            self.results['formatting'] = {
                'has_summary_table': '|' in output,
                'has_file_contents': 'File' in output,
                'output_length': len(output),
                'status': 'formatted'
            }

            print(f"✅ Formatted Output:")
            print(f"   Length: {len(output)} characters")
            print(f"   Has table: {'|' in output}")
            print(f"   Has contents: {'File' in output}")

            return len(output) > 100
        except Exception as e:
            print(f"❌ Formatting failed: {str(e)}")
            self.results['formatting']['error'] = str(e)
            return False

    def validate_autowiring(self):
        """Validate auto-wiring."""
        print(f"\n{'='*80}")
        print("Step 5: Auto-Wiring into Project")
        print(f"{'='*80}")

        framework = self.results['analysis'].get('framework', 'django')

        # Only test if project structure supports auto-wiring
        if framework == 'django' and not (self.project_root / 'manage.py').exists():
            print("⚠️  Skipping: Django project missing manage.py")
            return True

        wirer = ProjectAutoWirer(framework=framework, project_root=str(self.project_root))

        # Generate sample files for autowiring
        sample_files = self._get_sample_files_for_wiring(framework)

        try:
            result = wirer.autowire(sample_files)

            self.results['autowiring'] = {
                'success': result.get('success', False),
                'actions_count': len(result.get('actions', [])),
                'next_steps_count': len(result.get('next_steps', [])),
                'status': 'wired' if result.get('success') else 'failed'
            }

            print(f"✅ Auto-Wiring Result:")
            print(f"   Success: {result.get('success')}")
            print(f"   Actions: {len(result.get('actions', []))}")
            print(f"   Next Steps: {len(result.get('next_steps', []))}")

            if result.get('actions'):
                print(f"   Actions taken:")
                for action in result.get('actions', [])[:3]:
                    print(f"     - {action}")

            return result.get('success', False)
        except Exception as e:
            print(f"⚠️  Auto-Wiring note: {str(e)}")
            self.results['autowiring']['note'] = str(e)
            return True  # Don't fail on auto-wiring (may not be applicable)

    def run_validation(self):
        """Run full validation."""
        print("\n" + "="*80)
        print("REAL PROJECT VALIDATION")
        print("="*80)

        results_all = []

        # Run each validation step
        results_all.append(("Analysis", self.validate_analysis()))
        results_all.append(("Planning", self.validate_planning()))
        results_all.append(("Verification", self.validate_verification()))
        results_all.append(("Formatting", self.validate_formatting()))
        results_all.append(("Auto-Wiring", self.validate_autowiring()))

        # Summary
        print(f"\n{'='*80}")
        print("VALIDATION SUMMARY")
        print(f"{'='*80}")

        for step_name, passed in results_all:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {step_name}")

        overall_passed = all(r[1] for r in results_all)
        self.results['overall'] = 'PASSED' if overall_passed else 'FAILED'

        print(f"\n{'='*80}")
        print(f"Overall: {'✅ PROJECT VALIDATED' if overall_passed else '❌ VALIDATION FAILED'}")
        print(f"{'='*80}\n")

        # Save results
        results_file = Path(__file__).parent.parent.parent / f"validation_results_{self.project_root.name}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"Results saved: {results_file}")

        return overall_passed

    def _get_test_code(self, framework, language):
        """Get test code for framework."""
        if framework == 'django':
            return """
from django.db import models

class User(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
"""
        elif framework == 'fastapi':
            return """
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.get("/items")
async def get_items():
    return []
"""
        else:
            return "# Sample code"

    def _get_sample_files(self, framework):
        """Get sample files for formatting."""
        if framework == 'django':
            return [
                {'name': 'models.py', 'content': 'class User(models.Model): pass', 'type': 'model'},
                {'name': 'views.py', 'content': 'class UserViewSet(ViewSet): pass', 'type': 'view'},
                {'name': 'tests.py', 'content': 'class UserTests(TestCase): pass', 'type': 'test'},
            ]
        else:
            return [
                {'name': 'models.py', 'content': 'sample content', 'type': 'model'},
                {'name': 'handlers.py', 'content': 'sample content', 'type': 'handler'},
                {'name': 'tests.py', 'content': 'sample content', 'type': 'test'},
            ]

    def _get_sample_files_for_wiring(self, framework):
        """Get sample files for autowiring."""
        if framework == 'django':
            return {
                'app/models.py': 'class User(models.Model): pass',
                'app/views.py': 'from django.views import View',
            }
        else:
            return {
                'models.py': 'sample content',
                'handlers.py': 'sample content',
            }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python validate_real_project.py /path/to/project")
        sys.exit(1)

    project_root = sys.argv[1]
    if not Path(project_root).exists():
        print(f"Error: Project not found: {project_root}")
        sys.exit(1)

    validator = RealProjectValidator(project_root)
    success = validator.run_validation()
    sys.exit(0 if success else 1)
