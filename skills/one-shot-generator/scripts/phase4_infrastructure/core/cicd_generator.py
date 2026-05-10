"""
CI/CD Pipeline Generator - Continuous Integration and Deployment configurations

Generates:
- GitHub Actions workflows
- GitLab CI pipelines
- Jenkins pipelines
- CircleCI configurations
- Build, test, security scanning, and deployment stages
"""

from typing import Dict, Any


class CICDGenerator:
    """Generate CI/CD pipeline configurations"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_github_actions_workflow(self, app_name: str = "app") -> str:
        """Generate GitHub Actions workflow"""
        return f"""
name: Build and Deploy

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{{{ github.repository }}}}

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 black isort mypy

      - name: Lint with flake8
        run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

      - name: Format check with black
        run: black --check .

      - name: Type check with mypy
        run: mypy . || true

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt pytest pytest-cov pytest-django

      - name: Run tests
        run: pytest --cov=. --cov-report=xml
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unittests
          fail_ci_if_error: false

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  build:
    needs: [lint, test, security]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to Container Registry
        if: github.event_name == 'push'
        uses: docker/login-action@v2
        with:
          registry: ${{{{ env.REGISTRY }}}}
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{{{version}}}}
            type=semver,pattern={{{{major}}}}.{{{{minor}}}}
            type=sha

      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: ${{{{ github.event_name == 'push' }}}}
          tags: ${{{{ steps.meta.outputs.tags }}}}
          labels: ${{{{ steps.meta.outputs.labels }}}}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop' && github.event_name == 'push'
    environment:
      name: staging

    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        run: |
          mkdir -p $HOME/.kube
          echo "${{{{ secrets.KUBE_CONFIG }}}}" | base64 -d > $HOME/.kube/config
          chmod 600 $HOME/.kube/config

      - name: Deploy to staging
        run: |
          kubectl set image deployment/{app_name} {app_name}=ghcr.io/${{{{ github.repository }}}}:${{{{ github.sha }}}} -n staging
          kubectl rollout status deployment/{app_name} -n staging

  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment:
      name: production
      url: https://{app_name}.example.com

    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        run: |
          mkdir -p $HOME/.kube
          echo "${{{{ secrets.KUBE_CONFIG }}}}" | base64 -d > $HOME/.kube/config
          chmod 600 $HOME/.kube/config

      - name: Deploy to production
        run: |
          kubectl set image deployment/{app_name} {app_name}=ghcr.io/${{{{ github.repository }}}}:${{{{ github.sha }}}} -n production
          kubectl rollout status deployment/{app_name} -n production

      - name: Run smoke tests
        run: |
          ./scripts/smoke-tests.sh https://{app_name}.example.com
"""

    def generate_gitlab_ci_pipeline(self, app_name: str = "app") -> str:
        """Generate GitLab CI pipeline"""
        return f"""
stages:
  - lint
  - test
  - security
  - build
  - deploy

variables:
  DOCKER_IMAGE: $CI_REGISTRY_IMAGE
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: ""

lint:
  stage: lint
  image: python:3.11
  script:
    - pip install flake8 black isort mypy
    - flake8 . --count --select=E9,F63,F7,F82
    - black --check .
    - mypy . || true
  only:
    - merge_requests
    - develop
    - main

test:
  stage: test
  image: python:3.11
  services:
    - postgres:15
    - redis:7
  variables:
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_password
    POSTGRES_DB: test_db
    DATABASE_URL: postgresql://test_user:test_password@postgres:5432/test_db
    REDIS_URL: redis://redis:6379/0
  script:
    - pip install -r requirements.txt pytest pytest-cov pytest-django
    - pytest --cov=. --cov-report=term --cov-report=html
  artifacts:
    paths:
      - htmlcov/
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
  only:
    - merge_requests
    - develop
    - main

security-scan:
  stage: security
  image: aquasec/trivy:latest
  script:
    - trivy fs --format json --output trivy-report.json .
  artifacts:
    reports:
      container_scanning: trivy-report.json
  only:
    - merge_requests
    - develop
    - main

