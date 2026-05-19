#!/usr/bin/env python3
"""
Gap 7: Configuration File Generation

Auto-generates framework-specific config files and .env templates:
- Django: settings_{feature}.py with os.getenv() calls
- FastAPI: config_{feature}.py using Pydantic BaseSettings
- Spring Boot: application-{feature}.yml with ${ENV_VAR} placeholders
- Docker: .env.docker + Dockerfile ARG/ENV entries
- All frameworks: .env.example with all required env vars (never real secrets)

Input: Feature name, required config vars, framework
Output: Config files + .env.example
"""

import os
import re
import sys
from typing import List, Dict, Tuple
from pathlib import Path

# Shared library imports
sys.path.insert(0, str(Path(__file__).parent))
from lib.base_script import __version__, setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class ConfigGenerator:
    """Generates framework-specific config files."""

    def __init__(self, framework: str, feature_name: str):
        self.framework = framework.lower()
        self.feature_name = feature_name
        self.feature_slug = feature_name.lower().replace(' ', '_')

    def generate(self, required_vars: List[str]) -> Dict[str, str]:
        """
        Generate all config files.

        Args:
            required_vars: List of required environment variable names

        Returns:
            Dict mapping filepath -> content
        """
        files = {}

        # Always generate .env.example
        files['.env.example'] = self._generate_env_example(required_vars)

        # Framework-specific config files
        if self.framework == 'django':
            files[f'config/settings_{self.feature_slug}.py'] = self._generate_django_settings(required_vars)
        elif self.framework == 'fastapi':
            files[f'config_{self.feature_slug}.py'] = self._generate_fastapi_config(required_vars)
        elif self.framework == 'spring':
            files[f'src/main/resources/application-{self.feature_slug}.yml'] = self._generate_spring_config(required_vars)
        elif self.framework == 'go':
            files[f'config/{self.feature_slug}.env'] = self._generate_env_example(required_vars)

        return files

    def _generate_env_example(self, vars: List[str]) -> str:
        """Generate .env.example with all required vars (no real secrets)."""
        lines = [
            '# Environment Configuration — Copy to .env and fill with real values',
            '# Never commit real secrets to git; use .env.local (gitignored)',
            '',
            f'# {self.feature_name} Configuration',
        ]

        for var_name in vars:
            # Create descriptive example values based on var name
            if 'api_key' in var_name.lower() or 'secret' in var_name.lower():
                example = f'your_{var_name.lower()}_here'
            elif 'url' in var_name.lower() or 'host' in var_name.lower():
                example = f'localhost:5432'
            elif 'port' in var_name.lower():
                example = '5432'
            elif 'email' in var_name.lower():
                example = 'example@example.com'
            else:
                example = f'value_{var_name.lower()}'

            lines.append(f'{var_name}={example}')

        lines.extend([
            '',
            '# Secrets Management',
            '# For production, use one of:',
            '#   - Docker Secrets: /run/secrets/{var_name}',
            '#   - Kubernetes Secrets: kubectl create secret generic',
            '#   - HashiCorp Vault: vault write secret/data/app',
            '#   - AWS Secrets Manager',
            '',
        ])

        return '\n'.join(lines)

    def _generate_django_settings(self, vars: List[str]) -> str:
        """Generate Django settings_{feature}.py with os.getenv() calls."""
        import_vars = ', '.join(f"'{var}'" for var in vars)

        content = f'''"""
Django settings for {self.feature_name}

Import this in main settings.py or use environment variables directly.
"""

import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Configuration variables - use environment variables
REQUIRED_VARS = [{import_vars}]

# Verify all required vars are set
missing_vars = [v for v in REQUIRED_VARS if not os.getenv(v)]
if missing_vars:
    raise RuntimeError(f"Missing required environment variables: {{missing_vars}}")

# Feature-specific settings
'''

        for var in vars:
            snake_case = var.lower()
            content += f"{snake_case.upper()} = os.getenv('{var}')\n"

        content += f'''
# Example usage in main settings.py:
# from .settings_{self.feature_slug} import *

# Add to INSTALLED_APPS (if new Django app):
# INSTALLED_APPS = [
#     ...,
#     '{self.feature_slug}',
# ]

# Add to DATABASES (if new database):
# DATABASES['{self.feature_slug}'] = {{
#     'ENGINE': 'django.db.backends.postgresql',
#     'NAME': os.getenv('{vars[0]}'),
#     'USER': os.getenv('{vars[0]}_USER') if len(REQUIRED_VARS) > 1 else 'postgres',
#     'PASSWORD': os.getenv('{vars[0]}_PASSWORD') if len(REQUIRED_VARS) > 1 else 'postgres',
#     'HOST': os.getenv('DATABASE_HOST', 'localhost'),
#     'PORT': os.getenv('DATABASE_PORT', '5432'),
# }}
'''
        return content

    def _generate_fastapi_config(self, vars: List[str]) -> str:
        """Generate FastAPI config_{feature}.py using Pydantic BaseSettings."""
        content = f'''"""
FastAPI config for {self.feature_name}

Uses Pydantic BaseSettings for type-safe environment variable handling.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class {self._to_pascal_case(self.feature_slug)}Settings(BaseSettings):
    """
    Settings for {self.feature_name}.

    Load from environment variables with optional .env file.
    All variables are required unless marked Optional.
    """
'''

        for var in vars:
            snake_case = var.lower()
            content += f"    {snake_case}: str\n"

        content += f'''
    class Config:
        env_file = '.env'
        env_prefix = '{self.feature_slug.upper()}_'
        # Set env_nested_delimiter to support nested config (e.g., FEATURE_DB__HOST)
        # env_nested_delimiter = '__'


# Usage in your FastAPI app:
# from config_{self.feature_slug} import {self._to_pascal_case(self.feature_slug)}Settings
#
# settings = {self._to_pascal_case(self.feature_slug)}Settings()
#
# @app.get("/health")
# async def health_check():
#     return {{"status": "ok", "feature": "{self.feature_slug}"}}
'''
        return content

    def _generate_spring_config(self, vars: List[str]) -> str:
        """Generate Spring application-{feature}.yml with ${ENV_VAR} placeholders."""
        content = f'''# Spring Boot Application Configuration for {self.feature_name}
#
# Usage: Include in application.yml or set spring.config.import=optional:classpath:application-{self.feature_slug}.yml
#
# All values use environment variable placeholders: ${{VARIABLE_NAME}}
# Set these in .env, docker-compose.yml, or deployment environment

{self.feature_slug}:
  enabled: true
  config:
'''

        for var in vars:
            snake_case = var.lower()
            content += f"    {snake_case}: \"${{{var}}}\"\n"

        content += f'''
# Database configuration (if needed)
spring:
  datasource:
    url: "jdbc:postgresql://${{DB_HOST:localhost}}:${{DB_PORT:5432}}/${{DB_NAME:{self.feature_slug}}}"
    username: "${{DB_USER:postgres}}"
    password: "${{DB_PASSWORD:postgres}}"
    driver-class-name: org.postgresql.Driver
  jpa:
    hibernate:
      ddl-auto: validate  # Change to 'update' only in development
    show-sql: false
    properties:
      hibernate.format_sql: true

# Logging
logging:
  level:
    root: INFO
    com.example.{self.feature_slug}: DEBUG

# Server configuration
server:
  port: 8080
  error:
    include-message: always
    include-stacktrace: on-param

# Actuator (monitoring)
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
  endpoint:
    health:
      show-details: when-authorized
'''
        return content

    def _to_pascal_case(self, snake_str: str) -> str:
        """Convert snake_case to PascalCase."""
        return ''.join(word.capitalize() for word in snake_str.split('_'))


def main():
    """Test config generation."""
    with timed_run("config_generator") as timer:
        logger.debug("Testing config generation")

        test_vars = ['API_KEY', 'DATABASE_URL', 'WEBHOOK_SECRET']
        gen = ConfigGenerator('fastapi', 'Payment Processing')
        files = gen.generate(test_vars)

        logger.debug(f"Generated {len(files)} config files")
        for filepath, content in files.items():
            print(f"\n{'='*60}")
            print(f"File: {filepath}")
            print(f"{'='*60}")
            print(content[:200] + "..." if len(content) > 200 else content)

        check_budget("config_generator", timer.elapsed_ms, logger)

    logger.debug(f"config_generator completed in {timer.elapsed_ms:.0f}ms")


if __name__ == '__main__':
    main()
