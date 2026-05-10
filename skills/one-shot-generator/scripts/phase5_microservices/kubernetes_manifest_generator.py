#!/usr/bin/env python3
"""Kubernetes Manifest Generator - K8s Deployment Specs"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.base_script import setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class KubernetesManifestGenerator:
    """Generates Kubernetes deployment manifests."""

    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['k8s/deployment.yaml'] = self._deployment()
        files['k8s/service.yaml'] = self._service()
        files['k8s/ingress.yaml'] = self._ingress()
        files['k8s/configmap.yaml'] = self._configmap()
        files['k8s/secret.yaml'] = self._secret()
        files['k8s/hpa.yaml'] = self._hpa()
        files['k8s/README.md'] = self._readme()
        return files

    def _deployment(self) -> str:
        return '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  labels:
    app: api-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-service
  template:
    metadata:
      labels:
        app: api-service
    spec:
      containers:
      - name: api
        image: myregistry.azurecr.io/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: environment
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

    def _service(self) -> str:
        return '''apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  selector:
    app: api-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
'''

    def _ingress(self) -> str:
        return '''apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
'''

    def _configmap(self) -> str:
        return '''apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  environment: "production"
  log_level: "info"
  database_pool_size: "20"
'''

    def _secret(self) -> str:
        return '''apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
stringData:
  url: "postgresql://user:password@db.example.com:5432/mydb"
  username: "user"
  password: "password"
'''

    def _hpa(self) -> str:
        return '''apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
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

    def _readme(self) -> str:
        return '''# Kubernetes Manifests

## Deploy

```bash
kubectl apply -f k8s/
```

## Verify

```bash
kubectl get pods
kubectl describe pod api-service-xyz
kubectl logs api-service-xyz
```

## Scaling

```bash
# Manual
kubectl scale deployment api-service --replicas=5

# Automatic (HPA)
# Already configured in hpa.yaml
```
'''


def main():
    with timed_run("kubernetes_manifest_generator") as timer:
        logger.debug("Testing K8s Manifest generation")
        gen = KubernetesManifestGenerator("python")
        files = gen.generate()
        for filepath in files:
            print(f"  ✓ {filepath}")
        check_budget("kubernetes_manifest_generator", timer.elapsed_ms, logger)


if __name__ == '__main__':
    main()
