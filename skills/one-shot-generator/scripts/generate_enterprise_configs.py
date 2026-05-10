#!/usr/bin/env python3
"""
Gap 6: Enterprise Configuration Generation

Auto-generates enterprise deployment configurations:
- Dockerfile & docker-compose.yml
- Kubernetes manifests (Deployment, Service, Ingress, ConfigMap, Secrets)
- Terraform infrastructure-as-code
- GitHub Actions CI/CD pipelines
- GitLab CI/CD pipelines
- AWS CloudFormation

Input: Framework, deployment target, services (db, cache, queue)
Output: Complete deployment-ready infrastructure code
"""

import json
from typing import Dict, List


class EnterpriseConfigGenerator:
    """Generates enterprise deployment configurations."""

    def __init__(self, framework: str, deployment_target: str = 'kubernetes'):
        self.framework = framework.lower()
        self.deployment_target = deployment_target.lower()

    def generate_enterprise_configs(self, app_name: str, services: List[str], env_vars: Dict) -> Dict[str, str]:
        """
        Generate enterprise configurations.

        Returns: {filepath: content, ...}
        """
        configs = {}

        # Docker configs (always needed)
        configs.update(self._generate_docker_configs(app_name, services))

        # Deployment target-specific configs
        if self.deployment_target == 'kubernetes':
            configs.update(self._generate_kubernetes_configs(app_name, services))
        elif self.deployment_target == 'terraform':
            configs.update(self._generate_terraform_configs(app_name, services))
        elif self.deployment_target == 'cloudformation':
            configs.update(self._generate_cloudformation_configs(app_name, services))

        # CI/CD pipelines
        configs.update(self._generate_cicd_configs(app_name))

        return configs

    def _generate_docker_configs(self, app_name: str, services: List[str]) -> Dict[str, str]:
        """Generate Docker configurations."""
        configs = {}

        configs['Dockerfile'] = self._get_dockerfile(self.framework)
        configs['.dockerignore'] = self._get_dockerignore()
        configs['docker-compose.yml'] = self._get_docker_compose(app_name, services)

        return configs

    def _generate_kubernetes_configs(self, app_name: str, services: List[str]) -> Dict[str, str]:
        """Generate Kubernetes manifests."""
        configs = {}

        configs['k8s/namespace.yaml'] = self._get_k8s_namespace(app_name)
        configs['k8s/configmap.yaml'] = self._get_k8s_configmap(app_name)
        configs['k8s/deployment.yaml'] = self._get_k8s_deployment(app_name)
        configs['k8s/service.yaml'] = self._get_k8s_service(app_name)
        configs['k8s/ingress.yaml'] = self._get_k8s_ingress(app_name)
        configs['k8s/hpa.yaml'] = self._get_k8s_hpa(app_name)

        return configs

    def _generate_terraform_configs(self, app_name: str, services: List[str]) -> Dict[str, str]:
        """Generate Terraform infrastructure."""
        configs = {}

        configs['terraform/main.tf'] = self._get_terraform_main(app_name)
        configs['terraform/variables.tf'] = self._get_terraform_variables()
        configs['terraform/outputs.tf'] = self._get_terraform_outputs()
        configs['terraform/vpc.tf'] = self._get_terraform_vpc(app_name)
        configs['terraform/ecs.tf'] = self._get_terraform_ecs(app_name)
        configs['terraform/rds.tf'] = self._get_terraform_rds(app_name)

        return configs

    def _generate_cloudformation_configs(self, app_name: str, services: List[str]) -> Dict[str, str]:
        """Generate AWS CloudFormation templates."""
        configs = {}

        configs['cloudformation/main.yaml'] = self._get_cloudformation_template(app_name)

        return configs

    def _generate_cicd_configs(self, app_name: str) -> Dict[str, str]:
        """Generate CI/CD pipeline configurations."""
        configs = {}

        configs['.github/workflows/build.yml'] = self._get_github_actions_build(app_name)
        configs['.github/workflows/test.yml'] = self._get_github_actions_test(app_name)
        configs['.github/workflows/deploy.yml'] = self._get_github_actions_deploy(app_name)

        configs['.gitlab-ci.yml'] = self._get_gitlab_ci(app_name)

        return configs

    # Template generators

    def _get_dockerfile(self, framework: str) -> str:
        """Generate Dockerfile based on framework."""
        if framework == 'django':
            return '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV DEBUG=False

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
'''
        elif framework == 'fastapi':
            return '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
        elif framework == 'spring':
            return '''FROM maven:3.8-openjdk-17 AS builder