build-image:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $DOCKER_IMAGE:$CI_COMMIT_SHA -t $DOCKER_IMAGE:latest .
    - docker push $DOCKER_IMAGE:$CI_COMMIT_SHA
    - docker push $DOCKER_IMAGE:latest
  only:
    - develop
    - main

deploy-staging:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl config use-context $KUBE_CONTEXT_STAGING
    - kubectl set image deployment/{app_name} {app_name}=$DOCKER_IMAGE:$CI_COMMIT_SHA -n staging
    - kubectl rollout status deployment/{app_name} -n staging
  environment:
    name: staging
    kubernetes:
      namespace: staging
  only:
    - develop

deploy-production:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl config use-context $KUBE_CONTEXT_PRODUCTION
    - kubectl set image deployment/{app_name} {app_name}=$DOCKER_IMAGE:$CI_COMMIT_SHA -n production
    - kubectl rollout status deployment/{app_name} -n production
    - ./scripts/smoke-tests.sh https://{app_name}.example.com
  environment:
    name: production
    kubernetes:
      namespace: production
    url: https://{app_name}.example.com
  only:
    - main
  when: manual
"""

    def generate_jenkins_pipeline(self, app_name: str = "app") -> str:
        """Generate Jenkins Declarative Pipeline"""
        return f"""
pipeline {{
    agent any

    environment {{
        DOCKER_REGISTRY = 'docker.io'
        DOCKER_IMAGE = '${{DOCKER_REGISTRY}}/{app_name}'
        REGISTRY_CREDENTIALS = 'docker-registry-credentials'
        KUBE_CREDENTIALS_STAGING = 'kubeconfig-staging'
        KUBE_CREDENTIALS_PROD = 'kubeconfig-production'
    }}

    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
            }}
        }}

        stage('Lint') {{
            steps {{
                sh '''
                    python -m pip install flake8 black mypy
                    flake8 . --count --select=E9,F63,F7,F82
                    black --check .
                '''
            }}
        }}

        stage('Test') {{
            steps {{
                sh '''
                    python -m pip install -r requirements.txt pytest pytest-cov
                    pytest --cov=. --cov-report=xml --junitxml=test-results.xml
                '''
            }}
            post {{
                always {{
                    junit 'test-results.xml'
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')]
                }}
            }}
        }}

        stage('Security Scan') {{
            steps {{
                sh '''
                    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
                    trivy fs --format sarif --output trivy-report.sarif .
                '''
            }}
            post {{
                always {{
                    recordIssues(tools: [sarif(pattern: 'trivy-report.sarif')])
                }}
            }}
        }}

        stage('Build Image') {{
            when {{
                branch 'main'
                branch 'develop'
            }}
            steps {{
                script {{
                    withDockerRegistry([credentialsId: env.REGISTRY_CREDENTIALS, url: 'https://' + env.DOCKER_REGISTRY]) {{
                        sh '''
                            docker build -t ${{DOCKER_IMAGE}}:${{BUILD_NUMBER}} -t ${{DOCKER_IMAGE}}:latest .
                            docker push ${{DOCKER_IMAGE}}:${{BUILD_NUMBER}}
                            docker push ${{DOCKER_IMAGE}}:latest
                        '''
                    }}
                }}
            }}
        }}

        stage('Deploy to Staging') {{
            when {{
                branch 'develop'
            }}
            environment {{
                KUBE_CONFIG = credentials(env.KUBE_CREDENTIALS_STAGING)
            }}
            steps {{
                sh '''
                    kubectl config use-context staging
                    kubectl set image deployment/{app_name} {app_name}=${{DOCKER_IMAGE}}:${{BUILD_NUMBER}} -n staging
                    kubectl rollout status deployment/{app_name} -n staging
                '''
            }}
        }}

        stage('Deploy to Production') {{
            when {{
                branch 'main'
            }}
            environment {{
                KUBE_CONFIG = credentials(env.KUBE_CREDENTIALS_PROD)
            }}
            input {{
                message "Deploy to production?"
                ok "Deploy"
            }}
            steps {{
                sh '''
                    kubectl config use-context production
                    kubectl set image deployment/{app_name} {app_name}=${{DOCKER_IMAGE}}:${{BUILD_NUMBER}} -n production
                    kubectl rollout status deployment/{app_name} -n production
                '''
            }}
        }}

        stage('Smoke Tests') {{
            when {{
                branch 'main'
            }}
            steps {{
                sh './scripts/smoke-tests.sh https://{app_name}.example.com'
            }}
        }}
    }}

    post {{
        always {{
            cleanWs()
        }}
        failure {{
            mail(
                subject: "Pipeline Failed: ${{JOB_NAME}} #${{BUILD_NUMBER}}",
                body: "Check console output at ${{BUILD_URL}} to view the results.",
                to: env.CHANGE_AUTHOR_EMAIL
            )
        }}
    }}
}}
"""

    def generate_circleci_config(self, app_name: str = "app") -> str:
        """Generate CircleCI configuration"""
        return f"""
