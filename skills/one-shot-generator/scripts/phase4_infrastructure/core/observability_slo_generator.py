"""
Observability SLO Generator - Service Level Objectives and Error Budget tracking

Generates:
- SLI (Service Level Indicator) definitions
- SLO (Service Level Objective) specifications
- Error budget calculations and alerts
- Burn rate monitoring
- Availability tracking
- Latency thresholds
"""

from typing import Dict, Any
import json


class ObservabilitySLOGenerator:
    """Generate SLO/SLI observability configurations"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_slo_definition(self, app_name: str = "app") -> str:
        """Generate comprehensive SLO definition"""
        return f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-slo-definition
  namespace: default
data:
  slo.yaml: |
    # Service Level Objectives for {app_name}

    service: {app_name}
    team: backend-team
    sloDurationDays: 30

    # Availability SLO
    availability:
      objective: 99.9  # 99.9% uptime (43.2 minutes downtime/month)
      indicator: request_success_rate
      measurement:
        - type: http
          successCriteria: "status_code < 500"
        - type: grpc
          successCriteria: "status != ERROR"
      alertThreshold: 99.5  # Alert at 99.5% (gives 8 hour buffer)
      description: "Requests complete without 5xx errors"

    # Latency SLO
    latency:
      objective: 99.0  # 99% of requests meet threshold
      threshold: 500ms  # p99 latency < 500ms
      measurement:
        - percentile: p50
          target: 100ms
        - percentile: p95
          target: 300ms
        - percentile: p99
          target: 500ms
      alertThreshold: 98.5
      description: "99% of requests complete within 500ms"

    # Error Rate SLO
    errorRate:
      objective: 99.9
      threshold: 0.1%  # Max 0.1% error rate
      errorTypes:
        - 4xx: excluded  # Client errors don't count against SLO
        - 5xx: included  # Server errors count
        - timeout: included
        - connection_refused: included
      measurement: "sum(rate(errors[5m])) / sum(rate(requests[5m]))"
      alertThreshold: 0.05%

    # Durability SLO
    durability:
      objective: 99.99
      indicator: data_loss
      measurement: "count(successful_backups) / count(scheduled_backups)"
      description: "Backups complete successfully >= 99.99% of time"

    # Error Budget
    errorBudget:
      month: 43.2  # minutes (100% - 99.9%)
      week: 10.08  # minutes
      day: 1.44   # minutes
      hour: 0.036  # minutes (2.16 seconds)

    # Burn Rate Thresholds
    burnRate:
      fast:
        duration: 5m
        threshold: 10  # Burning at 10x rate
        action: page
      slow:
        duration: 30m
        threshold: 3  # Burning at 3x rate
        action: alert
      creeping:
        duration: 1h
        threshold: 1.2  # Burning at 1.2x rate
        action: log

    # Exceptions (don't count against SLO)
    exceptions:
      - description: "Planned maintenance"
        schedule: "Sun 02:00-03:00 UTC"
        frequency: weekly
      - description: "Third-party API outages"
        condition: "external_service_unavailable"
      - description: "Network issues"
        condition: "client_side_error"

    # Tracking and Reporting
    reporting:
      cadence: weekly
      recipients:
        - backend-team@company.com
        - management@company.com
      metrics:
        - uptime percentage
        - error budget remaining
        - burn rate
        - incidents in period

    # Escalation
    escalation:
      - burnRateExceeds: 10x
        duration: 5m
        action: "Page on-call engineer"
      - burnRateExceeds: 3x
        duration: 30m
        action: "Alert team lead"
      - errorBudgetRemaining: 10%
        action: "Weekly planning to reduce risk"
"""

    def generate_sli_metrics_rules(self, app_name: str = "app") -> str:
        """Generate Prometheus rules for SLI metrics"""
        return f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-sli-rules
  namespace: monitoring
