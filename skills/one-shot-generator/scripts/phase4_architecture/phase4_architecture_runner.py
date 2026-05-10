#!/usr/bin/env python3
"""Phase 4.1: Architecture Design Orchestrator (v0.7.0)

Routes architecture requests to specialized generators:
- DDD (Domain-Driven Design)
- CQRS (Command Query Responsibility Segregation)
- Event Sourcing (Immutable event log)
- Sagas (Distributed transactions)
- Hexagonal (Ports & Adapters)
"""

import sys
import argparse
from pathlib import Path
from typing import Dict

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.base_script import setup_logging, timed_run, check_budget
from format_multifile_output import format_multifile_response

__version__ = "0.7.0"
logger = setup_logging(__name__)


class Phase4ArchitectureRunner:
    """Orchestrates Phase 4.1 architecture module generation."""

    ARCHITECTURE_MODULES = {
        'ddd': 'Domain-Driven Design',
        'cqrs': 'Command Query Responsibility Segregation',
        'event_sourcing': 'Event Sourcing',
        'saga': 'Distributed Transaction Sagas',
        'hexagonal': 'Hexagonal Architecture (Ports & Adapters)',
    }

    def __init__(self, framework: str, arch_type: str = 'all'):
        self.framework = framework.lower()
        self.arch_type = arch_type.lower()

    def run(self) -> Dict[str, str]:
        """Generate architecture framework(s)."""
        files = {}

        if self.arch_type == 'all':
            # Generate all architecture modules
            arch_types = self.ARCHITECTURE_MODULES.keys()
        else:
            arch_types = [self.arch_type]

        for atype in arch_types:
            if atype not in self.ARCHITECTURE_MODULES:
                logger.warning(f"Unknown architecture type: {atype}")
                continue

            logger.info(f"Generating {self.ARCHITECTURE_MODULES[atype]}")

            if atype == 'ddd':
                files.update(self._generate_ddd())
            elif atype == 'cqrs':
                files.update(self._generate_cqrs())
            elif atype == 'event_sourcing':
                files.update(self._generate_event_sourcing())
            elif atype == 'saga':
                files.update(self._generate_saga())
            elif atype == 'hexagonal':
                files.update(self._generate_hexagonal())

        return files

    def _generate_ddd(self) -> Dict[str, str]:
        """Generate DDD module."""
        from ddd_generator import DDDGenerator
        gen = DDDGenerator(self.framework)
        return gen.generate()

    def _generate_cqrs(self) -> Dict[str, str]:
        """Generate CQRS module."""
        from cqrs_generator import CQRSGenerator
        gen = CQRSGenerator(self.framework)
        return gen.generate()

    def _generate_event_sourcing(self) -> Dict[str, str]:
        """Generate Event Sourcing module."""
        from event_sourcing_generator import EventSourcingGenerator
        gen = EventSourcingGenerator(self.framework)
        return gen.generate()

    def _generate_saga(self) -> Dict[str, str]:
        """Generate Saga module."""
        from saga_generator import SagaGenerator
        gen = SagaGenerator(self.framework)
        return gen.generate()

    def _generate_hexagonal(self) -> Dict[str, str]:
        """Generate Hexagonal module."""
        from hexagonal_generator import HexagonalGenerator
        gen = HexagonalGenerator(self.framework)
        return gen.generate()


def main():
    parser = argparse.ArgumentParser(
        description='Phase 4.1: Architecture Design Framework Generator'
    )
    parser.add_argument(
        '--framework',
        required=True,
        choices=['django', 'fastapi', 'spring', 'go', 'nodejs'],
        help='Target framework'
    )
    parser.add_argument(
        '--architecture',
        default='all',
        choices=['all', 'ddd', 'cqrs', 'event_sourcing', 'saga', 'hexagonal'],
        help='Architecture pattern to generate'
    )
    parser.add_argument(
        '--output-dir',
        default='./generated',
        help='Output directory for generated files'
    )

    args = parser.parse_args()

    with timed_run("phase4_architecture_runner") as timer:
        logger.info(f"Generating {args.architecture} architecture for {args.framework}")

        runner = Phase4ArchitectureRunner(args.framework, args.architecture)
        files = runner.run()

        logger.info(f"Generated {len(files)} architecture files")

        # Format for output
        output = format_multifile_response(
            files,
            args.framework,
            f"{args.architecture.upper()} Architecture Framework"
        )

        print(output)
        check_budget("phase4_architecture_runner", timer.elapsed_ms, logger)

    logger.info(f"Phase 4.1 completed in {timer.elapsed_ms:.0f}ms")


if __name__ == '__main__':
    main()
