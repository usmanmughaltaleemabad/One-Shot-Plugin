"""
GitOps Generator - Declarative deployment automation with ArgoCD and Flux

Generates:
- ArgoCD application definitions
- Flux GitRepository and Kustomization
- Deployment strategies (sync policies, waves)
- ApplicationSet for multi-environment
- Notification integrations
- RBAC for GitOps
"""

from typing import Dict, Any


class GitOpsGenerator:
    """Generate GitOps infrastructure configurations"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_argocd_application(self, app_name: str = "app", repo_url: str = "https://github.com/user/repo") -> str:
        """Generate ArgoCD Application definition"""
        return f"""
apiVersion: v1
kind: Namespace
metadata:
  name: argocd
---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {app_name}
  namespace: argocd
spec:
  project: default
  source:
    repoURL: {repo_url}
    targetRevision: main
    path: k8s/
    helm:
      releaseName: {app_name}
      values: |
        image:
          repository: myregistry.azurecr.io/{app_name}
          tag: latest
        replicas: 3
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
  destination:
    server: https://kubernetes.default.svc
    namespace: {app_name}
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - RespectIgnoreDifferences=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  notification:
    enabled: true
---
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: {app_name}-multi-env
  namespace: argocd
spec:
  goTemplate: true
  generators:
    - list:
        elements:
          - name: staging
            cluster: https://staging-cluster.example.com
            namespace: {app_name}-staging
          - name: production
            cluster: https://prod-cluster.example.com
            namespace: {app_name}-production
  template:
    metadata:
      name: '{{{{.name}}}}-{app_name}'
    spec:
      project: default
      source:
        repoURL: {repo_url}
        targetRevision: main
        path: k8s/
        helm:
          releaseName: {app_name}
          values: |
            environment: '{{{{.name}}}}'
            replicas: {{{{if eq .name "production"}}}}3{{{{else}}}}2{{{{end}}}}
      destination:
        server: '{{{{.cluster}}}}'
        namespace: '{{{{.namespace}}}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
---
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: {app_name}
  namespace: argocd
spec:
  sourceRepos:
    - {repo_url}
  destinations:
    - namespace: '{app_name}*'
      server: '*'
  clusterResourceWhitelist:
    - group: '*'
      kind: '*'
  namespaceResourceBlacklist:
    - group: ''
      kind: ResourceQuota
    - group: ''
      kind: LimitRange
"""

    def generate_flux_configuration(self, app_name: str = "app", repo_url: str = "https://github.com/user/repo") -> str:
        """Generate Flux GitRepository and Kustomization"""
        return f"""
apiVersion: v1
kind: Namespace
metadata:
  name: flux-system
---
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: {app_name}
  namespace: flux-system
spec:
  interval: 1m
  url: {repo_url}
  ref:
    branch: main
  secretRef:
    name: {app_name}-git-credentials
  timeout: 20s
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: {app_name}
  namespace: flux-system
spec:
  interval: 10m
  path: ./k8s
  prune: true
  wait: true
  timeout: 5m
  sourceRef:
    kind: GitRepository
    name: {app_name}
  postBuild:
    substitute:
      ENVIRONMENT: production
      APP_VERSION: "1.0.0"
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: {app_name}
      namespace: {app_name}
  serviceAccountName: {app_name}
  depends:
    - name: {app_name}-database
  patches:
    - target:
        group: apps
        version: v1
        kind: Deployment
        name: {app_name}
      patch: |-
        - op: replace
          path: /spec/replicas
          value: 3
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: {app_name}-database
  namespace: flux-system
spec:
  interval: 10m
  path: ./k8s/database
  prune: true
  wait: true
  sourceRef:
    kind: GitRepository
    name: {app_name}
---
apiVersion: v1
kind: Secret
metadata:
  name: {app_name}-git-credentials
  namespace: flux-system
type: Opaque
stringData:
  username: git
  password: ${{GITHUB_TOKEN}}
---
apiVersion: notification.toolkit.fluxcd.io/v1
kind: Alert
metadata:
  name: {app_name}
  namespace: flux-system
spec:
  providerRef:
    name: slack
  suspend: false
  eventSeverity: info
  eventSources:
    - kind: Kustomization
      name: {app_name}
    - kind: GitRepository
      name: {app_name}
