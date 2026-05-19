#!/usr/bin/env python3
"""
Phase 4 Infrastructure Orchestrator - CLI Entry Point

Orchestrates enterprise infrastructure generation for:
- Docker containers
- Kubernetes clusters
- Terraform infrastructure
- CI/CD pipelines
- Monitoring and observability
- Security configurations
- Networking and load balancing
- Database infrastructure

Usage:
    python phase4_runner.py --framework django --language python --app-name myapp
    python phase4_runner.py --framework fastapi --app-name api-service --domain myapp.com
    python phase4_runner.py --framework spring --docker --kubernetes
"""

import argparse
import sys
import json
from pathlib import Path

# Add phase4_infrastructure to path
sys.path.insert(0, str(Path(__file__).parent / "phase4_infrastructure"))

from infrastructure_orchestrator import InfrastructureOrchestrator


class Phase4Runner:
    """Run Phase 4 infrastructure generation"""

    SUPPORTED_FRAMEWORKS = ["django", "fastapi", "spring", "go", "nodejs"]
    SUPPORTED_LANGUAGES = ["python", "javascript", "go", "java"]

    def __init__(self):
        self.parser = self._setup_parser()

    def _setup_parser(self) -> argparse.ArgumentParser:
        """Setup argument parser"""
        parser = argparse.ArgumentParser(
            description="Generate enterprise infrastructure (Phase 4)"
        )

        parser.add_argument(
            "--framework",
            choices=self.SUPPORTED_FRAMEWORKS,
            default="django",
            help="Framework to target"
        )

        parser.add_argument(
            "--language",
            choices=self.SUPPORTED_LANGUAGES,
            default="python",
            help="Programming language"
        )

        parser.add_argument(
            "--app-name",
            default="app",
            help="Application name (used in configs)"
        )

        parser.add_argument(
            "--domain",
            default="example.com",
            help="Domain name (used in networking configs)"
        )

        parser.add_argument(
            "--output-dir",
            default="./infrastructure",
            help="Output directory for generated files"
        )

        parser.add_argument(
            "--format",
            choices=["json", "files"],
            default="files",
            help="Output format"
        )

        parser.add_argument(
            "--docker",
            action="store_true",
            help="Only generate Docker configs"
        )

        parser.add_argument(
            "--kubernetes",
            action="store_true",
            help="Only generate Kubernetes configs"
        )

        parser.add_argument(
            "--terraform",
            action="store_true",
            help="Only generate Terraform configs"
        )

        parser.add_argument(
            "--cicd",
            action="store_true",
            help="Only generate CI/CD configs"
        )

        parser.add_argument(
            "--monitoring",
            action="store_true",
            help="Only generate monitoring configs"
        )

        parser.add_argument(
            "--security",
            action="store_true",
            help="Only generate security configs"
        )

        parser.add_argument(
            "--networking",
            action="store_true",
            help="Only generate networking configs"
        )

        parser.add_argument(
            "--database",
            action="store_true",
            help="Only generate database infrastructure configs"
        )

        parser.add_argument(
            "--all",
            action="store_true",
            help="Generate all infrastructure (default)"
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be generated without writing files"
        )

        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Verbose output"
        )

        return parser

    def run(self, args=None):
        """Run the generator"""
        try:
            parsed_args = self.parser.parse_args(args)
            self._validate_args(parsed_args)
            self._generate(parsed_args)
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _validate_args(self, args):
        """Validate arguments"""
        if args.framework not in self.SUPPORTED_FRAMEWORKS:
            raise ValueError(f"Unsupported framework: {args.framework}")

        if args.language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {args.language}")

    def _generate(self, args):
        """Generate the infrastructure"""
        if args.verbose:
            print(f"[Phase4] Generating infrastructure for {args.framework}/{args.language}")
            print(f"[Phase4] App name: {args.app_name}")
            print(f"[Phase4] Domain: {args.domain}")

        # Create orchestrator
        orchestrator = InfrastructureOrchestrator(
            framework=args.framework,
            language=args.language,
            app_name=args.app_name,
            domain=args.domain
        )

        # Generate infrastructure
        if args.docker:
            generated = {"docker": orchestrator.generate_docker()}
        elif args.kubernetes:
            generated = {"kubernetes": orchestrator.generate_kubernetes()}
        elif args.terraform:
            generated = {"terraform": orchestrator.generate_terraform()}
        elif args.cicd:
            generated = {"cicd": orchestrator.generate_cicd()}
        elif args.monitoring:
            generated = {"monitoring": orchestrator.generate_monitoring()}
        elif args.security:
            generated = {"security": orchestrator.generate_security()}
        elif args.networking:
            generated = {"networking": orchestrator.generate_networking()}
        elif args.database:
            generated = {"database": orchestrator.generate_database_infrastructure()}
        else:
            # Default: generate all
            generated = orchestrator.generate_all_infrastructure()

        # Output
        if args.format == "json":
            self._output_json(generated)
        else:
            self._output_files(generated, args)

        if args.verbose:
            total_files = sum(len(v) if isinstance(v, dict) else 1 for v in generated.values())
            print(f"[Phase4] Generated {total_files} files")

    def _output_json(self, files: dict):
        """Output as JSON"""
        # Flatten the nested structure
        flattened = {}
        for category, category_files in files.items():
            if isinstance(category_files, dict):
                for name, content in category_files.items():
                    flattened[f"{category}/{name}"] = content
            else:
                flattened[category] = category_files

        output = {
            "files": flattened,
            "count": len(flattened)
        }
        print(json.dumps(output, indent=2))

    def _output_files(self, files: dict, args):
        """Write files to disk"""
        output_dir = Path(args.output_dir)

        if not args.dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)

        total_written = 0
        for category, category_files in files.items():
            if isinstance(category_files, dict):
                category_dir = output_dir / category
                if not args.dry_run:
                    category_dir.mkdir(parents=True, exist_ok=True)

                for filename, content in category_files.items():
                    filepath = category_dir / filename
                    if args.dry_run:
                        print(f"Would create: {filepath}")
                    else:
                        filepath.parent.mkdir(parents=True, exist_ok=True)
                        filepath.write_text(content)
                        print(f"Created: {filepath}")
                        total_written += 1

        if not args.dry_run:
            print(f"\nGenerated {total_written} files in {output_dir}")
            print(f"\nNext steps:")
            print(f"1. Review generated files in {output_dir}/")
            print(f"2. Update domain/app name in configs as needed")
            print(f"3. Deploy using: terraform apply (for Terraform)")
            print(f"4. Deploy using: kubectl apply -f {output_dir}/kubernetes/ (for Kubernetes)")
            print(f"5. Deploy using: docker-compose up (for Docker)")


def main():
    """Main entry point"""
    runner = Phase4Runner()
    return runner.run()


if __name__ == '__main__':
    sys.exit(main())
