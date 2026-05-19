#!/usr/bin/env python3
"""
Generate .env.example template with all required environment variables.
"""

from typing import Dict, List


class EnvironmentGenerator:
    """Generate environment variable templates."""

    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate_database_vars(self, db_type: str = 'postgresql') -> str:
        """Generate database environment variables."""
        vars_str = '# Database\n'

        if db_type == 'postgresql':
            vars_str += '''DATABASE_URL=postgresql://user:password@localhost:5432/myapp
DATABASE_ECHO=false
'''
        elif db_type == 'mysql':
            vars_str += '''DATABASE_URL=mysql://user:password@localhost:3306/myapp
DATABASE_POOL_SIZE=10
'''
        elif db_type == 'mongodb':
            vars_str += '''MONGODB_URI=mongodb://localhost:27017/myapp
MONGODB_USER=admin
MONGODB_PASS=password
'''
        else:
            vars_str += 'DATABASE_URL=sqlite:///./test.db\n'

        return vars_str

    def generate_auth_vars(self) -> str:
        """Generate authentication environment variables."""
        return '''
# Authentication
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24
OAUTH_GOOGLE_CLIENT_ID=
OAUTH_GOOGLE_CLIENT_SECRET=
OAUTH_GITHUB_CLIENT_ID=
OAUTH_GITHUB_CLIENT_SECRET=
'''

    def generate_queue_vars(self) -> str:
        """Generate queue/job variables."""
        return '''
# Queue & Jobs
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
QUEUE_TIMEOUT=300
MAX_RETRIES=3
'''

    def generate_redis_vars(self) -> str:
        """Generate Redis variables."""
        return '''
# Redis Cache
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600
'''

    def generate_logging_vars(self) -> str:
        """Generate logging variables."""
        return '''
# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
SENTRY_DSN=
'''

    def generate_external_api_vars(self) -> str:
        """Generate external API variables."""
        return '''
# External APIs
STRIPE_API_KEY=sk_test_
STRIPE_WEBHOOK_SECRET=whsec_
OPENAI_API_KEY=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
'''

    def generate_django_vars(self) -> str:
        """Generate Django-specific variables."""
        return f'''# Django
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
{self.generate_database_vars('postgresql')}{self.generate_auth_vars()}{self.generate_redis_vars()}{self.generate_logging_vars()}'''

    def generate_fastapi_vars(self) -> str:
        """Generate FastAPI-specific variables."""
        return f'''# FastAPI
DEBUG=False
{self.generate_database_vars('postgresql')}{self.generate_auth_vars()}{self.generate_redis_vars()}{self.generate_logging_vars()}'''

    def generate_nestjs_vars(self) -> str:
        """Generate NestJS-specific variables."""
        return f'''# NestJS
NODE_ENV=development
PORT=3000
{self.generate_database_vars('postgresql')}{self.generate_auth_vars()}{self.generate_queue_vars()}{self.generate_logging_vars()}'''

    def generate_express_vars(self) -> str:
        """Generate Express-specific variables."""
        return f'''# Express
NODE_ENV=development
PORT=3000
{self.generate_database_vars('mysql')}{self.generate_auth_vars()}{self.generate_logging_vars()}'''

    def generate_spring_vars(self) -> str:
        """Generate Spring-specific variables."""
        return f'''# Spring Boot
SPRING_PROFILES_ACTIVE=dev
SERVER_PORT=8080
{self.generate_database_vars('postgresql')}{self.generate_auth_vars()}{self.generate_logging_vars()}'''

    def generate(self) -> str:
        """Generate complete .env.example for framework."""
        if self.framework == 'django':
            return self.generate_django_vars()
        elif self.framework == 'fastapi':
            return self.generate_fastapi_vars()
        elif self.framework == 'nestjs':
            return self.generate_nestjs_vars()
        elif self.framework == 'express':
            return self.generate_express_vars()
        elif self.framework == 'spring':
            return self.generate_spring_vars()
        else:
            return '# Environment variables\n'


def generate_env_template(framework: str) -> str:
    """Generate .env.example template for framework."""
    generator = EnvironmentGenerator(framework)
    return generator.generate()
