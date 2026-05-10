#!/usr/bin/env python3
"""Phase 4.3: Cost Optimization Orchestrator"""

import sys
import argparse
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.base_script import setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class Phase4CostRunner:
    """Orchestrates Phase 4.3 Cost Optimization."""

    COST_MODULES = {
        'lambda': 'Lambda Optimization',
        'database': 'Database Query Optimization',
        'caching': 'Caching Strategies',
        'cdn': 'CDN Configuration',
        'autoscaling': 'Autoscaling',
    }

    def __init__(self, framework: str, cost_type: str = 'all'):
        self.framework = framework.lower()
        self.cost_type = cost_type.lower()

    def run(self) -> Dict[str, str]:
        """Generate cost optimization framework(s)."""
        files = {}

        if self.cost_type == 'all':
            cost_types = self.COST_MODULES.keys()
        else:
            cost_types = [self.cost_type]

        for ctype in cost_types:
            if ctype not in self.COST_MODULES:
                logger.warning(f"Unknown cost type: {ctype}")
                continue

            logger.info(f"Generating {self.COST_MODULES[ctype]}")

            if ctype == 'lambda':
                files.update(self._generate_lambda())
            elif ctype == 'database':
                files.update(self._generate_database())
            elif ctype == 'caching':
                files.update(self._generate_caching())
            elif ctype == 'cdn':
                files.update(self._generate_cdn())
            elif ctype == 'autoscaling':
                files.update(self._generate_autoscaling())

        return files

    def _generate_lambda(self) -> Dict[str, str]:
        from lambda_optimizer import LambdaOptimizer
        gen = LambdaOptimizer(self.framework)
        return gen.generate()

    def _generate_database(self) -> Dict[str, str]:
        from database_query_optimizer import DatabaseQueryOptimizer
        gen = DatabaseQueryOptimizer(self.framework)
        return gen.generate()

    def _generate_caching(self) -> Dict[str, str]:
        from caching_strategy_generator import CachingStrategyGenerator
        gen = CachingStrategyGenerator(self.framework)
        return gen.generate()

    def _generate_cdn(self) -> Dict[str, str]:
        from cdn_config_generator import CDNConfigGenerator
        gen = CDNConfigGenerator(self.framework)
        return gen.generate()

    def _generate_autoscaling(self) -> Dict[str, str]:
        from autoscaling_generator import AutoscalingGenerator
        gen = AutoscalingGenerator(self.framework)
        return gen.generate()


def main():
    parser = argparse.ArgumentParser(description='Phase 4.3: Cost Optimization')
    parser.add_argument('--framework', required=True, choices=['django', 'fastapi', 'spring', 'go', 'nodejs'])
    parser.add_argument('--cost', default='all', choices=['all', 'lambda', 'database', 'caching', 'cdn', 'autoscaling'])
    parser.add_argument('--output-dir', default='./generated')

    args = parser.parse_args()

    with timed_run("phase4_cost_runner") as timer:
        logger.info(f"Generating {args.cost} cost optimization for {args.framework}")
        runner = Phase4CostRunner(args.framework, args.cost)
        files = runner.run()
        logger.info(f"Generated {len(files)} cost optimization files")
        print(f"✅ Phase 4.3 Cost Optimization: {len(files)} files")
        check_budget("phase4_cost_runner", timer.elapsed_ms, logger)


if __name__ == '__main__':
    main()
