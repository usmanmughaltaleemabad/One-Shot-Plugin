"""
Cost Optimization Generator - Infrastructure cost management and optimization

Generates:
- Kubecost configurations
- Spot instance integration
- Resource optimization policies
- Cost allocation and chargeback
- Commitment discounts (reserved instances, savings plans)
- Cost monitoring and alerting
"""

from typing import Dict, Any
import json


class CostOptimizationGenerator:
    """Generate cost optimization configurations"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_kubecost_values(self, app_name: str = "app") -> str:
        """Generate Kubecost Helm values for cost tracking"""
        return """
# Kubecost Helm Chart Values for cost visibility and optimization

kubecostModel:
  warmCache: true
  warmSavingsCache: true
  maxQueryConcurrency: 5

ingress:
  enabled: true
  ingressClassName: nginx
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/auth-type: basic
    nginx.ingress.kubernetes.io/auth-secret: kubecost-auth
  hosts:
    - host: kubecost.example.com
      paths:
        - path: /
          pathType: Prefix

prometheus:
  server:
    enabled: false
  alertmanager:
    enabled: false

# Kubecost service configuration
service:
  type: LoadBalancer
  port: 9090

# Enable cost allocation by labels
kubecostModel:
  warmCache: true
  etl: true
  warmSavingsCache: true
  savings:
    spotCheckHour: 1

# Multi-cluster support
kubecostModel:
  promClusterIDLabel: cluster_id
  warmCache: true

# Slack/email notifications for cost anomalies
notifications:
  slack:
    enabled: true
    webhookUrl: "${SLACK_WEBHOOK_URL}"
  email:
    enabled: true
    recipients:
      - billing@company.com

# Budget alerts
budgets:
  - name: monthly-limit
    amount: 5000
    period: monthly
    alerts:
      - threshold: 80
        action: slack
      - threshold: 100
        action: slack,email

# Custom pricing
customPricing:
  enabled: true
  provider: aws