---
apiVersion: notification.toolkit.fluxcd.io/v1
kind: Provider
metadata:
  name: slack
  namespace: flux-system
spec:
  type: slack
  address: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: {app_name}-flux
rules:
  - apiGroups: [apps]
    resources: [deployments]
    verbs: [get, list, watch, create, update, patch]
  - apiGroups: [batch]
    resources: [jobs]
    verbs: [get, list, watch]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: {app_name}-flux
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: {app_name}-flux
subjects:
  - kind: ServiceAccount
    name: {app_name}
    namespace: flux-system
"""

    def generate_deployment_waves(self, app_name: str = "app") -> str:
        """Generate progressive deployment waves"""
        return f"""
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: {app_name}-waves
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/user/repo
    targetRevision: main
    path: k8s/
  destination:
    server: https://kubernetes.default.svc
    namespace: {app_name}
  syncPolicy:
    syncOptions:
      - RespectIgnoreDifferences=true
---
apiVersion: argoproj.io/v1alpha1
kind: AppWave
metadata:
  name: {app_name}-canary
spec:
  application: {app_name}-waves
  waves:
    - name: canary
      weight: 10
      selector:
        matchLabels:
          version: canary
    - name: rolling
      weight: 90
      selector:
        matchLabels:
          version: stable
  strategy:
    canary:
      steps:
        - setWeight: 10
          pause:
            duration: 5m
        - analysis:
            metrics:
              - name: error-rate
                threshold: "< 1%"
              - name: latency-p95
                threshold: "< 500ms"
        - setWeight: 25
          pause:
            duration: 5m
        - setWeight: 50
          pause:
            duration: 5m
        - setWeight: 100
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: {app_name}-analysis
spec:
  metrics:
    - name: error-rate
      interval: 60s
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            sum(rate(http_requests_total{{job="{app_name}",status=~"5..."}}[5m])) /
            sum(rate(http_requests_total{{job="{app_name}"}}[5m]))
    - name: latency-p95
      interval: 60s
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            histogram_quantile(0.95,
              sum(rate(http_request_duration_seconds_bucket{{job="{app_name}"}}[5m])) by (le)
            )
"""

    def generate_gitops_workflow(self, app_name: str = "app") -> str:
        """Generate GitOps workflow documentation"""
        return f"""
# {app_name} GitOps Workflow

## Overview

This project uses ArgoCD for declarative, GitOps-based deployments.

## Files Structure

```
repo/
├── k8s/
│   ├── base/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── kustomization.yaml
│   │   └── configmap.yaml
│   ├── overlays/
│   │   ├── staging/
│   │   │   ├── kustomization.yaml
│   │   │   ├── replicas.yaml
│   │   │   └── config.yaml
│   │   └── production/
│   │       ├── kustomization.yaml
│   │       ├── replicas.yaml
│   │       └── config.yaml
│   └── argocd/
│       ├── application.yaml
│       ├── applicationset.yaml
│       └── project.yaml
├── .github/
│   └── workflows/
│       └── deploy.yml
└── helm/
    └── {app_name}/
        ├── Chart.yaml
        ├── values.yaml
        └── templates/

```

## Deployment Process

### 1. Code Change
```bash
# Developer commits code
git commit -m "feat: add new feature"
git push origin feature-branch
```

### 2. Pull Request
```bash
# CI/CD pipeline runs (GitHub Actions)
# - Tests
# - Security scans
# - Build Docker image
# - Create pull request
```

### 3. Review & Merge
```bash
# Code review on GitHub
# Merge to main branch
git merge --squash feature-branch
```

### 4. ArgoCD Sync
```bash
# ArgoCD detects main branch change (polls every 3 minutes)
# Or via webhook (immediate)
# Syncs manifests to Kubernetes cluster
```

### 5. Verification
```bash
# ArgoCD runs health checks
# Monitors deployment status
# Sends notifications to Slack
```

## Making Changes

### Update Deployment Replicas

1. **Edit overlay**
   ```bash
   vim k8s/overlays/production/kustomization.yaml
   # Change replicas: 3 -> 5
   ```