data:
  sli-rules.yml: |
    groups:
      - name: {app_name}-sli
        interval: 30s
        rules:
          # Request Success Rate (Availability)
          - record: {app_name}:request_success_rate:5m
            expr: |
              sum(rate(http_requests_total{{job="{app_name}", status!~"5.."}}[5m]))
              /
              sum(rate(http_requests_total{{job="{app_name}"}}[5m]))

          - record: {app_name}:request_success_rate:30m
            expr: |
              sum(rate(http_requests_total{{job="{app_name}", status!~"5.."}}[30m]))
              /
              sum(rate(http_requests_total{{job="{app_name}"}}[30m]))

          # Latency Percentiles
          - record: {app_name}:latency_p50:5m
            expr: |
              histogram_quantile(0.50,
                sum(rate(http_request_duration_seconds_bucket{{job="{app_name}"}}[5m])) by (le)
              )

          - record: {app_name}:latency_p95:5m
            expr: |
              histogram_quantile(0.95,
                sum(rate(http_request_duration_seconds_bucket{{job="{app_name}"}}[5m])) by (le)
              )

          - record: {app_name}:latency_p99:5m
            expr: |
              histogram_quantile(0.99,
                sum(rate(http_request_duration_seconds_bucket{{job="{app_name}"}}[5m])) by (le)
              )

          # Requests Meeting Latency SLO
          - record: {app_name}:latency_slo_compliance:5m
            expr: |
              sum(rate(http_request_duration_seconds_bucket{{job="{app_name}", le="0.5"}}[5m]))
              /
              sum(rate(http_requests_total{{job="{app_name}"}}[5m]))

          # Error Rate
          - record: {app_name}:error_rate:5m
            expr: |
              sum(rate(http_requests_total{{job="{app_name}", status=~"5.."}}[5m]))
              /
              sum(rate(http_requests_total{{job="{app_name}"}}[5m]))

          # Database Query Success Rate
          - record: {app_name}:db_query_success_rate:5m
            expr: |
              sum(rate(db_query_duration_seconds_count{{job="{app_name}", result="success"}}[5m]))
              /
              sum(rate(db_query_duration_seconds_count{{job="{app_name}"}}[5m]))

          # Cache Hit Rate
          - record: {app_name}:cache_hit_rate:5m
            expr: |
              sum(rate(cache_hits_total{{job="{app_name}"}}[5m]))
              /
              sum(rate(cache_requests_total{{job="{app_name}"}}[5m]))

          # Availability (uptime)
          - record: {app_name}:availability:5m
            expr: |
              count(up{{job="{app_name}"}} == 1)
              /
              count(up{{job="{app_name}"}})
"""

    def generate_burn_rate_alerts(self, app_name: str = "app") -> str:
        """Generate burn rate alerting rules"""
        return f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-burn-rate-alerts
  namespace: monitoring
data:
  burn-rate-rules.yml: |
    groups:
      - name: {app_name}-burn-rate-alerts
        interval: 1m
        rules:
          # SLO: 99.9% availability (0.1% error budget)
          # Burn rate 10x = 1% errors in 5 minutes
          - alert: SLOBurnRate10x
            expr: |
              (1 - {app_name}:request_success_rate:5m) > 0.01
            for: 5m
            labels:
              severity: critical
              slo: availability
            annotations:
              summary: "{{ $labels.job }} SLO burn rate 10x"
              description: "Request success rate {{ $value | humanizePercentage }} (target 99.9%)"

          # SLO burn rate 3x
          - alert: SLOBurnRate3x
            expr: |
              (1 - {app_name}:request_success_rate:30m) > 0.003
            for: 30m
            labels:
              severity: warning
              slo: availability
            annotations:
              summary: "{{ $labels.job }} SLO burn rate 3x"
              description: "Request success rate {{ $value | humanizePercentage }}"

          # Latency SLO breach (p99 > 500ms)
          - alert: LatencySLOBreach
            expr: |
              {app_name}:latency_p99:5m > 0.5
            for: 5m
            labels:
              severity: warning
              slo: latency
            annotations:
              summary: "{{ $labels.job }} latency SLO breached"
              description: "p99 latency {{ $value }}s (target 0.5s)"

          # Error Budget Exhaustion
          - alert: ErrorBudgetLow
            expr: |
              1 - {app_name}:request_success_rate:5m > 0.001
            for: 10m
            labels:
              severity: critical
              slo: error-budget
            annotations:
              summary: "{{ $labels.job }} error budget critical"
              description: "Error rate {{ $value | humanizePercentage }} is unsustainable"
"""

    def generate_error_budget_tracking(self, app_name: str = "app") -> str:
        """Generate error budget tracking configuration"""
        return f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-error-budget
  namespace: monitoring
data:
  error-budget.yaml: |
    # Error Budget Tracking for {app_name}

    # SLO: 99.9% availability
    # Monthly error budget: 0.1% = 43.2 minutes

    tracking:
      period: monthly
      startDate: "2026-05-01"
      sloPercentage: 99.9

    errorBudget:
      monthly:
        total: 43.2  # minutes
        consumed: 5.0  # minutes
        remaining: 38.2  # minutes
        percentageRemaining: 88.4%
        burnRate: 0.17  # minutes per day

      weekly:
        total: 10.08
        consumed: 1.2
        remaining: 8.88
        percentageRemaining: 88.1%

      daily:
        total: 1.44
        consumed: 0.17
        remaining: 1.27
        percentageRemaining: 88.2%

    incidents:
      - date: "2026-05-02"
        duration: "2 minutes"
        cause: "Database connection pool exhaustion"
        cost: 2.0  # minutes of error budget
        preventive: "Increased pool size"

      - date: "2026-05-05"
        duration: "3 minutes"
        cause: "Memory leak in deployment"
        cost: 3.0
        preventive: "Fixed leak, deployed v1.2.1"

    riskAssessment:
      currentBurnRate: 0.17  # minutes per day
      projectedMonthlyBudget: 43.2
      projectedMonthlyConsumption: 5.1  # at current rate
      riskLevel: "low"
      daysToExhaustion: "254"

    recommendations:
      - action: "Continue current SLO target"
        rationale: "Error budget consumption is sustainable"
      - action: "Review database tuning"
        rationale: "Latest incident was database-related"
      - action: "Schedule capacity planning"
        rationale: "Traffic growth may impact SLO"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-error-budget-prometheus
  namespace: monitoring