WORKDIR /app
COPY . .
RUN mvn clean package -DskipTests

FROM openjdk:17-slim

WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
'''
        elif framework == 'go':
            return '''FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY . .
RUN go build -o main .

FROM alpine:latest

WORKDIR /app
COPY --from=builder /app/main .
COPY --from=builder /app/.env .

EXPOSE 8080

CMD ["./main"]
'''
        else:
            return '''FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
'''

    def _get_dockerignore(self) -> str:
        return '''node_modules
npm-debug.log
.git
.gitignore
README.md
.env
.DS_Store
__pycache__
*.pyc
*.pyo
.venv
.pytest_cache
.coverage
build/
dist/
*.egg-info/
.vscode
.idea
target/
'''

    def _get_docker_compose(self, app_name: str, services: List[str]) -> str:
        """Generate docker-compose.yml."""
        service_defs = ''

        if 'postgres' in services:
            service_defs += '''
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME:-''' + app_name + '''}
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-password}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
'''

        if 'redis' in services:
            service_defs += '''
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
'''

        if 'rabbitmq' in services:
            service_defs += '''
  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBIT_USER:-guest}
      RABBITMQ_DEFAULT_PASS: ${RABBIT_PASS:-guest}
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
'''

        return f'''version: '3.9'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=${{DEBUG:-False}}
      - DATABASE_URL=${{DATABASE_URL:-postgresql://postgres:password@postgres:5432/''' + app_name + '''}}
      - REDIS_URL=${{REDIS_URL:-redis://redis:6379}}
    depends_on:{''' + '\n      '.join([f'- {service}' for service in ['postgres', 'redis', 'rabbitmq'] if service in services]) + '''}
    networks:
      - backend
{service_defs}
volumes:
  postgres_data:

networks:
  backend:
    driver: bridge
'''

    def _get_k8s_namespace(self, app_name: str) -> str:
        return f'''apiVersion: v1
kind: Namespace
metadata:
  name: {app_name}
  labels:
    app: {app_name}
'''

    def _get_k8s_configmap(self, app_name: str) -> str:
        return f'''apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-config
  namespace: {app_name}
data:
  LOG_LEVEL: "INFO"
  DEBUG: "false"
  PORT: "8000"
'''

    def _get_k8s_deployment(self, app_name: str) -> str:
        return f'''apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  namespace: {app_name}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
      - name: {app_name}
        image: {{registry}}/{app_name}:{{tag}}
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: {app_name}-config
              key: LOG_LEVEL
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
'''

    def _get_k8s_service(self, app_name: str) -> str:
        return f'''apiVersion: v1
kind: Service
metadata:
  name: {app_name}
  namespace: {app_name}
spec:
  type: ClusterIP
  selector:
    app: {app_name}
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
'''

    def _get_k8s_ingress(self, app_name: str) -> str:
        return f'''apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {app_name}
  namespace: {app_name}
spec:
  ingressClassName: nginx
  rules:
  - host: {app_name}.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {app_name}
            port:
              number: 80
'''

    def _get_k8s_hpa(self, app_name: str) -> str:
        return f'''apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {app_name}
  namespace: {app_name}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {app_name}
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
'''

    def _get_terraform_main(self, app_name: str) -> str:
        return f'''terraform {{
  required_version = ">= 1.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}

  backend "s3" {{
    bucket         = "terraform-state-''' + app_name + '''"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }}
}}

provider "aws" {{
  region = var.aws_region
}}
'''

    def _get_terraform_variables(self) -> str:
        return '''variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "app_name" {
  description = "Application name"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
}

variable "instance_type" {
  description = "EC2 instance type"
  default     = "t3.micro"
}
'''

    def _get_terraform_outputs(self) -> str:
        return '''output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.main.endpoint
}
'''

    def _get_terraform_vpc(self, app_name: str) -> str:
        return f'''resource "aws_vpc" "{app_name}" {{
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {{
    Name = "{app_name}-vpc"
  }}
}}

resource "aws_subnet" "public" {{
  vpc_id                  = aws_vpc.{app_name}.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${{data.aws_availability_zones.available.names[0]}}"
  map_public_ip_on_launch = true

  tags = {{
    Name = "{app_name}-public-subnet"
  }}
}}

resource "aws_internet_gateway" "{app_name}" {{
  vpc_id = aws_vpc.{app_name}.id

  tags = {{
    Name = "{app_name}-igw"
  }}
}}
'''

    def _get_terraform_ecs(self, app_name: str) -> str:
        return f'''resource "aws_ecs_cluster" "main" {{
  name = "{app_name}-cluster"
}}

resource "aws_ecs_task_definition" "main" {{
  family                   = "{app_name}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"

  container_definitions = jsonencode([{{
    name      = "{app_name}"
    image     = "{{image_uri}}"
    essential = true
    portMappings = [{{
      containerPort = 8000
      hostPort      = 8000
      protocol      = "tcp"
    }}]
  }}])
}}
'''

    def _get_terraform_rds(self, app_name: str) -> str:
        return f'''resource "aws_db_instance" "main" {{
  identifier     = "{app_name}-db"
  engine         = "postgres"
  engine_version = "15.1"
  instance_class = "db.t3.micro"

  allocated_storage = 20
  storage_encrypted = true

  db_name  = "{app_name}"
  username = var.db_username
  password = random_password.db_password.result

  skip_final_snapshot       = true
  publicly_accessible       = false
  vpc_security_group_ids    = [aws_security_group.rds.id]
  db_subnet_group_name      = aws_db_subnet_group.main.name

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
}}
'''

    def _get_cloudformation_template(self, app_name: str) -> str:
        return f'''AWSTemplateFormatVersion: '2010-09-09'
Description: '{app_name} CloudFormation Template'

Parameters:
  ImageUri:
    Type: String
    Description: Docker image URI

Resources:
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: {app_name}-cluster

  TaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Family: {app_name}
      NetworkMode: awsvpc
      RequiresCompatibilities:
        - FARGATE
      Cpu: '256'
      Memory: '512'
      ContainerDefinitions:
        - Name: {app_name}
          Image: !Ref ImageUri
          PortMappings:
            - ContainerPort: 8000

  ECSService:
    Type: AWS::ECS::Service
    Properties:
      ServiceName: {app_name}
      Cluster: !Ref ECSCluster
      TaskDefinition: !Ref TaskDefinition
      DesiredCount: 1
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          AssignPublicIp: ENABLED
          Subnets:
            - !Ref PublicSubnet

Outputs:
  ClusterName:
    Value: !Ref ECSCluster
'''

    def _get_github_actions_build(self, app_name: str) -> str:
        return f'''name: Build

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Build image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: false
          tags: {app_name}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
'''

    def _get_github_actions_test(self, app_name: str) -> str:
        return f'''name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Run tests
        run: |
          python -m pytest

      - name: Upload coverage
        uses: codecov/codecov-action@v3
'''

    def _get_github_actions_deploy(self, app_name: str) -> str:
        return f'''name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{{{ secrets.AWS_ACCESS_KEY_ID }}}}
          aws-secret-access-key: ${{{{ secrets.AWS_SECRET_ACCESS_KEY }}}}
          aws-region: us-east-1

      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster {app_name}-cluster --service {app_name} --force-new-deployment
'''

    def _get_gitlab_ci(self, app_name: str) -> str:
        return f'''stages:
  - build
  - test
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: ""

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t {app_name}:$CI_COMMIT_SHA .
    - docker tag {app_name}:$CI_COMMIT_SHA {app_name}:latest

test:
  stage: test
  image: python:3.11
  services:
    - postgres:15
  script:
    - pip install -r requirements.txt
    - pytest

deploy:
  stage: deploy
  image: alpine:latest
  script:
    - echo "Deploying {app_name} to production"
  only:
    - main
'''


def main():
    """Test enterprise config generation."""
    gen = EnterpriseConfigGenerator('fastapi', 'kubernetes')
    files = gen.generate_enterprise_configs('myapp', ['postgres', 'redis', 'rabbitmq'], {})
    for filepath, content in files.items():
        print(f"File: {filepath}\n---\n")


if __name__ == '__main__':
    main()
