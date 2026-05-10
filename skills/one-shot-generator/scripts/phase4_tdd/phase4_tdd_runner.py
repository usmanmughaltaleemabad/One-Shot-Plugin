#!/usr/bin/env python3
"""Phase 4.2: TDD Cycle Integration Orchestrator"""

import sys
import argparse
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.base_script import setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class Phase4TDDRunner:
    """Orchestrates Phase 4.2 TDD module generation."""

    TDD_MODULES = {
        'property_tests': 'Property-Based Testing',
        'mutation_testing': 'Mutation Testing',
        'contract_tests': 'Consumer-Driven Contracts',
    }

    def __init__(self, framework: str, tdd_type: str = 'all'):
        self.framework = framework.lower()
        self.tdd_type = tdd_type.lower()

    def run(self) -> Dict[str, str]:
        """Generate TDD framework(s)."""
        files = {}

        if self.tdd_type == 'all':
            tdd_types = self.TDD_MODULES.keys()
        else:
            tdd_types = [self.tdd_type]

        for ttype in tdd_types:
            if ttype not in self.TDD_MODULES:
                logger.warning(f"Unknown TDD type: {ttype}")
                continue

            logger.info(f"Generating {self.TDD_MODULES[ttype]}")

            if ttype == 'property_tests':
                files.update(self._generate_property_tests())
            elif ttype == 'mutation_testing':
                files.update(self._generate_mutation_testing())
            elif ttype == 'contract_tests':
                files.update(self._generate_contract_tests())

        return files

    def _generate_property_tests(self) -> Dict[str, str]:
        from property_test_generator import PropertyTestGenerator
        gen = PropertyTestGenerator(self.framework)
        return gen.generate()

    def _generate_mutation_testing(self) -> Dict[str, str]:
        from mutation_test_runner import MutationTestRunner
        gen = MutationTestRunner(self.framework)
        return gen.generate()

    def _generate_contract_tests(self) -> Dict[str, str]:
        from contract_test_generator import ContractTestGenerator
        gen = ContractTestGenerator(self.framework)
        return gen.generate()


def main():
    parser = argparse.ArgumentParser(description='Phase 4.2: TDD Cycle Integration')
    parser.add_argument('--framework', required=True, choices=['django', 'fastapi', 'spring', 'go', 'nodejs'])
    parser.add_argument('--tdd', default='all', choices=['all', 'property_tests', 'mutation_testing', 'contract_tests'])
    parser.add_argument('--output-dir', default='./generated')

    args = parser.parse_args()

    with timed_run("phase4_tdd_runner") as timer:
        logger.info(f"Generating {args.tdd} TDD for {args.framework}")
        runner = Phase4TDDRunner(args.framework, args.tdd)
        files = runner.run()
        logger.info(f"Generated {len(files)} TDD files")
        print(f"✅ Phase 4.2 TDD Cycle: {len(files)} files")
        check_budget("phase4_tdd_runner", timer.elapsed_ms, logger)


if __name__ == '__main__':
    main()
