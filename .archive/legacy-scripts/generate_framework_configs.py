#!/usr/bin/env python3
"""
Gap 3: Framework Configuration Generation

Auto-generates framework configuration files based on detected patterns:
- Django: settings.py, manage.py, wsgi.py, asgi.py
- FastAPI: main.py, config.py, logging config
- Spring: application.properties, application.yml, pom.xml
- Go: main.go, config.go, .env
- Node/Express: package.json, .env, server.js

Input: Framework, feature requirements, detected context
Output: Complete configuration files ready to use
"""

import json
import os
from typing import Dict, Tuple


class ConfigGenerator:
    """Generates framework configuration files."""

    def __init__(self, framework: str, project_root: str):
        self.framework = framework.lower()
        self.project_root = project_root

    def generate_configs(self, feature_name: str, dependencies: Dict) -> Dict[str, str]:
        """
        Generate all config files for framework.

        Returns: {filepath: content, ...}
        """

        if self.framework == 'django':
            return self._generate_django_configs(feature_name, dependencies)
        elif self.framework == 'fastapi':
            return self._generate_fastapi_configs(feature_name, dependencies)
        elif self.framework == 'spring':
            return self._generate_spring_configs(feature_name, dependencies)
        elif self.framework == 'go':
            return self._generate_go_configs(feature_name, dependencies)
        elif self.framework in ['express', 'nodejs']:
            return self._generate_nodejs_configs(feature_name, dependencies)
        else:
            return {}

    def _generate_django_configs(self, feature_name: str, deps: Dict) -> Dict[str, str]:
        """Generate Django configuration files."""

        configs = {}

        # settings.py additions
        settings_content = self._get_django_settings(deps)
        configs['config/settings.py'] = settings_content

        # manage.py (if doesn't exist)
        configs['manage.py'] = self._get_django_manage()

        # wsgi.py
        configs['config/wsgi.py'] = self._get_django_wsgi()

        # asgi.py (if async)
        if deps.get('async'):
            configs['config/asgi.py'] = self._get_django_asgi()

        # .env template
        configs['.env.example'] = self._get_env_template(deps)

        # docker-compose.yml (if Docker detected)
        if deps.get('docker'):
            configs['docker-compose.yml'] = self._get_docker_compose('django')

        return configs

    def _generate_fastapi_configs(self, feature_name: str, deps: Dict) -> Dict[str, str]:
        """Generate FastAPI configuration files."""

        configs = {}

        # main.py (app startup)
        configs['main.py'] = self._get_fastapi_main(deps)

        # config.py (settings)
        configs['config.py'] = self._get_fastapi_config(deps)

        # logging config
        configs['logging_config.json'] = self._get_fastapi_logging()

        # .env template
        configs['.env.example'] = self._get_env_template(deps)

        # pyproject.toml (if using poetry)
        if deps.get('package_manager') == 'poetry':
            configs['pyproject.toml'] = self._get_pyproject_toml(deps)

        # requirements.txt
        if deps.get('package_manager') != 'poetry':
            configs['requirements.txt'] = self._get_requirements_txt(deps)

        # docker-compose.yml
        if deps.get('docker'):
            configs['docker-compose.yml'] = self._get_docker_compose('fastapi')

        return configs

    def _generate_spring_configs(self, feature_name: str, deps: Dict) -> Dict[str, str]:
        """Generate Spring Boot configuration files."""

        configs = {}

        # application.properties
        configs['src/main/resources/application.properties'] = self._get_spring_properties(deps)

        # application-dev.properties
        configs['src/main/resources/application-dev.properties'] = self._get_spring_properties_dev(deps)

        # pom.xml (Maven) — default for Spring Boot
        if deps.get('build_tool') == 'gradle':
            configs['build.gradle'] = self._get_gradle_build(deps)
        else:
            configs['pom.xml'] = self._get_pom_xml(deps)

        # .env
        configs['.env.example'] = self._get_env_template(deps)

        # Flyway migration placeholder
        configs['src/main/resources/db/migration/V1__Initial_Schema.sql'] = "-- Initial schema"

        # docker-compose.yml
        if deps.get('docker'):
            configs['docker-compose.yml'] = self._get_docker_compose('spring')

        return configs

    def _generate_go_configs(self, feature_name: str, deps: Dict) -> Dict[str, str]:
        """Generate Go configuration files."""

        configs = {}

        # config.go (configuration struct)
        configs['internal/config/config.go'] = self._get_go_config()

        # main.go (app entry)
        configs['main.go'] = self._get_go_main(deps)

        # .env template
        configs['.env.example'] = self._get_env_template(deps)

        # go.mod
        configs['go.mod'] = self._get_go_mod(deps)

        # Makefile
        configs['Makefile'] = self._get_makefile('go')

        # docker-compose.yml
        if deps.get('docker'):
            configs['docker-compose.yml'] = self._get_docker_compose('go')

        return configs

    def _generate_nodejs_configs(self, feature_name: str, deps: Dict) -> Dict[str, str]:
        """Generate Node.js/Express configuration files."""

        configs = {}

        # package.json
        configs['package.json'] = self._get_package_json(deps)

        # .env template
        configs['.env.example'] = self._get_env_template(deps)

        # server.js or index.js
        configs['src/server.js'] = self._get_nodejs_server(deps)

        # config.js
        configs['src/config.js'] = self._get_nodejs_config(deps)

        # docker-compose.yml
        if deps.get('docker'):
            configs['docker-compose.yml'] = self._get_docker_compose('nodejs')

        return configs

    # Django helpers
    def _get_django_settings(self, deps: Dict) -> str:
        """Django settings.py content."""
        db_engine = 'postgresql' if 'postgres' in str(deps).lower() else 'sqlite3'
        database_config = f"'ENGINE': 'django.db.backends.{db_engine}'"

        return f'''import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'config.urls'
TEMPLATES = [{{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
}}]

DATABASES = {{
    'default': {{
        {database_config},
        'NAME': os.environ.get('DB_NAME', BASE_DIR / 'db.sqlite3'),
    }}
}}

AUTH_PASSWORD_VALIDATORS = [
    {{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}},
    {{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'}},
    {{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}},
    {{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {{
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}}
'''

    def _get_django_manage(self) -> str:
        return '''#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
'''

    def _get_django_wsgi(self) -> str:
        return '''import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()
'''

    def _get_django_asgi(self) -> str:
        return '''import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_asgi_application()
'''

    # FastAPI helpers
    def _get_fastapi_main(self, deps: Dict) -> str:
        return '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

