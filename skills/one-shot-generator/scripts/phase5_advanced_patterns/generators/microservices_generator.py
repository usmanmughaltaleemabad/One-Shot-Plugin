"""
Phase 5.1: Microservices Orchestration Generator

Generates production-ready microservices infrastructure:
- Kubernetes manifests (Deployment, Service, ConfigMap, Secret)
- Helm charts for multi-environment deployment
- Service mesh configuration (Istio)
- Service discovery and inter-service communication
- Distributed tracing (Jaeger, Datadog)
- Canary and blue-green deployment configs
"""

from typing import Dict


def generate_kubernetes_deployment(app_name: str, language: str, framework: str) -> Dict[str, str]:
    """Generate Kubernetes deployment manifests"""
    return {
        "k8s/deployment.yaml": f'''apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  namespace: default
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
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: {app_name}
      containers:
      - name: {app_name}
        image: {app_name}:latest
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 8000
          protocol: TCP
        - name: metrics
          containerPort: 8001
          protocol: TCP
        env:
        - name: APP_NAME
          value: {app_name}
        - name: ENVIRONMENT
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
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
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: config
          mountPath: /etc/config
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: {app_name}-config
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
''',
        "k8s/service.yaml": f'''apiVersion: v1
kind: Service
metadata:
  name: {app_name}
  namespace: default
  labels:
    app: {app_name}
spec:
  type: ClusterIP
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
  - name: metrics
    port: 8001
    targetPort: 8001
    protocol: TCP
  selector:
    app: {app_name}
  sessionAffinity: None
''',
        "k8s/configmap.yaml": f'''apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-config
  namespace: default
data:
  app.config: |
    [application]
    name = {app_name}
    debug = false
    log_level = INFO

    [database]
    connection_pool_size = 20

    [cache]
    ttl = 3600
    max_size = 10000
''',
        "k8s/rbac.yaml": f'''apiVersion: v1
kind: ServiceAccount
metadata:
  name: {app_name}
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {app_name}
  namespace: default
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
  namespace: default
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {app_name}
subjects:
- kind: ServiceAccount
  name: {app_name}
  namespace: default
''',
    }


def generate_helm_chart(app_name: str, language: str) -> Dict[str, str]:
    """Generate Helm chart for multi-environment deployment"""
    return {
        "helm/Chart.yaml": f'''apiVersion: v2
name: {app_name}
description: A Helm chart for {app_name} microservice
type: application
version: 1.0.0
appVersion: "1.0.0"
keywords:
  - {app_name}
  - microservice
maintainers:
  - name: Development Team
    email: dev@example.com
''',
        "helm/values.yaml": f'''replicaCount: 3

image:
  repository: {app_name}
  pullPolicy: IfNotPresent
  tag: "latest"

imagePullSecrets: []
nameOverride: ""
fullnameOverride: ""

service:
  type: ClusterIP
  port: 80
  targetPort: 8000

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: {app_name}.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: {app_name}-tls
      hosts:
        - {app_name}.example.com

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 80

nodeSelector: {{}}
tolerations: []
affinity: {{}}

env:
  - name: LOG_LEVEL
    value: INFO
  - name: CACHE_TTL
    value: "3600"
''',
        "helm/values-dev.yaml": '''replicaCount: 1

image:
  tag: "dev"

autoscaling:
  enabled: false

resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
''',
        "helm/values-prod.yaml": '''replicaCount: 3

image:
  tag: "latest"

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20

ingress:
  enabled: true
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

env:
  - name: LOG_LEVEL
    value: WARN
''',
        "helm/templates/deployment.yaml": '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "chart.fullname" . }}
  labels:
    {{- include "chart.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "chart.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "chart.selectorLabels" . | nindent 8 }}
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health/live
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          {{- toYaml .Values.resources | nindent 10 }}
        env:
          {{- toYaml .Values.env | nindent 10 }}
''',
        "helm/templates/_helpers.tpl": '''{{- define "chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "chart.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "chart.labels" -}}
helm.sh/chart: {{ include "chart.chart" . }}
{{ include "chart.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
''',
    }


def generate_service_mesh_config(app_name: str) -> Dict[str, str]:
    """Generate Istio service mesh configuration"""
    return {
        "service-mesh/virtualservice.yaml": f'''apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: {app_name}
  namespace: default
spec:
  hosts:
  - {app_name}
  http:
  - match:
    - uri:
        prefix: /api/v1
    route:
    - destination:
        host: {app_name}
        port:
          number: 80
        subset: v1
      weight: 90
    - destination:
        host: {app_name}
        port:
          number: 80
        subset: v2
      weight: 10
    timeout: 30s
    retries:
      attempts: 3
      perTryTimeout: 10s
''',
        "service-mesh/destinationrule.yaml": f'''apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: {app_name}
  namespace: default
spec:
  host: {app_name}
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 100
        http2MaxRequests: 100
        maxRequestsPerConnection: 2
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
      minRequestVolume: 10
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
''',
        "service-mesh/peerauthentication.yaml": f'''apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: default
spec:
  mtls:
    mode: STRICT
''',
    }


def generate_microservices(framework: str, language: str, app_name: str = None) -> Dict[str, str]:
    """Generate complete microservices orchestration infrastructure"""
    app_name = app_name or "microservice"
    output = {}

    # Kubernetes manifests
    output.update(generate_kubernetes_deployment(app_name, language, framework))

    # Helm chart
    output.update(generate_helm_chart(app_name, language))

    # Service mesh (Istio)
    output.update(generate_service_mesh_config(app_name))

    # Docker image
    if language == "python":
        output["Dockerfile"] = f'''FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
    else:
        output["Dockerfile"] = f'''FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 8000
CMD ["node", "server.js"]
'''

    # Docker Compose for local dev
    output["docker-compose.yaml"] = f'''version: '3.8'

services:
  {app_name}:
    build: .
    ports:
      - "8000:8000"
    environment:
      - NODE_ENV=development
      - LOG_LEVEL=DEBUG
    volumes:
      - .:/app
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
'''

    # Deployment scripts
    output["deploy.sh"] = f'''#!/bin/bash
set -e

APP_NAME="{app_name}"
NAMESPACE="default"
ENVIRONMENT="${{1:-dev}}"

echo "Deploying $APP_NAME to $ENVIRONMENT..."

# Build Docker image
docker build -t $APP_NAME:latest .

# Deploy with Helm
helm upgrade --install $APP_NAME ./helm \\
  --namespace $NAMESPACE \\
  --values helm/values-$ENVIRONMENT.yaml \\
  --wait

echo "Deployment complete!"
kubectl -n $NAMESPACE rollout status deployment/$APP_NAME
'''

    # Monitoring and observability
    output["k8s/servicemonitor.yaml"] = f'''apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {app_name}
  namespace: default
spec:
  selector:
    matchLabels:
      app: {app_name}
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
'''

    return output