version: 2.1

orbs:
  docker: circleci/docker@2.1.4
  kubernetes: circleci/kubernetes@1.3.1

workflows:
  version: 2
  build-and-deploy:
    jobs:
      - lint
      - test
      - security-scan
      - build-image:
          requires:
            - lint
            - test
            - security-scan
          filters:
            branches:
              only:
                - main
                - develop
      - deploy-staging:
          requires:
            - build-image
          filters:
            branches:
              only: develop
      - deploy-production:
          requires:
            - build-image
          filters:
            branches:
              only: main

jobs:
  lint:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: pip install flake8 black mypy
      - run:
          name: Run flake8
          command: flake8 . --count --select=E9,F63,F7,F82
      - run:
          name: Run black
          command: black --check .

  test:
    docker:
      - image: cimg/python:3.11
        environment:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
      - image: cimg/postgres:15
        environment:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: test_db
      - image: cimg/redis:7
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: pip install -r requirements.txt pytest pytest-cov
      - run:
          name: Run tests
          command: pytest --cov=. --cov-report=xml
      - store_test_results:
          path: test-results
      - store_artifacts:
          path: coverage.xml

  security-scan:
    docker:
      - image: aquasec/trivy:latest
    steps:
      - checkout
      - run:
          name: Run Trivy scan
          command: trivy fs --format sarif --output trivy-report.sarif .
      - store_artifacts:
          path: trivy-report.sarif

  build-image:
    executor: docker/default
    steps:
      - checkout
      - docker/check:
          registry: ${{DOCKER_REGISTRY}}
          docker-password: DOCKER_PASSWORD
          docker-username: DOCKER_USERNAME
      - docker/build:
          image: ${{DOCKER_IMAGE}}
          tag: ${{CIRCLE_SHA1}},latest
      - docker/push:
          image: ${{DOCKER_IMAGE}}
          tag: ${{CIRCLE_SHA1}},latest

  deploy-staging:
    executor: kubernetes/default
    steps:
      - run:
          name: Deploy to staging
          command: |
            kubectl config use-context staging
            kubectl set image deployment/{app_name} {app_name}=${{DOCKER_IMAGE}}:${{CIRCLE_SHA1}} -n staging
            kubectl rollout status deployment/{app_name} -n staging

  deploy-production:
    executor: kubernetes/default
    steps:
      - checkout
      - run:
          name: Deploy to production
          command: |
            kubectl config use-context production
            kubectl set image deployment/{app_name} {app_name}=${{DOCKER_IMAGE}}:${{CIRCLE_SHA1}} -n production
            kubectl rollout status deployment/{app_name} -n production
      - run:
          name: Run smoke tests
          command: ./scripts/smoke-tests.sh https://{app_name}.example.com
"""


def generate_cicd_configs(framework: str, language: str, app_name: str = "app") -> Dict[str, str]:
    """
    Generate CI/CD pipeline configurations.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = CICDGenerator(framework, language)
    output = {}

    output[".github/workflows/build-deploy.yml"] = generator.generate_github_actions_workflow(app_name)
    output[".gitlab-ci.yml"] = generator.generate_gitlab_ci_pipeline(app_name)
    output["Jenkinsfile"] = generator.generate_jenkins_pipeline(app_name)
    output[".circleci/config.yml"] = generator.generate_circleci_config(app_name)

    return output