2. **Commit and push**
   ```bash
   git commit -am "ops: scale production to 5 replicas"
   git push origin main
   ```

3. **ArgoCD detects and syncs**
   ```bash
   # ArgoCD automatically applies the change
   kubectl get deployment -n {app_name}
   # Observe replicas increasing to 5
   ```

### Update Image

1. **Update deployment**
   ```bash
   vim k8s/overlays/production/deployment.yaml
   # image: myregistry.azurecr.io/{app_name}:v1.2.3
   ```

2. **Commit and push**
   ```bash
   git commit -am "feat: update to v1.2.3"
   git push origin main
   ```

3. **ArgoCD syncs new image**
   ```bash
   # Rolling update happens automatically
   kubectl rollout status deployment/{app_name} -n {app_name}
   ```

## Manual Operations

### Force Sync
```bash
argocd app sync {app_name}
argocd app wait {app_name}
```

### Rollback
```bash
argocd app history {app_name}
argocd app rollback {app_name} 1  # Rollback to revision 1
```

### View Status
```bash
argocd app get {app_name}
argocd app get {app_name} --refresh
```

## Troubleshooting

### Sync Failed
```bash
# Check ArgoCD application status
kubectl describe application {app_name} -n argocd

# View sync status
argocd app get {app_name}

# Check logs
kubectl logs -f -l app.kubernetes.io/name=argocd-application-controller -n argocd
```

### Resource Drift
```bash
# ArgoCD automatically fixes drift (selfHeal: true)
# Or manually sync
argocd app sync {app_name}

# View differences
argocd app diff {app_name}
```

### Webhook Not Triggering
```bash
# Check webhook configuration
kubectl get secret github-webhook-secret -n argocd

# Manually refresh repo
argocd repo refresh https://github.com/user/repo

# Check last sync time
kubectl get application {app_name} -n argocd -o jsonpath='{{.status.lastSyncTime}}'
```

## Best Practices

1. **One repository per application** or **monorepo with Kustomize overlays**
2. **Use GitOps for everything** (infra, config, policy)
3. **Require pull requests** for all changes
4. **Implement code review** before merge
5. **Automate testing** in CI/CD pipeline
6. **Use semantic versioning** for releases
7. **Tag releases** in git
8. **Document** all changes in commit messages
9. **Monitor** deployment status and health
10. **Plan** for disaster recovery (external backups)

## Monitoring & Alerts

### Slack Notifications
- Sync success/failure
- Health check changes
- Manual syncs
- Resource errors

### Metrics
- Sync duration
- Application health
- Resource count
- Error rate

## Security

### RBAC
```bash
# Restrict ArgoCD access
kubectl apply -f rbac-project.yaml

# Service account per team
kubectl create serviceaccount {app_name}-deployer
kubectl create rolebinding {app_name}-deployer --clusterrole=edit --serviceaccount={app_name}:{app_name}-deployer
```

### Secret Management
```bash
# Use External Secrets Operator
# Never commit secrets to git
# Reference from AWS Secrets Manager / Vault
```

### Audit Logging
```bash
# All deployments logged in ArgoCD
# Git history shows all changes
# Kubernetes audit logs track API calls
```

## Support

- **Documentation**: https://argocd.io
- **Community**: https://github.com/argoproj/argo-cd/discussions
- **Issues**: https://github.com/argoproj/argo-cd/issues
"""


def generate_gitops_configs(framework: str, language: str, app_name: str = "app", repo_url: str = "https://github.com/user/repo") -> Dict[str, str]:
    """
    Generate GitOps infrastructure configurations.

    Args:
        framework: django, fastapi, spring
        language: python, javascript
        app_name: application name
        repo_url: Git repository URL

    Returns: dict of {filename: code_content}
    """
    generator = GitOpsGenerator(framework, language)
    output = {}

    output["gitops/argocd-application.yaml"] = generator.generate_argocd_application(app_name, repo_url)
    output["gitops/flux-configuration.yaml"] = generator.generate_flux_configuration(app_name, repo_url)
    output["gitops/deployment-waves.yaml"] = generator.generate_deployment_waves(app_name)
    output["gitops/gitops-workflow.md"] = generator.generate_gitops_workflow(app_name)

    return output
