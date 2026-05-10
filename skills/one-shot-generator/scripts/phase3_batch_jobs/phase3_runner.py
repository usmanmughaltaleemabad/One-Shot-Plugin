"""
Phase 3 Runner - Entry point for batch job specialist

Usage:
    python phase3_runner.py --framework django --language python --job-name process_data
    python phase3_runner.py --framework fastapi --language python --job-name send_email
    python phase3_runner.py --framework spring --language python --queue-type celery
"""

import argparse
import sys
import json
from pathlib import Path
from orchestrator_phase3 import orchestrate_phase3, orchestrate_phase3_enhanced


class Phase3Runner:
    """Run Phase 3 batch job generation"""

    SUPPORTED_FRAMEWORKS = ["django", "fastapi", "spring", "go"]
    SUPPORTED_LANGUAGES = ["python", "javascript", "go", "java"]
    SUPPORTED_QUEUE_TYPES = ["celery", "rq", "bull", "gcloud_tasks", "sqs"]

    def __init__(self):
        self.parser = self._setup_parser()

    def _setup_parser(self) -> argparse.ArgumentParser:
        """Setup argument parser"""
        parser = argparse.ArgumentParser(
            description="Generate batch job infrastructure (Phase 3)"
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
            "--job-name",
            default="process_batch",
            help="Name of the job/task"
        )

        parser.add_argument(
            "--queue-type",
            choices=self.SUPPORTED_QUEUE_TYPES,
            default="auto",
            help="Queue system type"
        )

        parser.add_argument(
            "--output-dir",
            default="./batch_jobs",
            help="Output directory for generated files"
        )

        parser.add_argument(
            "--format",
            choices=["json", "files"],
            default="files",
            help="Output format"
        )

        parser.add_argument(
            "--include-tests",
            action="store_true",
            help="Include test files"
        )

        parser.add_argument(
            "--include-docker",
            action="store_true",
            help="Include Docker configuration"
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

        parser.add_argument(
            "--enhanced",
            action="store_true",
            help="Use vault+checkpoint mode (OneShot-inspired stateful orchestration)"
        )

        parser.add_argument(
            "--vault-dir",
            default="./job_vault",
            help="Directory for job vault (with --enhanced)"
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

        # Validate framework/language combinations
        framework_language_map = {
            "django": ["python"],
            "fastapi": ["python"],
            "spring": ["java"],
            "go": ["go"],
        }

        if args.framework in framework_language_map:
            allowed_langs = framework_language_map[args.framework]
            if args.language not in allowed_langs:
                raise ValueError(
                    f"{args.framework} framework requires one of: {', '.join(allowed_langs)}"
                )

    def _generate(self, args):
        """Generate the code"""
        if args.verbose:
            print(f"[Phase3] Generating for {args.framework}/{args.language}")
            print(f"[Phase3] Job name: {args.job_name}")
            print(f"[Phase3] Queue type: {args.queue_type}")
            if args.enhanced:
                print(f"[Phase3] Mode: Enhanced (vault+checkpoint)")
                print(f"[Phase3] Vault dir: {args.vault_dir}")

        # Generate core infrastructure
        if args.enhanced:
            # Use enhanced orchestrator with vault/checkpoint/budget
            generated_files = orchestrate_phase3_enhanced(
                framework=args.framework,
                language=args.language,
                job_name=args.job_name,
                vault_dir=args.vault_dir,
                job_config={"budget": 1000.0, "daily_limit": 500.0},
                queue_type=args.queue_type if args.queue_type != "auto" else None
            )
        else:
            # Standard orchestration
            generated_files = orchestrate_phase3(
                framework=args.framework,
                language=args.language,
                job_name=args.job_name,
                queue_type=args.queue_type if args.queue_type != "auto" else None
            )

        # Add optional components
        if args.include_tests:
            if args.verbose:
                print("[Phase3] Including test files...")
            generated_files.update(self._generate_tests(args))

        if args.include_docker:
            if args.verbose:
                print("[Phase3] Including Docker configuration...")
            generated_files.update(self._generate_docker(args))

        # Output
        if args.format == "json":
            self._output_json(generated_files)
        else:
            self._output_files(generated_files, args)

        if args.verbose:
            print(f"[Phase3] Generated {len(generated_files)} files")

    def _generate_tests(self, args) -> dict:
        """Generate test files"""
        return {
            f"test_jobs.py" if args.language == "python" else "test_jobs.js": """
# Test file placeholder - add your tests here
"""
        }

    def _generate_docker(self, args) -> dict:
        """Generate Docker configuration"""
        if args.language == "python":
            return {
                "Dockerfile": f"""
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "worker.py"]
""",
                "docker-compose.yml": """
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  worker:
    build: .
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
    volumes:
      - .:/app
"""
            }
        else:
            return {
                "Dockerfile": """
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

CMD ["node", "worker.js"]
""",
                "docker-compose.yml": """
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  worker:
    build: .
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis
    volumes:
      - .:/app
"""
            }

    def _output_json(self, files: dict):
        """Output as JSON"""
        output = {
            "files": {name: content for name, content in files.items()},
            "count": len(files)
        }
        print(json.dumps(output, indent=2))

    def _output_files(self, files: dict, args):
        """Write files to disk"""
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in files.items():
            filepath = output_dir / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)

            if args.dry_run:
                print(f"Would write: {filepath} ({len(content)} bytes)")
            else:
                filepath.write_text(content)
                if args.verbose:
                    print(f"Created: {filepath}")

        print(f"\n✓ Generated {len(files)} files to {output_dir}")


def main():
    """Main entry point"""
    runner = Phase3Runner()
    sys.exit(runner.run())


if __name__ == "__main__":
    main()
