"""
Monitoring Generator - Observability and metrics collection infrastructure

Generates:
- Prometheus scrape configurations
- Grafana dashboards
- AlertManager rules
- Logging configurations (ELK, Loki)
- Distributed tracing (Jaeger)
- Service mesh metrics (Istio, Linkerd)
"""

from typing import Dict, Any
import json


class MonitoringGenerator:
    """Generate monitoring and observability configurations"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_prometheus_config(self, app_name: str = "app") -> str:
        """Generate Prometheus configuration"""
        return f"""
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'production'
    env: 'prod'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

rule_files:
  - '/etc/prometheus/rules/*.yml'

scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Kubernetes API server
  - job_name: 'kubernetes-apiservers'
    kubernetes_sd_configs:
      - role: endpoints
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https

  # Kubernetes nodes
  - job_name: 'kubernetes-nodes'
    kubernetes_sd_configs:
      - role: node
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)

  # Kubernetes pods
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: 'true'
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\\d+)?;(\\d+)
        replacement: $1:$2
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: kubernetes_pod_name

  # Application metrics
  - job_name: '{app_name}-app'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: '{app_name}'
      - source_labels: [__meta_kubernetes_pod_container_port_number]
        action: keep
        regex: '8000|8001'
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod

  # Node Exporter
  - job_name: 'node-exporter'
    kubernetes_sd_configs:
      - role: node
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)

  # cAdvisor (container metrics)
  - job_name: 'cadvisor'
    kubernetes_sd_configs:
      - role: node
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - target_label: __metrics_path__
        replacement: /metrics/cadvisor
"""

    def generate_prometheus_rules(self, app_name: str = "app") -> str:
        """Generate Prometheus alerting rules"""
        return f"""
