#!/usr/bin/env python3
"""
Generate framework-specific configuration for generated features.

Merges new config into existing framework config files.
"""

import re
from typing import Dict, Tuple


class FrameworkConfigGenerator:
    """Generate and merge framework configurations."""

    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate_django_settings(self, features: Dict[str, bool]) -> str:
        """Generate Django settings.py additions."""
        config = ''

        if features.get('auth'):
            config += '''
# Authentication
AUTH_USER_MODEL = 'auth.User'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]
'''

        if features.get('webhooks'):
            config += '''
# Webhooks
WEBHOOK_TIMEOUT = 30
WEBHOOK_RETRIES = 3
WEBHOOK_SECRET = env('WEBHOOK_SECRET', '')
'''

        if features.get('celery'):
            config += '''
# Celery
CELERY_BROKER_URL = env('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
'''

        return config

    def generate_fastapi_main(self, features: Dict[str, bool]) -> str:
        """Generate FastAPI main.py additions."""
        config = ''

        if features.get('auth'):
            config += '''
from fastapi.security import HTTPBearer
security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    token = credentials.credentials
    # Validate token
    return token
'''

        if features.get('cors'):
            config += '''
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
'''

        return config

    def generate_nestjs_module(self, features: Dict[str, bool]) -> str:
        """Generate NestJS module imports."""
        config = 'import { Module } from \'@nestjs/common\';\n'

        if features.get('auth'):
            config += 'import { AuthModule } from \'./auth/auth.module\';\n'

        if features.get('typeorm'):
            config += 'import { TypeOrmModule } from \'@nestjs/typeorm\';\n'

        if features.get('redis'):
            config += 'import { RedisModule } from \'@nestjs/redis\';\n'

        return config

    def generate_express_index(self, features: Dict[str, bool]) -> str:
        """Generate Express index.js additions."""
        config = ''

        if features.get('auth'):
            config += '''
const passport = require('passport');
app.use(passport.initialize());
app.use(passport.session());
'''

        if features.get('cors'):
            config += '''
const cors = require('cors');
app.use(cors({
  origin: process.env.CORS_ORIGIN || '*',
  credentials: true
}));
'''

        if features.get('logging'):
            config += '''
const morgan = require('morgan');
app.use(morgan('combined'));
'''

        return config

    def generate_spring_properties(self, features: Dict[str, bool]) -> str:
        """Generate Spring application.properties additions."""
        config = ''

        if features.get('auth'):
            config += '''
spring.security.user.name=admin
spring.security.user.password=admin
jwt.secret=${JWT_SECRET}
jwt.expiration=86400
'''

        if features.get('database'):
            config += '''
spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=false
spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.PostgreSQLDialect
'''

        if features.get('redis'):
            config += '''
spring.redis.host=localhost
spring.redis.port=6379
'''

        return config

    def generate(self, features: Dict[str, bool]) -> Dict[str, str]:
        """Generate config for framework."""
        config = {}

        if self.framework == 'django':
            config['settings.py'] = self.generate_django_settings(features)
        elif self.framework == 'fastapi':
            config['main.py'] = self.generate_fastapi_main(features)
        elif self.framework == 'nestjs':
            config['app.module.ts'] = self.generate_nestjs_module(features)
        elif self.framework == 'express':
            config['index.js'] = self.generate_express_index(features)
        elif self.framework == 'spring':
            config['application.properties'] = self.generate_spring_properties(features)

        return config


def generate_framework_config(
    framework: str,
    features: Dict[str, bool]
) -> Dict[str, str]:
    """Generate framework-specific configuration."""
    generator = FrameworkConfigGenerator(framework)
    return generator.generate(features)