"""

    def generate_spot_instance_config(self, app_name: str = "app") -> str:
        """Generate spot instance and nodepool configuration"""
        return f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-cost-config
  namespace: default
data:
  spot-strategy.yaml: |
    # Spot instance strategy for cost optimization

    spotInstances:
      enabled: true
      maxPrice: "70%"  # Max 70% of on-demand price
      interruptionBehavior: terminate
      validUntil: "2027-05-09T00:00:00Z"

    nodePool:
      - name: on-demand-general
        instanceType: t3.medium
        capacity: 10
        strategy: on-demand
        labels:
          pool: on-demand
          cost-tier: regular
        taints:
          - key: cost-tier
            value: regular
            effect: NoSchedule

      - name: spot-general
        instanceType:
          - t3.medium
          - t3.large
          - t2.medium
          - t2.large
        capacity: 20
        strategy: spot
        labels:
          pool: spot
          cost-tier: spot
        taints:
          - key: cost-tier
            value: spot
            effect: NoSchedule

      - name: reserved-compute
        instanceType: c5.xlarge
        capacity: 5
        strategy: reserved
        reservationId: "reservation-123"
        labels:
          pool: reserved
          cost-tier: committed

    scheduling:
      # Prefer spot instances for non-critical workloads
      - workload: batch-jobs
        preferredPool: spot-general
        fallback: on-demand-general

      - workload: production-api
        preferredPool: on-demand-general
        fallback: reserved-compute

      - workload: cache
        preferredPool: spot-general
        fallback: on-demand-general

    # Cost limits and alerts
    costLimits:
      monthlyBudget: 5000
      dailyBudget: 166
      alertThreshold: 80  # Alert at 80% of budget

    # Rightsizing recommendations
    rightsizing:
      enabled: true
      checkInterval: daily
      thresholds:
        cpuUtilization: 20  # Alert if avg CPU < 20%
        memoryUtilization: 30  # Alert if avg memory < 30%
        networkUtilization: 10  # Alert if network < 10%
---
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: {app_name}-spot
spec:
  template:
    metadata:
      labels:
        pool: spot
        cost-tier: spot
    spec:
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot"]
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
        - key: node.kubernetes.io/instance-type
          operator: In
          values: ["t3.medium", "t3.large", "t2.medium"]
        - key: karpenter.sh/weighted-priority
          operator: In
          values: ["100"]
      providerRef:
        name: {app_name}-spot-provider
      taints:
        - key: cost-tier
          value: spot
          effect: NoSchedule
  limits:
    cpu: "1000"
    memory: 1000Gi
  consolidationPolicy:
    nodes: "Never"
  ttlSecondsAfterEmpty: 30
---
apiVersion: karpenter.sh/v1beta1
kind: EC2NodeClass
metadata:
  name: {app_name}-spot-provider
spec:
  amiFamily: AL2
  role: "KarpenterNodeRole"
  subnetSelector:
    karpenter.sh/discovery: "{app_name}"
  securityGroupSelector:
    karpenter.sh/discovery: "{app_name}"
  tags:
    ManagedBy: karpenter
    CostCenter: {app_name}
  metadataOptions:
    httpEndpoint: enabled
    httpProtocolIPv6: disabled
    httpPutResponseHopLimit: 2
  monitoring:
    enabled: true
---
apiVersion: v1
kind: PodDisruptionBudget
metadata:
  name: {app_name}-pdb
  namespace: {app_name}
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: {app_name}
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {app_name}-batch-pdb
  namespace: {app_name}
spec:
  maxUnavailable: 50%
  selector:
    matchLabels:
      app: {app_name}
      component: batch-job
"""

    def generate_cost_monitoring_dashboard(self, app_name: str = "app") -> str:
        """Generate cost monitoring Grafana dashboard"""
        dashboard = {
            "dashboard": {
                "title": f"{app_name} Cost Dashboard",
                "tags": ["cost", "kubecost", app_name],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Monthly Cost Trend",
                        "targets": [
                            {
                                "expr": "kubecost_cumulative_cloud_spend_total",
                                "legendFormat": "Total Cost"
                            }
                        ],
                        "type": "graph"
                    },
                    {
                        "id": 2,
                        "title": "Cost by Namespace",
                        "targets": [
                            {
                                "expr": "kubecost_namespace_monthly_cost",
                                "legendFormat": "{{ namespace }}"
                            }
                        ],
                        "type": "piechart"
                    },
                    {
                        "id": 3,
                        "title": "Cost by Pod",
                        "targets": [
                            {
                                "expr": f"kubecost_pod_monthly_cost{{namespace=\"{app_name}\"}}",
                                "legendFormat": "{{ pod }}"
                            }
                        ],
                        "type": "table"
                    },
                    {
                        "id": 4,
                        "title": "On-Demand vs Spot",
                        "targets": [
                            {
                                "expr": "kubecost_node_hourly_cost{node_type='on-demand'}",
                                "legendFormat": "On-Demand"
                            },
                            {
                                "expr": "kubecost_node_hourly_cost{node_type='spot'}",
                                "legendFormat": "Spot"
                            }
                        ],
                        "type": "graph"
                    },
                    {
                        "id": 5,
                        "title": "Compute vs Storage vs Network",
                        "targets": [
                            {
                                "expr": "kubecost_compute_cost",
                                "legendFormat": "Compute"
                            },
                            {
                                "expr": "kubecost_storage_cost",
                                "legendFormat": "Storage"
                            },
                            {
                                "expr": "kubecost_network_cost",
                                "legendFormat": "Network"
                            }
                        ],
                        "type": "bargauge"
                    },
                    {
                        "id": 6,
                        "title": "Savings Opportunities",
                        "targets": [
                            {
                                "expr": "kubecost_savings_opportunity_cost",
                                "legendFormat": "{{ category }}"
                            }
                        ],
                        "type": "stat"
                    }
                ]
            }
        }
        return json.dumps(dashboard, indent=2)

    def generate_cost_allocation_rules(self, app_name: str = "app") -> str:
        """Generate cost allocation and chargeback rules"""
        return f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-cost-allocation
  namespace: default
data:
  cost-allocation.yaml: |
    # Cost allocation and chargeback model

    allocationRules:
      # Label-based allocation
      - name: by-team
        label: cost-center
        default: unallocated
        values:
          backend: backend-team
          frontend: frontend-team
          ml: ml-team

      - name: by-environment
        label: environment
        default: development
        values:
          prod: production
          staging: staging
          dev: development

      - name: by-customer
        label: customer-id
        default: internal

    # Namespace allocation
    namespaceAllocation:
      {app_name}:
        team: backend-team
        cost-center: engineering
        environment: production

      monitoring:
        team: devops
        cost-center: infrastructure
        environment: production

      security:
        team: security
        cost-center: security
        environment: production

    # Resource type allocation
    resourceAllocation:
      # Pod resources
      pods:
        allocation: proportional
        metric: cpu-request

      # Storage
      pvc:
        allocation: direct
        metric: size

      # Network
      loadbalancer:
        allocation: direct
        metric: count

    # Chargeback rates
    chargebackRates:
      compute:
        cpu: 0.05  # $ per CPU-hour
        memory: 0.01  # $ per GB-hour
      storage:
        ssd: 0.10  # $ per GB-month
        standard: 0.05  # $ per GB-month
      network:
        ingress: 0.02  # $ per GB
        egress: 0.05  # $ per GB

    # Cost sharing (shared resources)
    costSharing:
      # Shared ingress controller
      ingress:
        allocated: false
        shared: true
        distributionMethod: proportional-to-traffic

      # Shared monitoring
      monitoring:
        allocated: false
        shared: true
        distributionMethod: equal-split

      # Shared DNS
      dns:
        allocated: false
        shared: true
        distributionMethod: equal-split

    # Discount rules
    discounts:
      reservedInstances:
        enabled: true
        coverage: 0.3  # 30% of capacity
        savings: 0.40  # 40% off on-demand

      savingsPlans:
        enabled: true
        commitment: 1-year
        savings: 0.35  # 35% off on-demand

      spotInstances:
        enabled: true
        savings: 0.70  # 70% off on-demand