data:
  error-budget-rules.yml: |
    groups:
      - name: {app_name}-error-budget
        interval: 5m
        rules:
          # Monthly error budget consumed
          - record: {app_name}:error_budget_consumed_monthly
            expr: |
              (1 - avg_over_time({app_name}:request_success_rate:5m[30d])) * 43.2

          # Error budget burn rate (minutes per day)
          - record: {app_name}:error_budget_burn_rate
            expr: |
              (1 - avg_over_time({app_name}:request_success_rate:5m[7d])) * 1.44 * 30

          # Days until error budget exhaustion
          - record: {app_name}:error_budget_days_remaining
            expr: |
              (43.2 - {app_name}:error_budget_consumed_monthly) / {app_name}:error_budget_burn_rate

          # Error budget consumption percentage
          - record: {app_name}:error_budget_percentage
            expr: |
              ({app_name}:error_budget_consumed_monthly / 43.2) * 100
"""

    def generate_slo_dashboard(self, app_name: str = "app") -> str:
        """Generate SLO monitoring Grafana dashboard"""
        dashboard = {
            "dashboard": {
                "title": f"{app_name} SLO Dashboard",
                "tags": ["slo", "sli", app_name],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Availability (SLO: 99.9%)",
                        "targets": [
                            {
                                "expr": f"100 * {app_name}:request_success_rate:5m",
                                "legendFormat": "Availability %"
                            }
                        ],
                        "thresholds": [99.9],
                        "type": "stat"
                    },
                    {
                        "id": 2,
                        "title": "Latency p99 (Target: 500ms)",
                        "targets": [
                            {
                                "expr": f"{app_name}:latency_p99:5m",
                                "legendFormat": "p99 Latency"
                            }
                        ],
                        "type": "graph"
                    },
                    {
                        "id": 3,
                        "title": "Error Budget Remaining",
                        "targets": [
                            {
                                "expr": f"(43.2 - {app_name}:error_budget_consumed_monthly)",
                                "legendFormat": "Minutes"
                            }
                        ],
                        "type": "gauge"
                    },
                    {
                        "id": 4,
                        "title": "Burn Rate (minutes/day)",
                        "targets": [
                            {
                                "expr": f"{app_name}:error_budget_burn_rate",
                                "legendFormat": "Burn Rate"
                            }
                        ],
                        "type": "graph"
                    },
                    {
                        "id": 5,
                        "title": "Request Success Rate (5m, 30m, 1h)",
                        "targets": [
                            {
                                "expr": f"100 * {app_name}:request_success_rate:5m",
                                "legendFormat": "5m"
                            },
                            {
                                "expr": f"100 * {app_name}:request_success_rate:30m",
                                "legendFormat": "30m"
                            }
                        ],
                        "type": "graph"
                    },
                    {
                        "id": 6,
                        "title": "Days Until Budget Exhaustion",
                        "targets": [
                            {
                                "expr": f"{app_name}:error_budget_days_remaining",
                                "legendFormat": "Days"
                            }
                        ],
                        "type": "stat"
                    }
                ]
            }
        }
        return json.dumps(dashboard, indent=2)


def generate_observability_slo_configs(framework: str, language: str, app_name: str = "app") -> Dict[str, str]:
    """
    Generate SLO/SLI observability configurations.

    Args:
        framework: django, fastapi, spring
        language: python, javascript
        app_name: application name

    Returns: dict of {filename: code_content}
    """
    generator = ObservabilitySLOGenerator(framework, language)
    output = {}

    output["observability/slo-definition.yaml"] = generator.generate_slo_definition(app_name)
    output["observability/sli-metrics-rules.yaml"] = generator.generate_sli_metrics_rules(app_name)
    output["observability/burn-rate-alerts.yaml"] = generator.generate_burn_rate_alerts(app_name)
    output["observability/error-budget-tracking.yaml"] = generator.generate_error_budget_tracking(app_name)
    output["observability/slo-dashboard.json"] = generator.generate_slo_dashboard(app_name)

    return output