groups:
  - name: {app_name}-alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          (sum(rate(http_requests_total{{job="{app_name}-app", status=~"5.."}}[5m])) by (instance) /
           sum(rate(http_requests_total{{job="{app_name}-app"}}[5m])) by (instance)) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.instance }}"
          description: "Error rate is {{ $value | humanizePercentage }} for {{ $labels.instance }}"

      # High latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{job="{app_name}-app"}}[5m])) by (le, instance)) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High latency on {{ $labels.instance }}"
          description: "p95 latency is {{ $value }}s for {{ $labels.instance }}"

      # Pod restart
      - alert: PodRestartingTooOften
        expr: |
          rate(kube_pod_container_status_restarts_total{{pod=~"{app_name}-.*"}}[15m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pod {{ $labels.pod }} restarting too often"
          description: "Pod {{ $labels.pod }} has restarted {{ $value }} times in 15m"

      # Memory pressure
      - alert: MemoryPressure
        expr: |
          container_memory_usage_bytes{{pod=~"{app_name}-.*"}} / container_spec_memory_limit_bytes > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Memory pressure on {{ $labels.pod }}"
          description: "Memory usage is {{ $value | humanizePercentage }} of limit"

      # CPU throttling
      - alert: CPUThrottling
        expr: |
          rate(container_cpu_cfs_throttled_seconds_total{{pod=~"{app_name}-.*"}}[5m]) > 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CPU throttling on {{ $labels.pod }}"
          description: "CPU throttled {{ $value | humanizePercentage }} of time"

      # Database connection exhaustion
      - alert: DBConnectionExhaustion
        expr: |
          sum(pg_stat_activity_count) by (instance) / sum(max_conn) by (instance) > 0.8
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool exhaustion on {{ $labels.instance }}"
          description: "{{ $value | humanizePercentage }} of connections in use"

      # Redis memory pressure
      - alert: RedisMemoryPressure
        expr: |
          redis_memory_used_bytes / redis_memory_max_bytes > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis memory pressure"
          description: "Redis memory usage is {{ $value | humanizePercentage }} of max"
"""

    def generate_grafana_dashboard(self, app_name: str = "app") -> str:
        """Generate Grafana dashboard JSON"""
        dashboard = {
            "dashboard": {
                "title": f"{app_name} Overview",
                "tags": ["app", app_name],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Requests per second",
                        "targets": [
                            {
                                "expr": f'sum(rate(http_requests_total{{job="{app_name}-app"}}[5m]))',
                                "legendFormat": "RPS"
                            }
                        ],
                        "type": "graph"
                    },
                    {
                        "id": 2,
                        "title": "Error rate",
                        "targets": [
                            {
                                "expr": f'sum(rate(http_requests_total{{job="{app_name}-app", status=~"5.."}}[5m])) / sum(rate(http_requests_total{{job="{app_name}-app"}}[5m]))',
                                "legendFormat": "Error rate"
                            }
                        ],
                        "type": "graph"
                    },
                    {
                        "id": 3,
                        "title": "p95 Latency",
                        "targets": [
                            {
                                "expr": f'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{job="{app_name}-app"}}[5m])) by (le))',
                                "legendFormat": "p95"
                            }
                        ],
                        "type": "graph"
                    },
                    {
                        "id": 4,
                        "title": "Memory usage",
                        "targets": [
                            {
                                "expr": f'sum(container_memory_usage_bytes{{pod=~"{app_name}-.*"}}) by (pod)',
                                "legendFormat": "{{ pod }}"
                            }
                        ],
                        "type": "graph"
                    },
                    {
                        "id": 5,
                        "title": "CPU usage",
                        "targets": [
                            {
                                "expr": f'sum(rate(container_cpu_usage_seconds_total{{pod=~"{app_name}-.*"}}[5m])) by (pod)',
                                "legendFormat": "{{ pod }}"
                            }
                        ],
                        "type": "graph"
                    },
                    {
                        "id": 6,
                        "title": "Pod restarts",
                        "targets": [
                            {
                                "expr": f'sum(increase(kube_pod_container_status_restarts_total{{pod=~"{app_name}-.*"}}[1h])) by (pod)',
                                "legendFormat": "{{ pod }}"
                            }
                        ],
                        "type": "stat"
                    }
                ]
            }
        }
        return json.dumps(dashboard, indent=2)

    def generate_alertmanager_config(self, app_name: str = "app") -> str:
        """Generate AlertManager configuration"""
        return f"""
global:
  resolve_timeout: 5m
  slack_api_url: ${{SLACK_WEBHOOK_URL}}
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_auth_username: ${{SMTP_USERNAME}}
  smtp_auth_password: ${{SMTP_PASSWORD}}
  smtp_from: 'alerts@{app_name}.com'

route:
  receiver: 'default'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h

  routes:
    - match:
        severity: critical
      receiver: 'critical'
      continue: true
      repeat_interval: 1h

    - match:
        severity: warning
      receiver: 'warning'
      repeat_interval: 4h

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true

  - name: 'critical'
    slack_configs:
      - channel: '#critical-alerts'
        title: 'CRITICAL: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true
    email_configs:
      - to: 'ops-team@{app_name}.com'
        headers:
          Subject: 'CRITICAL ALERT: {{ .GroupLabels.alertname }}'

  - name: 'warning'
    slack_configs:
      - channel: '#warnings'
        title: '⚠️ {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
"""

    def generate_loki_config(self, app_name: str = "app") -> str:
        """Generate Loki logging configuration"""
        return f"""
auth_enabled: false

ingester:
  chunk_idle_period: 3m
  max_chunk_age: 1h
  max_streams_per_user: 10000
  chunk_retain_period: 1m

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

server:
  http_listen_port: 3100

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
"""

    def generate_fluent_bit_config(self, app_name: str = "app") -> str:
        """Generate Fluent Bit logging agent configuration"""
        return """
[SERVICE]
    Daemon off
    Flush 1
    Log_Level info
    Parsers_File parsers.conf

[INPUT]
    Name tail
    Path /var/log/containers/*{app_name}*.log
    Parser docker
    Tag kubernetes.*
    Refresh_Interval 5
    Mem_Buf_Limit 5MB
    Skip_Long_Lines On

[FILTER]
    Name kubernetes
    Match kubernetes.*
    Kube_URL https://kubernetes.default.svc:443
    Kube_CA_File /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    Kube_Token_File /var/run/secrets/kubernetes.io/serviceaccount/token
    Labels On

[OUTPUT]
    Name loki
    Match kubernetes.*
    Host loki
    Port 3100
    Labels job=kubernetes-cluster
    Auto_Metadata_Labels on
"""

    def generate_jaeger_config(self, app_name: str = "app") -> str:
        """Generate Jaeger distributed tracing configuration"""
        return f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: jaeger-configuration
  namespace: monitoring
data:
  sampling.json: |
    {{
      "default_strategy": {{
        "type": "probabilistic",
        "param": 0.1
      }},
      "service_strategies": [
        {{
          "service": "{app_name}",
          "type": "ratelimiting",
          "param": 100
        }}
      ]
    }}
"""


def generate_monitoring_configs(framework: str, language: str, app_name: str = "app") -> Dict[str, str]:
    """
    Generate monitoring and observability configurations.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = MonitoringGenerator(framework, language)
    output = {}

    output["prometheus/prometheus.yml"] = generator.generate_prometheus_config(app_name)
    output["prometheus/rules.yml"] = generator.generate_prometheus_rules(app_name)
    output["alertmanager/alertmanager.yml"] = generator.generate_alertmanager_config(app_name)
    output["grafana/dashboard.json"] = generator.generate_grafana_dashboard(app_name)
    output["loki/loki-config.yml"] = generator.generate_loki_config(app_name)
    output["fluent-bit/fluent-bit.conf"] = generator.generate_fluent_bit_config(app_name)
    output["jaeger/jaeger-config.yaml"] = generator.generate_jaeger_config(app_name)

    return output
