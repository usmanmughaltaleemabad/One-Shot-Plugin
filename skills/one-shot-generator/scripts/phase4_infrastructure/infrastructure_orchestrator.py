"""
Infrastructure Orchestrator - Coordinates all infrastructure generation for Phase 4

Orchestrates:
- Docker container configurations
- Kubernetes manifests
- Terraform infrastructure-as-code
- CI/CD pipelines
- Monitoring and observability
- Security configurations
- Networking and load balancing
- Database infrastructure
"""

from typing import Dict, Any, List
from core.docker_generator import generate_docker_configs
from core.kubernetes_generator import generate_kubernetes_manifests
from core.terraform_generator import generate_terraform_configs
from core.cicd_generator import generate_cicd_configs
from core.monitoring_generator import generate_monitoring_configs
from core.security_generator import generate_security_configs
from core.networking_generator import generate_networking_configs
from core.database_infrastructure_generator import generate_database_infrastructure_configs


class InfrastructureOrchestrator:
    """Orchestrate all infrastructure generation"""

    def __init__(self, framework: str, language: str, app_name: str = "app", domain: str = "example.com"):
        self.framework = framework
        self.language = language
        self.app_name = app_name
        self.domain = domain

    def generate_all_infrastructure(self) -> Dict[str, Dict[str, str]]:
        """
        Generate all infrastructure configurations.

        Returns:
            Dictionary mapping categories to generated files:
            {
                'docker': {filename: content, ...},
                'kubernetes': {filename: content, ...},
                'terraform': {filename: content, ...},
                'cicd': {filename: content, ...},
                'monitoring': {filename: content, ...},
                'security': {filename: content, ...},
                'networking': {filename: content, ...},
                'database': {filename: content, ...}
            }
        """
        return {
            'docker': self.generate_docker(),
            'kubernetes': self.generate_kubernetes(),
            'terraform': self.generate_terraform(),
            'cicd': self.generate_cicd(),
            'monitoring': self.generate_monitoring(),
            'security': self.generate_security(),
            'networking': self.generate_networking(),
            'database': self.generate_database_infrastructure(),
        }

    def generate_docker(self) -> Dict[str, str]:
        """Generate Docker configurations"""
        return generate_docker_configs(self.framework, self.language)

    def generate_kubernetes(self) -> Dict[str, str]:
        """Generate Kubernetes manifests"""
        return generate_kubernetes_manifests(self.framework, self.language, self.app_name)

    def generate_terraform(self) -> Dict[str, str]:
        """Generate Terraform infrastructure code"""
        return generate_terraform_configs(self.framework, self.language, self.app_name)

    def generate_cicd(self) -> Dict[str, str]:
        """Generate CI/CD pipeline configurations"""
        return generate_cicd_configs(self.framework, self.language, self.app_name)

    def generate_monitoring(self) -> Dict[str, str]:
        """Generate monitoring and observability configs"""
        return generate_monitoring_configs(self.framework, self.language, self.app_name)

    def generate_security(self) -> Dict[str, str]:
        """Generate security configurations"""
        return generate_security_configs(self.framework, self.language, self.app_name, self.domain)

    def generate_networking(self) -> Dict[str, str]:
        """Generate networking and load balancing configs"""
        return generate_networking_configs(self.framework, self.language, self.app_name, self.domain)

    def generate_database_infrastructure(self) -> Dict[str, str]:
        """Generate database infrastructure configs"""
        return generate_database_infrastructure_configs(self.framework, self.language, self.app_name)

    def generate_deployment_guide(self) -> str:
        """Generate deployment guide"""
        return f"""
# {self.app_name} Infrastructure Deployment Guide

## Overview

This guide covers deploying {self.app_name} infrastructure across multiple environments using:
- Docker for containerization
- Kubernetes for orchestration
- Terraform for infrastructure-as-code
- Multiple CI/CD platforms
- Comprehensive monitoring and observability
- Security-first architecture

## Prerequisites

### Required Tools
- Docker CLI (v20.10+)
- kubectl (v1.27+)
- Terraform (v1.0+)
- Helm (v3.10+)
- Git
- AWS CLI (for AWS deployments)

### AWS Account Setup
```bash
aws configure
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

## Phase 1: Docker Setup

### Build container image
```bash
docker build -t {self.app_name}:latest .
docker tag {self.app_name}:latest $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/{self.app_name}:latest
```

### Push to registry
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/{self.app_name}:latest
```

## Phase 2: Infrastructure with Terraform

### Initialize Terraform
```bash
cd terraform/
terraform init -backend-config="key=prod/terraform.tfstate"
terraform plan -var-file="environments/prod.tfvars"
```

### Create S3 backend for state
```bash
aws s3api create-bucket \
  --bucket {self.app_name}-terraform-state \
  --region us-east-1

aws dynamodb create-table \
  --table-name {self.app_name}-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

### Apply infrastructure
```bash
terraform apply -auto-approve -var-file="environments/prod.tfvars"
terraform output -raw kubeconfig > ~/.kube/{self.app_name}-config
export KUBECONFIG=~/.kube/{self.app_name}-config
```

## Phase 3: Kubernetes Deployment

### Create namespaces
```bash
kubectl create namespace {self.app_name}
kubectl create namespace monitoring
kubectl create namespace security
```

### Deploy secrets
```bash
kubectl create secret generic {self.app_name}-secrets \\
  --from-literal=database-url="postgresql://..." \\
  --from-literal=redis-url="redis://..." \\
  -n {self.app_name}
```

### Apply Kubernetes manifests
```bash
# Namespace and RBAC
kubectl apply -f k8s-namespace.yaml

# Deployment
kubectl apply -f k8s-deployment.yaml
kubectl apply -f k8s-service.yaml
kubectl apply -f k8s-ingress.yaml

# Configuration
kubectl apply -f k8s-configmap.yaml

# Auto-scaling
kubectl apply -f k8s-hpa.yaml

# Verify deployment
kubectl rollout status deployment/{self.app_name} -n {self.app_name}
kubectl get pods -n {self.app_name}
```

## Phase 4: Database Setup

### PostgreSQL with Patroni HA
```bash
kubectl apply -f database/postgresql-ha.yaml
kubectl wait --for=condition=ready pod -l app=postgresql -n default --timeout=300s
```

### Redis Cluster
```bash
kubectl apply -f database/redis-cluster.yaml
kubectl wait --for=condition=ready pod -l app=redis-cluster -n default --timeout=300s
```

### Configure backups
```bash
kubectl apply -f database/backup-strategy.yaml
```

## Phase 5: Monitoring Setup

### Install Prometheus
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \\
  -f monitoring/prometheus.yml \\
  -n monitoring
```

### Install Grafana
```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install grafana grafana/grafana \\
  -n monitoring
```

### Install Loki for logging
```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \\
  -n monitoring
```

### Load Grafana dashboard
```bash
kubectl port-forward -n monitoring svc/grafana 3000:80
# Open http://localhost:3000
# Import dashboard: cat monitoring/grafana/dashboard.json
```

## Phase 6: Security Hardening

### Install cert-manager
```bash
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \\
  --namespace cert-manager \\
  --create-namespace \\
  --set installCRDs=true
```

### Apply certificate issuer
```bash
kubectl apply -f security/cert-manager-issuer.yaml
```

### Install Vault
```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm install vault hashicorp/vault \\
  -f security/vault-config.hcl \\
  -n security
```

### Apply network policies
```bash
kubectl apply -f security/network-policies.yaml
kubectl apply -f security/pod-security-policy.yaml
```

## Phase 7: CI/CD Pipeline Setup

### GitHub Actions
```bash
mkdir -p .github/workflows
cp .github/workflows/build-deploy.yml .
git add .github/workflows/build-deploy.yml
git commit -m "Add GitHub Actions CI/CD pipeline"
```

### GitLab CI
```bash
cp .gitlab-ci.yml .
git add .gitlab-ci.yml
git commit -m "Add GitLab CI pipeline"
```

### Jenkins
```bash
cp Jenkinsfile .
git add Jenkinsfile
git commit -m "Add Jenkins pipeline"
```

## Phase 8: Networking & Ingress

### Install NGINX Ingress Controller
```bash
helm repo add nginx-stable https://helm.nginx.com/stable
helm install nginx-ingress nginx-stable/nginx-ingress \\
  --set controller.service.type=LoadBalancer \\
  -n ingress-nginx \\
  --create-namespace
```

### Deploy ingress
```bash
kubectl apply -f networking/nginx-ingress.yaml
kubectl get ingress -n {self.app_name}
```

### DNS configuration
```bash
kubectl apply -f networking/dns-config.yaml
# Update Route 53 or your DNS provider with the Ingress IP
```

## Health Checks

### Application health
```bash
kubectl port-forward -n {self.app_name} svc/{self.app_name} 8000:8000
curl http://localhost:8000/health
```

### Database health
```bash
kubectl exec -it postgresql-0 -- psql -U postgres -c "SELECT version();"
```

### Redis health
```bash
kubectl exec -it redis-cluster-0 -- redis-cli cluster info
```

### Kubernetes cluster health
```bash
kubectl get nodes
kubectl get pods --all-namespaces
kubectl describe nodes
```

## Monitoring Dashboards

### Prometheus
```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Open http://localhost:9090
```

### Grafana
```bash
kubectl port-forward -n monitoring svc/grafana 3000:80
kubectl get secret -n monitoring grafana -o jsonpath="{{.data.admin-password}}" | base64 --decode
# Open http://localhost:3000
# Default credentials: admin / [decoded password]
```

### AlertManager
```bash
kubectl port-forward -n monitoring svc/alertmanager 9093:9093
# Open http://localhost:9093
```

## Maintenance

### Update Kubernetes version
```bash
terraform apply -var cluster_version=1.28 -auto-approve
```

### Scale application
```bash
kubectl scale deployment {self.app_name} --replicas=5 -n {self.app_name}
```

### Database backup and recovery
```bash
# Trigger backup
kubectl exec -it postgresql-0 -- pg_dump -U postgres {self.app_name} > backup.sql

# Restore from backup
kubectl exec -it postgresql-0 -- psql -U postgres < backup.sql
```

### Rolling update
```bash
kubectl set image deployment/{self.app_name} {self.app_name}=myregistry.azurecr.io/{self.app_name}:v2 -n {self.app_name}
kubectl rollout status deployment/{self.app_name} -n {self.app_name}
```

## Troubleshooting

### Pod not starting
```bash
kubectl describe pod -n {self.app_name}
kubectl logs -n {self.app_name} <pod-name>
```

### Database connection issues
```bash
kubectl exec -it postgresql-0 -- psql -U postgres -c "SELECT datname, usename FROM pg_stat_activity;"
```

### High memory usage
```bash
kubectl top pod -n {self.app_name}
kubectl top nodes
```

### Network policy issues
```bash
kubectl get networkpolicies -n {self.app_name}
kubectl describe networkpolicy -n {self.app_name}
```

## Disaster Recovery

### Backup Kubernetes cluster
```bash
velero backup create {self.app_name}-backup
```

### Restore from backup
```bash
velero restore create --from-backup {self.app_name}-backup
```

### Database point-in-time recovery
```bash
# Restore to specific time using WAL archiving
pg_basebackup -h localhost -U postgres -D /recovery -v -P -W
```

## Production Checklist

- [ ] SSL/TLS certificates configured and valid
- [ ] Database backups automated and tested
- [ ] Monitoring and alerting configured
- [ ] Network policies enforced
- [ ] Pod security policies in place
- [ ] RBAC properly configured
- [ ] Resource requests and limits set
- [ ] Health checks configured
- [ ] Logging aggregation enabled
- [ ] Disaster recovery plan documented
- [ ] Load testing completed
- [ ] Security audit passed

## Support

For issues or questions:
1. Check logs: `kubectl logs -f -n {self.app_name} <pod-name>`
2. Review monitoring dashboards
3. Check infrastructure status: `terraform state list`
4. Review CI/CD pipeline logs
"""

    def generate_deployment_checklist(self) -> str:
        """Generate deployment checklist"""
        return f"""
# {self.app_name} Deployment Checklist

## Pre-Deployment (1-2 days before)

### Infrastructure
- [ ] AWS account configured and credentials set
- [ ] VPC and subnets planned
- [ ] IAM roles and policies created
- [ ] S3 buckets for backups and state created
- [ ] DynamoDB tables for Terraform locks created

### Code & Configuration
- [ ] Docker image built and tested locally
- [ ] Docker image pushed to registry
- [ ] Kubernetes manifests reviewed
- [ ] Environment variables documented
- [ ] Secrets managed securely
- [ ] Configuration files validated

### Documentation
- [ ] Deployment guide reviewed
- [ ] Runbooks prepared
- [ ] Escalation contacts documented
- [ ] Rollback procedures tested

## Deployment Day

### Pre-Deployment (1 hour before)

- [ ] Team on standby
- [ ] Monitoring dashboards open
- [ ] Logs aggregation ready
- [ ] Database backups current
- [ ] DNS TTL lowered to 5 minutes

### Infrastructure Provisioning (30-45 minutes)

- [ ] Terraform plan reviewed
- [ ] Infrastructure created: `terraform apply`
- [ ] VPC and network verified
- [ ] EKS cluster healthy
- [ ] RDS instance healthy
- [ ] Redis cluster healthy

### Kubernetes Deployment (15-30 minutes)

- [ ] Namespaces created
- [ ] Secrets configured
- [ ] ConfigMaps applied
- [ ] Deployments created
- [ ] Services created
- [ ] Ingress configured

### Application Startup (5-10 minutes)

- [ ] Pods starting and healthy
- [ ] Database migrations running
- [ ] Cache warming complete
- [ ] Health checks passing
- [ ] Load balancer healthy

### Verification (10-15 minutes)

- [ ] Application endpoints responding
- [ ] Health check endpoints working
- [ ] Database connectivity verified
- [ ] Cache functionality tested
- [ ] Logging working
- [ ] Metrics collecting

### Monitoring (5 minutes)

- [ ] Prometheus targets healthy
- [ ] Grafana dashboards showing metrics
- [ ] Alerts configured
- [ ] No error spikes in logs

### Post-Deployment

- [ ] Update DNS records (if needed)
- [ ] Announce deployment completion
- [ ] Document any issues encountered
- [ ] Schedule post-deployment retrospective
- [ ] Monitor for 1 hour for issues

## Rollback Procedures

### If deployment fails before going live:

```bash
# Scale down new deployment
kubectl scale deployment {self.app_name} --replicas=0

# Use previous version from rolling update
kubectl rollout undo deployment/{self.app_name}

# Or destroy and redeploy from previous state
terraform destroy -auto-approve
terraform apply -auto-approve
```

### If issues appear after deployment:

```bash
# Check logs
kubectl logs -f deployment/{self.app_name} -n {self.app_name}

# Increase replica count for resilience
kubectl scale deployment {self.app_name} --replicas=3

# Force rolling restart
kubectl rollout restart deployment/{self.app_name}

# If needed, revert to previous commit
git revert <commit-hash>
git push
# CI/CD will automatically redeploy
```

## Post-Deployment Validation

### First 24 hours:

- [ ] Monitor error rates (should be < 0.1%)
- [ ] Monitor latency (p95 < 500ms)
- [ ] Monitor CPU usage (< 70%)
- [ ] Monitor memory usage (< 80%)
- [ ] Monitor database connections
- [ ] Check for memory leaks
- [ ] Verify log rotation working
- [ ] Verify backups completing
- [ ] Test failover scenarios
- [ ] Load test to baseline

### First week:

- [ ] Monitor for memory leaks
- [ ] Verify all alerts working
- [ ] Test disaster recovery
- [ ] Performance profile under real load
- [ ] Verify scaling policies working
- [ ] Check backup restoration
- [ ] Review logs for issues
- [ ] Optimize resource requests/limits

### First month:

- [ ] Review monitoring alerts (tune thresholds)
- [ ] Analyze performance metrics
- [ ] Plan optimization work
- [ ] Conduct security audit
- [ ] Update documentation
- [ ] Train team on new infrastructure
"""


def orchestrate_infrastructure_generation(framework: str, language: str, app_name: str = "app", domain: str = "example.com") -> Dict[str, Any]:
    """
    Main entry point for Phase 4 infrastructure generation.

    Args:
        framework: django, fastapi, spring
        language: python, javascript
        app_name: application name
        domain: domain name

    Returns:
        Complete infrastructure package with all configs and guides
    """
    orchestrator = InfrastructureOrchestrator(framework, language, app_name, domain)

    return {
        'infrastructure': orchestrator.generate_all_infrastructure(),
        'deployment_guide': orchestrator.generate_deployment_guide(),
        'deployment_checklist': orchestrator.generate_deployment_checklist(),
    }