"""

    def generate_cost_optimization_policies(self, app_name: str = "app") -> str:
        """Generate cost optimization policies and recommendations"""
        return f"""
apiVersion: constraints.kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: {app_name}-cost-limits
spec:
  validationFailureAction: audit
  rules:
    # Enforce resource requests
    - name: require-resource-requests
      match:
        resources:
          kinds:
            - Pod
      validate:
        message: "CPU and memory requests are required"
        pattern:
          spec:
            containers:
              - resources:
                  requests:
                    cpu: "?*"
                    memory: "?*"

    # Enforce resource limits
    - name: require-resource-limits
      match:
        resources:
          kinds:
            - Pod
      validate:
        message: "CPU and memory limits are required"
        pattern:
          spec:
            containers:
              - resources:
                  limits:
                    cpu: "?*"
                    memory: "?*"

    # Prefer local storage for ephemeral data
    - name: discourage-pvc-for-temp
      match:
        resources:
          kinds:
            - Pod
      validate:
        message: "Ephemeral data should use emptyDir, not PVC"
        pattern:
          spec:
            volumes:
              - name: "temp-*"
                emptyDir: {}

    # Cost center labeling
    - name: require-cost-labels
      match:
        resources:
          kinds:
            - Deployment
            - StatefulSet
      validate:
        message: "Cost center labels are required"
        pattern:
          metadata:
            labels:
              cost-center: "?*"
              team: "?*"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {app_name}-optimization-recommendations
  namespace: default
data:
  recommendations.yaml: |
    # Cost optimization recommendations

    rightsizing:
      - resource: pod-memory
        pattern: "pods with <20% avg memory utilization"
        recommendation: "Reduce memory request/limit by 50%"
        savings: "15-25%"
        effort: "Low"
        risk: "Low"

      - resource: pod-cpu
        pattern: "pods with <10% avg CPU utilization"
        recommendation: "Consolidate onto smaller instance types"
        savings: "20-30%"
        effort: "Medium"
        risk: "Medium"

      - resource: node-utilization
        pattern: "nodes with <30% utilization"
        recommendation: "Use Karpenter to consolidate"
        savings: "30-40%"
        effort: "High"
        risk: "Medium"

    commitmentDiscounts:
      - type: reserved-instances
        savings: "40%"
        commitment: 1-year
        currentCoverage: "30%"
        targetCoverage: "50%"
        recommendation: "Increase RI purchase"

      - type: savings-plans
        savings: "35%"
        commitment: 1-year
        currentCoverage: "0%"
        targetCoverage: "20%"
        recommendation: "Consider savings plans"

    spotInstances:
      - workload: batch-jobs
        currentMethod: on-demand
        recommendation: "Use spot instances"
        savings: "70%"
        effort: "Low"
        risk: "Low"

      - workload: dev-environments
        currentMethod: on-demand
        recommendation: "Schedule only during business hours"
        savings: "50%"
        effort: "Medium"
        risk: "Low"

    dataTransfer:
      - pattern: "Large egress to internet"
        recommendation: "Use CloudFront or edge caching"
        savings: "50-70%"
        effort: "Medium"

      - pattern: "Cross-region data transfer"
        recommendation: "Consider VPC endpoints"
        savings: "85%"
        effort: "High"

    storage:
      - pattern: "Cold data in standard storage"
        recommendation: "Archive to S3 Glacier"
        savings: "80%"
        effort: "Medium"

      - pattern: "Large PVC with low utilization"
        recommendation: "Right-size volumes"
        savings: "20-40%"
        effort: "Low"
"""


def generate_cost_optimization_configs(framework: str, language: str, app_name: str = "app") -> Dict[str, str]:
    """
    Generate cost optimization configurations.

    Args:
        framework: django, fastapi, spring
        language: python, javascript
        app_name: application name

    Returns: dict of {filename: code_content}
    """
    generator = CostOptimizationGenerator(framework, language)
    output = {}

    output["cost-optimization/kubecost-values.yaml"] = generator.generate_kubecost_values(app_name)
    output["cost-optimization/spot-instance-config.yaml"] = generator.generate_spot_instance_config(app_name)
    output["cost-optimization/cost-dashboard.json"] = generator.generate_cost_monitoring_dashboard(app_name)
    output["cost-optimization/cost-allocation.yaml"] = generator.generate_cost_allocation_rules(app_name)
    output["cost-optimization/cost-policies.yaml"] = generator.generate_cost_optimization_policies(app_name)

    return output
