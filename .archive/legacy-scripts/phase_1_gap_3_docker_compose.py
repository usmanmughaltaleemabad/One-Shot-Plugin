#!/usr/bin/env python3
"""
Generate docker-compose.yml for local development environment.
"""

import yaml
from typing import Dict, Any


class DockerComposeGenerator:
    """Generate docker-compose.yml for development."""

    def __init__(self, framework: str, db_type: str = 'postgresql', with_cache: bool = True):
        self.framework = framework.lower()
        self.db_type = db_type.lower()
        self.with_cache = with_cache

    def generate_compose(self) -> Dict[str, Any]:
        """Generate docker-compose configuration."""
        compose = {
            'version': '3.8',
            'services': {},
            'volumes': {}
        }

        # App service
        if self.framework == 'django':
            compose['services']['app'] = {
                'build': '.',
                'command': 'python manage.py runserver 0.0.0.0:8000',
                'ports': ['8000:8000'],
                'environment': [
                    'DATABASE_URL=postgresql://postgres:password@db:5432/myapp',
                    'REDIS_URL=redis://redis:6379/0' if self.with_cache else None,
                    'DEBUG=True',
                ],
                'depends_on': ['db'],
                'volumes': ['.:/app'],
            }
            if self.with_cache:
                compose['services']['app']['depends_on'].append('redis')

        elif self.framework == 'fastapi':
            compose['services']['app'] = {
                'build': '.',
                'command': 'uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload',
                'ports': ['8000:8000'],
                'environment': [
                    'DATABASE_URL=postgresql://postgres:password@db:5432/myapp',
                    'REDIS_URL=redis://redis:6379/0' if self.with_cache else None,
                ],
                'depends_on': ['db'],
                'volumes': ['.:/app'],
            }
            if self.with_cache:
                compose['services']['app']['depends_on'].append('redis')

        elif self.framework == 'nestjs':
            compose['services']['app'] = {
                'build': '.',
                'command': 'npm run start:dev',
                'ports': ['3000:3000'],
                'environment': [
                    'DATABASE_URL=postgresql://postgres:password@db:5432/myapp',
                    'NODE_ENV=development',
                ],
                'depends_on': ['db'],
                'volumes': ['.:/app', '/app/node_modules'],
            }

        elif self.framework == 'express':
            compose['services']['app'] = {
                'build': '.',
                'command': 'npm run dev',
                'ports': ['3000:3000'],
                'environment': [
                    'DATABASE_URL=mysql://root:password@db:3306/myapp' if self.db_type == 'mysql' else 'DATABASE_URL=postgresql://postgres:password@db:5432/myapp',
                    'NODE_ENV=development',
                ],
                'depends_on': ['db'],
                'volumes': ['.:/app', '/app/node_modules'],
            }

        elif self.framework == 'spring':
            compose['services']['app'] = {
                'build': '.',
                'ports': ['8080:8080'],
                'environment': [
                    'SPRING_DATASOURCE_URL=jdbc:postgresql://db:5432/myapp',
                    'SPRING_DATASOURCE_USERNAME=postgres',
                    'SPRING_DATASOURCE_PASSWORD=password',
                    'SPRING_PROFILES_ACTIVE=dev',
                ],
                'depends_on': ['db'],
            }

        # Database service
        if self.db_type == 'postgresql':
            compose['services']['db'] = {
                'image': 'postgres:14',
                'environment': {
                    'POSTGRES_USER': 'postgres',
                    'POSTGRES_PASSWORD': 'password',
                    'POSTGRES_DB': 'myapp',
                },
                'ports': ['5432:5432'],
                'volumes': ['postgres_data:/var/lib/postgresql/data'],
            }
            compose['volumes']['postgres_data'] = {}

        elif self.db_type == 'mysql':
            compose['services']['db'] = {
                'image': 'mysql:8',
                'environment': {
                    'MYSQL_ROOT_PASSWORD': 'password',
                    'MYSQL_DATABASE': 'myapp',
                },
                'ports': ['3306:3306'],
                'volumes': ['mysql_data:/var/lib/mysql'],
            }
            compose['volumes']['mysql_data'] = {}

        elif self.db_type == 'mongodb':
            compose['services']['db'] = {
                'image': 'mongo:5',
                'ports': ['27017:27017'],
                'environment': {
                    'MONGO_INITDB_ROOT_USERNAME': 'admin',
                    'MONGO_INITDB_ROOT_PASSWORD': 'password',
                },
                'volumes': ['mongo_data:/data/db'],
            }
            compose['volumes']['mongo_data'] = {}

        # Redis cache
        if self.with_cache:
            compose['services']['redis'] = {
                'image': 'redis:7',
                'ports': ['6379:6379'],
                'volumes': ['redis_data:/data'],
            }
            compose['volumes']['redis_data'] = {}

        # Optional: pgAdmin for PostgreSQL
        if self.db_type == 'postgresql':
            compose['services']['pgadmin'] = {
                'image': 'dpage/pgadmin4',
                'ports': ['5050:80'],
                'environment': {
                    'PGADMIN_DEFAULT_EMAIL': 'admin@example.com',
                    'PGADMIN_DEFAULT_PASSWORD': 'admin',
                },
                'depends_on': ['db'],
            }

        return compose

    def to_yaml(self) -> str:
        """Convert to YAML string."""
        compose = self.generate_compose()

        # Remove None values from environment lists
        for service in compose.get('services', {}).values():
            if 'environment' in service and isinstance(service['environment'], list):
                service['environment'] = [e for e in service['environment'] if e is not None]

        return yaml.dump(compose, default_flow_style=False, sort_keys=False)


def generate_docker_compose(
    framework: str,
    db_type: str = 'postgresql',
    with_cache: bool = True
) -> str:
    """Generate docker-compose.yml content."""
    generator = DockerComposeGenerator(framework, db_type, with_cache)
    return generator.to_yaml()
