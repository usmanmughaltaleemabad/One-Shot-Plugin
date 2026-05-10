#!/usr/bin/env python3
"""
Orchestrate optional harness modules based on command-line flags.

Parses arguments for flags like --preview, --tdd, --review, --strangler, etc.
and invokes the corresponding Python modules, formatting output for SKILL.md.

Usage:
  python orchestrate_harness_modules.py "[description]" "@/path" "--tdd --review"

Returns: JSON with module outputs keyed by module name for SKILL.md to integrate
"""

import sys
import json
import re
from pathlib import Path


def parse_flags(arguments: str) -> dict:
    """Extract flags from arguments string."""
    flags = {}

    # Match flag patterns
    patterns = {
        'preview': r'--preview\b',
        'tdd': r'--tdd\b',
        'explain_tdd': r'--explain-tdd\b',
        'review': r'--review\b',
        'strangler': r'--strangler\b',
        'strangler_extract': r'--strangler-extract\b',
        'batch': r'--batch\b',
        'jobs': r'--jobs\b',
        'cli': r'--cli\b',
        'config': r'--config\b',
        'enterprise': r'--enterprise\b',
        'docs': r'--docs\b',
        'infra': r'--infra\b',
        'deploy': r'--deploy\b',
        'multi': r'--multi\b',
        'sidecar': r'--sidecar\b',
        'handlers': r'--handlers\b',
        'gen_tests': r'--gen-tests\b',
        'tour': r'--tour\b',
        'health_check': r'--health-check\b',
        'detect_bus': r'--detect-bus\b',
        'catalog': r'--catalog\s+(\S+)',
        'budget': r'--budget\s+(\d+)',
        'usage': r'--usage\b',
        'architecture': r'--architecture\s+"([^"]+)"',
        'debug': r'--debug\s+"([^"]+)"',
        'debug_prod': r'--debug-prod\b',
        'observability': r'--observability\s+(\S+)',
        'pr': r'--pr\b',
        'check_consistency': r'--check-consistency\b',
        'standardize': r'--standardize\b',
        'language': r'--language\s+(\S+)',
        'sys_debug': r'--sys-debug\s+"([^"]+)"',
        'write_plan': r'--plan\s+"([^"]+)"',
        'execute_plan': r'--execute-plan\s+(\S+)',
        'verify_complete': r'--verify-complete\b',
    }

    for flag_name, pattern in patterns.items():
        match = re.search(pattern, arguments)
        if match:
            if match.groups():
                flags[flag_name] = match.group(1)
            else:
                flags[flag_name] = True

    return flags


def get_module_path(module_name: str) -> Path:
    """Get path to module script."""
    script_dir = Path(__file__).parent
    return script_dir / f"{module_name}.py"


def load_module_output(module_name: str, flags: dict, arguments: str) -> dict:
    """
    Load output from a harness module.
    Returns dict with 'status', 'output', or 'error'.
    """
    try:
        module_path = get_module_path(module_name)
        if not module_path.exists():
            return {'status': 'not_found', 'message': f'{module_name} not implemented yet'}

        # For now, return placeholder
        # In real implementation, would import and call module functions
        return {
            'status': 'pending',
            'message': f'{module_name} module available but not yet wired'
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'No arguments provided'}))
        sys.exit(1)

    arguments = sys.argv[1]
    flags = parse_flags(arguments)

    # Output flags for SKILL.md to use
    result = {
        'flags': flags,
        'modules_to_invoke': []
    }

    # Map flags to modules
    flag_module_map = {
        'preview': 'preview_mode',
        'tdd': 'tdd_mode',
        'review': 'code_review_automation',
        'strangler': 'strangler_analyzer',  # v1.0: monolith analysis
        'strangler_extract': 'strangler_extractor',  # v1.0: microservice generation
        'batch': 'batch_jobs_generator',  # v2.0: Phase 3 batch job specialist
        'jobs': 'batch_jobs_generator',  # v2.0: Phase 3 batch job specialist
        'cli': 'generate_cli_scaffold',  # Gap 4: CLI scaffolding
        'config': 'generate_framework_configs',  # Gap 5: Config generation
        'enterprise': 'generate_enterprise_configs',  # Gap 7: Enterprise configs
        'docs': 'generate_openapi_docs',  # Gap 8: OpenAPI docs
        'infra': 'phase4_infrastructure',  # Phase 4: Infrastructure orchestration
        'deploy': 'phase4_infrastructure',  # Phase 4: Infrastructure orchestration
        'multi': 'multi_sidecar_orchestration',  # Gap 6: Multi-handler orchestration
        'sidecar': 'multi_sidecar_orchestration',  # Gap 6: Multi-handler orchestration
        'handlers': 'generate_handlers_orchestration',  # Gap 6: Handler generation
        'gen_tests': 'generate_comprehensive_tests',  # Test generation
        'detect_bus': 'detect_message_bus',
        'catalog': 'event_catalog',
        'architecture': 'architecture_design',
        'debug': 'debugging_helpers',
        'debug_prod': 'production_debugger',
        'health_check': 'health_check',
        'tour': 'interactive_tour',
        'budget': 'cost_management',
        'pr': 'pr_integration',
        'check_consistency': 'consistency_checker',
        # Superpowers skills (Phase 4+)
        'sys_debug': 'systematic_debug',
        'write_plan': 'plan_writer',
        'execute_plan': 'plan_executor',
        'verify_complete': 'completion_gate',
    }

    for flag, module in flag_module_map.items():
        if flag in flags:
            result['modules_to_invoke'].append({
                'flag': flag,
                'module': module,
                'value': flags[flag] if isinstance(flags[flag], str) else True
            })

    print(json.dumps(result))


if __name__ == '__main__':
    main()
