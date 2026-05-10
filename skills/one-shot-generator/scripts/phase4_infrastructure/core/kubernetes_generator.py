"""
Kubernetes Generator - K8s manifests for production deployment

Generates:
- Deployment manifests
- Service definitions
- ConfigMaps and Secrets
- Ingress configuration
- StatefulSets for databases
- Helm charts
"""

from typing import Dict, Any


class KubernetesGenerator:
    """Generate Kubernetes manifests"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_k8s_deployment(self, app_name: str = "app") -> str:
        """Generate Kubernetes Deployment manifest"""
        return f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  labels:
    app: {app_name}
    version: v1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      serviceAccountName: {app_name}
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000

      containers:
      - name: {app_name}
        image: myregistry.azurecr.io/{app_name}:latest
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP

        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DEBUG
          value: "false"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: {app_name}-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: {app_name}-config
              key: redis-url

        resources:
          requests:
            cpu: "250m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"

        livenessProbe:
          httpGet:
            path: /health/live
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /health/ready
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2

        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL

      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - {app_name}
              topologyKey: kubernetes.io/hostname

      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
"""

    def generate_k8s_service(self, app_name: str = "app") -> str:
        """Generate Kubernetes Service"""
        return f"""
apiVersion: v1
kind: Service
metadata:
  name: {app_name}
  labels:
    app: {app_name}
spec:
  type: LoadBalancer
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
  selector:
    app: {app_name}
---
apiVersion: v1
kind: Service
metadata:
  name: {app_name}-internal
  labels:
    app: {app_name}
spec:
  type: ClusterIP
  ports:
  - name: http
    port: 8000
    targetPort: 8000
    protocol: TCP
  selector:
    app: {app_name}
"""

    def generate_k8s_ingress(self, app_name: str = "app", domain: str = "example.com") -> str:
        """Generate Kubernetes Ingress"""
        return f"""
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {app_name}
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - {domain}
    secretName: {app_name}-tls
  rules:
  - host: {domain}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {app_name}
            port:
              name: http
"""

    def generate_k8s_configmap(self, app_name: str = "app") -> str:
        """Generate Kubernetes ConfigMap"""
        return f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-config
data:
  redis-url: "redis://redis-master:6379/0"
  log-level: "INFO"
  max-workers: "4"
  cache-ttl: "3600"
---
apiVersion: v1
kind: Secret
metadata:
  name: {app_name}-secrets
type: Opaque
stringData:
  database-url: "postgresql://user:password@postgres:5432/appdb"
  secret-key: "your-secret-key-here"
  api-key: "your-api-key-here"
"""

    def generate_k8s_hpa(self, app_name: str = "app") -> str:
        """Generate Horizontal Pod Autoscaler"""
        return f"""
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {app_name}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {app_name}
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
"""

    def generate_k8s_namespace(self, app_name: str = "app") -> str:
        """Generate Kubernetes Namespace with RBAC"""
        return f"""
apiVersion: v1
kind: Namespace
metadata:
  name: {app_name}
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {app_name}
  namespace: {app_name}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {app_name}
  namespace: {app_name}
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {app_name}
  namespace: {app_name}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {app_name}
subjects:
- kind: ServiceAccount
  name: {app_name}
  namespace: {app_name}
"""


def generate_kubernetes_manifests(framework: str, language: str, app_name: str = "app") -> Dict[str, str]:
    """
    Generate Kubernetes manifests.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = KubernetesGenerator(framework, language)
    output = {}

    output["k8s-namespace.yaml"] = generator.generate_k8s_namespace(app_name)
    output["k8s-deployment.yaml"] = generator.generate_k8s_deployment(app_name)
    output["k8s-service.yaml"] = generator.generate_k8s_service(app_name)
    output["k8s-ingress.yaml"] = generator.generate_k8s_ingress(app_name)
    output["k8s-configmap.yaml"] = generator.generate_k8s_configmap(app_name)
    output["k8s-hpa.yaml"] = generator.generate_k8s_hpa(app_name)

    return output
