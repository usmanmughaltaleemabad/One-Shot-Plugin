"""
Docker Generator - Container generation for all frameworks

Generates:
- Dockerfile (multi-stage)
- docker-compose for local development
- Container optimization
- Base image selection
"""

from typing import Dict, Any


class DockerGenerator:
    """Generate Docker configurations"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_django_dockerfile(self) -> str:
        """Generate Django Dockerfile"""
        return """
# Multi-stage build for Django
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and build wheels
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Set environment variables
ENV PATH=/root/.local/bin:$PATH \\
    PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    DJANGO_SETTINGS_MODULE=config.settings.production

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Collect static files
RUN python manage.py collectstatic --noinput --clear

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "sync", "--access-logfile", "-", "--error-logfile", "-", "config.wsgi"]
"""

    def generate_fastapi_dockerfile(self) -> str:
        """Generate FastAPI Dockerfile"""
        return """
FROM python:3.11-slim as builder

WORKDIR /app
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH \\
    PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
"""

    def generate_nestjs_dockerfile(self) -> str:
        """Generate NestJS Dockerfile"""
        return """
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

ENV NODE_ENV=production

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

COPY package*.json ./
RUN npm ci --only=production

COPY --from=builder /app/dist ./dist

RUN addgroup -g 1000 appuser && adduser -D -u 1000 -G appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD node -e "require('http').get('http://localhost:3000/health', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/main"]
"""

    def generate_docker_compose(self) -> str:
        """Generate docker-compose.yml for local development"""
        return """
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: app-dev
    ports:
      - "8000:8000"
    environment:
      - DEBUG=true
      - DATABASE_URL=postgresql://user:password@db:5432/appdb
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    command: >
      sh -c "python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8000"

  db:
    image: postgres:15-alpine
    container_name: app-db
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=appdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d appdb"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: app-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: app-worker
    environment:
      - DEBUG=true
      - DATABASE_URL=postgresql://user:password@db:5432/appdb
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    command: python -m celery -A config.celery worker -l info

volumes:
  postgres_data:
  redis_data:
"""


def generate_docker_configs(framework: str, language: str) -> Dict[str, str]:
    """
    Generate Docker configurations.

    Args:
        framework: django, fastapi, spring, nestjs
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = DockerGenerator(framework, language)
    output = {}

    if language == "python":
        if framework == "django":
            output["Dockerfile"] = generator.generate_django_dockerfile()
        elif framework == "fastapi":
            output["Dockerfile"] = generator.generate_fastapi_dockerfile()

        output["docker-compose.yml"] = generator.generate_docker_compose()

    elif language == "javascript":
        output["Dockerfile"] = generator.generate_nestjs_dockerfile()
        output["docker-compose.yml"] = generator.generate_docker_compose()

    return output