app = FastAPI(
    title="API",
    version="1.0.0",
    description="Generated FastAPI application"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

    def _get_fastapi_config(self, deps: Dict) -> str:
        return '''import os
from typing import List

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")

settings = Settings()
'''

    def _get_fastapi_logging(self) -> str:
        return json.dumps({
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                }
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": "INFO"
                }
            }
        }, indent=2)

    # Spring helpers
    def _get_spring_properties(self, deps: Dict) -> str:
        return '''spring.application.name=api
spring.profiles.active=dev

server.port=8080
server.servlet.context-path=/api

spring.datasource.url=jdbc:postgresql://localhost:5432/app
spring.datasource.username=postgres
spring.datasource.password=postgres
spring.datasource.driver-class-name=org.postgresql.Driver

spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=false
spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.PostgreSQLDialect

logging.level.root=INFO
logging.level.com.app=DEBUG
'''

    def _get_spring_properties_dev(self, deps: Dict) -> str:
        return '''spring.jpa.show-sql=true
spring.jpa.properties.hibernate.format_sql=true
logging.level.org.hibernate.SQL=DEBUG
logging.level.org.hibernate.type.descriptor.sql.BasicBinder=TRACE
'''

    def _get_pom_xml(self, deps: Dict) -> str:
        return '''<?xml version="1.0" encoding="UTF-8"?>
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>api</artifactId>
    <version>1.0.0</version>
    <name>API</name>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.1.0</version>
    </parent>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
        </dependency>
    </dependencies>
</project>
'''

    # Go helpers
    def _get_go_config(self) -> str:
        return '''package config

import "os"

type Config struct {
    Port     string
    DBHost   string
    DBPort   string
    DBUser   string
    DBPass   string
    DBName   string
    Debug    bool
}

func Load() *Config {
    return &Config{
        Port:   getEnv("PORT", "8080"),
        DBHost: getEnv("DB_HOST", "localhost"),
        DBPort: getEnv("DB_PORT", "5432"),
        DBUser: getEnv("DB_USER", "postgres"),
        DBPass: getEnv("DB_PASS", "postgres"),
        DBName: getEnv("DB_NAME", "app"),
    }
}

func getEnv(key, defaultVal string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultVal
}
'''

    def _get_go_main(self, deps: Dict) -> str:
        return '''package main

import (
    "fmt"
    "log"
    "./internal/config"
)

func main() {
    cfg := config.Load()

    fmt.Printf("Starting server on port %s\\n", cfg.Port)

    // TODO: Initialize database, routes, etc.
    log.Fatal("Server stopped")
}
'''

    def _get_go_mod(self, deps: Dict) -> str:
        return '''module github.com/example/api

go 1.21

require (
    github.com/lib/pq v1.10.9
)
'''

    # Node.js helpers
    def _get_package_json(self, deps: Dict) -> str:
        return json.dumps({
            "name": "api",
            "version": "1.0.0",
            "description": "Generated Node.js API",
            "main": "src/server.js",
            "scripts": {
                "start": "node src/server.js",
                "dev": "nodemon src/server.js",
                "test": "jest"
            },
            "dependencies": {
                "express": "^4.18.0",
                "dotenv": "^16.0.0",
                "cors": "^2.8.5",
                "morgan": "^1.10.0"
            },
            "devDependencies": {
                "nodemon": "^2.0.20",
                "jest": "^29.0.0"
            }
        }, indent=2)

    def _get_nodejs_server(self, deps: Dict) -> str:
        return '''const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 8000;

app.use(cors());
app.use(morgan('combined'));
app.use(express.json());

app.get('/health', (req, res) => {
    res.json({ status: 'ok' });
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
'''

    def _get_nodejs_config(self, deps: Dict) -> str:
        return '''module.exports = {
    port: process.env.PORT || 8000,
    nodeEnv: process.env.NODE_ENV || 'development',
    dbUrl: process.env.DATABASE_URL || 'postgresql://localhost/app',
    corsOrigins: (process.env.CORS_ORIGINS || 'http://localhost:3000').split(','),
};
'''

    # Generic helpers
    def _get_env_template(self, deps: Dict) -> str:
        return '''# Environment variables
DEBUG=False
SECRET_KEY=change-me-in-production

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASS=postgres
DB_NAME=app

# Server
PORT=8000
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
'''

    def _get_docker_compose(self, framework: str) -> str:
        """Generate docker-compose.yml."""
        if framework == 'django':
            return '''version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    ports:
      - "8000:8000"
    depends_on:
      - db
'''
        elif framework == 'fastapi':
            return '''version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"

  api:
    build: .
    command: uvicorn main:app --host 0.0.0.0
    ports:
      - "8000:8000"
    depends_on:
      - db
'''
        else:
            return '''version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
'''

    def _get_makefile(self, framework: str) -> str:
        """Generate Makefile for common tasks."""
        if framework == 'go':
            return '''.PHONY: build run test clean

build:
\tgo build -o bin/api main.go

run:
\tgo run main.go

test:
\tgo test ./...

clean:
\trm -f bin/api
'''
        return '''.PHONY: install run test

install:
\tgo mod download

run:
\tgo run main.go

test:
\tgo test ./...
'''

    def _get_pyproject_toml(self, deps: Dict) -> str:
        return '''[tool.poetry]
name = "api"
version = "0.1.0"
description = "Generated FastAPI application"

[tool.poetry.dependencies]
python = "^3.10"
fastapi = "^0.104.0"
sqlalchemy = "^2.0.0"
pydantic = "^2.0.0"
uvicorn = "^0.24.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
'''

    def _get_requirements_txt(self, deps: Dict) -> str:
        return '''fastapi==0.104.1
sqlalchemy==2.0.23
pydantic==2.5.0
uvicorn==0.24.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
'''

    def _get_gradle_build(self, deps: Dict) -> str:
        return '''plugins {
    id 'java'
    id 'org.springframework.boot' version '3.1.5'
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    runtimeOnly 'org.postgresql:postgresql'
}
'''


def main():
    """Test config generation."""
    gen = ConfigGenerator('django', '/path/to/project')
    configs = gen.generate_configs('User Auth', {
        'async': False,
        'docker': True,
    })

    for filepath, content in configs.items():
        print(f"\n{'='*60}")
        print(f"File: {filepath}")
        print(f"{'='*60}")
        print(content[:500] + "..." if len(content) > 500 else content)


if __name__ == '__main__':
    main()
