#!/usr/bin/env python3
"""Phase 4.5: Enterprise Compliance Orchestrator (v0.7.0)

Routes compliance requests to specialized generators:
- SOC 2 Type II controls
- HIPAA PHI protection
- GDPR data handling
- PII detection and masking
- Secrets rotation and vault integration
"""

import sys
import argparse
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.base_script import setup_logging, timed_run, check_budget
from format_multifile_output import format_multifile_response

__version__ = "0.7.0"
logger = setup_logging(__name__)


class Phase4ComplianceRunner:
    """Orchestrates Phase 4.5 compliance module generation."""

    COMPLIANCE_FRAMEWORKS = {
        'soc2': 'SOC 2 Type II Compliance',
        'hipaa': 'HIPAA PHI Protection',
        'gdpr': 'GDPR Data Protection',
        'pii': 'PII Detection & Masking',
        'secrets': 'Secrets Rotation & Vault',
    }

    def __init__(self, framework: str, compliance_type: str = 'all'):
        self.framework = framework.lower()
        self.compliance_type = compliance_type.lower()

    def run(self) -> Dict[str, str]:
        """Generate compliance framework(s)."""
        files = {}

        if self.compliance_type == 'all':
            # Generate all compliance frameworks
            compliance_types = self.COMPLIANCE_FRAMEWORKS.keys()
        else:
            compliance_types = [self.compliance_type]

        for ctype in compliance_types:
            if ctype not in self.COMPLIANCE_FRAMEWORKS:
                logger.warning(f"Unknown compliance type: {ctype}")
                continue

            logger.info(f"Generating {self.COMPLIANCE_FRAMEWORKS[ctype]}")

            if ctype == 'soc2':
                files.update(self._generate_soc2())
            elif ctype == 'hipaa':
                files.update(self._generate_hipaa())
            elif ctype == 'gdpr':
                files.update(self._generate_gdpr())
            elif ctype == 'pii':
                files.update(self._generate_pii())
            elif ctype == 'secrets':
                files.update(self._generate_secrets())

        return files

    def _generate_soc2(self) -> Dict[str, str]:
        """Generate SOC 2 compliance files."""
        from soc2_generator import SOC2Generator
        gen = SOC2Generator(self.framework)
        return gen.generate()

    def _generate_hipaa(self) -> Dict[str, str]:
        """Generate HIPAA compliance files."""
        from hipaa_generator import HIPAAGenerator
        gen = HIPAAGenerator(self.framework)
        return gen.generate()

    def _generate_gdpr(self) -> Dict[str, str]:
        """Generate GDPR compliance files."""
        from gdpr_generator import GDPRGenerator
        gen = GDPRGenerator(self.framework)
        return gen.generate()

    def _generate_pii(self) -> Dict[str, str]:
        """Generate PII detection files."""
        from pii_detector_generator import PIIDetectorGenerator
        gen = PIIDetectorGenerator(self.framework)
        return gen.generate()

    def _generate_secrets(self) -> Dict[str, str]:
        """Generate secrets management files."""
        from secrets_rotation_generator import SecretsRotationGenerator
        gen = SecretsRotationGenerator(self.framework)
        return gen.generate()

    @staticmethod
    def _vault_config() -> str:
        return '''"""HashiCorp Vault Configuration for Secrets Management"""

VAULT_CONFIG = {
    "address": "http://vault:8200",
    "engine": "kv/v2",
    "secret_paths": {
        "database": "secret/data/database/credentials",
        "api_keys": "secret/data/api/keys",
        "certificates": "secret/data/certificates",
    },
    "auth_method": "token",  # or "oidc", "jwt", "kubernetes"
}
'''

    @staticmethod
    def _rotation_schedule() -> str:
        return '''"""Secrets Rotation Schedule"""

ROTATION_SCHEDULE = {
    "database_password": {"days": 30, "grace_period_days": 7},
    "api_keys": {"days": 90, "grace_period_days": 14},
    "certificates": {"days": 365, "grace_period_days": 30},
    "tls_secrets": {"days": 30, "grace_period_days": 3},
}

# Run rotation check:
# 0 2 * * * /opt/scripts/check_secrets_rotation.sh
# Run rotation:
# 0 3 * * 1 /opt/scripts/rotate_secrets.sh
'''


def main():
    parser = argparse.ArgumentParser(
        description='Phase 4.5: Enterprise Compliance Framework Generator'
    )
    parser.add_argument(
        '--framework',
        required=True,
        choices=['django', 'fastapi', 'spring', 'go', 'nodejs'],
        help='Target framework'
    )
    parser.add_argument(
        '--compliance',
        default='all',
        choices=['all', 'soc2', 'hipaa', 'gdpr', 'pii', 'secrets'],
        help='Compliance framework to generate'
    )
    parser.add_argument(
        '--output-dir',
        default='./generated',
        help='Output directory for generated files'
    )

    args = parser.parse_args()

    with timed_run("phase4_compliance_runner") as timer:
        logger.info(f"Generating {args.compliance} compliance for {args.framework}")

        runner = Phase4ComplianceRunner(args.framework, args.compliance)
        files = runner.run()

        logger.info(f"Generated {len(files)} compliance files")

        # Format for output
        output = format_multifile_response(
            files,
            args.framework,
            f"{args.compliance.upper()} Compliance Framework"
        )

        print(output)
        check_budget("phase4_compliance_runner", timer.elapsed_ms, logger)

    logger.info(f"Phase 4.5 completed in {timer.elapsed_ms:.0f}ms")


if __name__ == '__main__':
    main()
