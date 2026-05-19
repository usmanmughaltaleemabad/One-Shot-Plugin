#!/usr/bin/env python3
"""
Phase 5 FinOps: Cost Optimization

Cloud bills growing? Here's why:
- Unused servers (forgot to terminate)
- Over-provisioned (allocated 100GB, using 10GB)
- Inefficient queries (N+1 database queries)
- Inefficient storage (old data never deleted)

Cost optimization:
- Right-size: use smallest instance that works
- Reserved instances: commit for 1 year = 40% discount
- Spot instances: unused capacity = 90% discount
- Cleanup: delete unused resources
- Monitor: track spend per service

Example:
- EC2: $10,000/month → optimize → $3,000/month (-70%)
"""

from typing import Dict, List, Optional
from datetime import datetime


def generate_cost_tracker() -> str:
    """Generate cost tracking system."""

    tracker = '''
class CostTracker:
    """
    Track and optimize cloud costs.

    Cost centers:
    - Compute (EC2, Lambda)
    - Storage (S3, EBS)
    - Network (bandwidth, data transfer)
    - Database (RDS, DynamoDB)
    - Services (CloudFront, SQS)
    """

    def __init__(self):
        self._costs = {}  # resource_id → cost_per_month
        self._trends = []  # monthly trends

    def track_resource(
        self,
        resource_id: str,
        resource_type: str,  # ec2, s3, rds
        monthly_cost: float
    ) -> None:
        """Track resource cost"""
        self._costs[resource_id] = {
            "type": resource_type,
            "cost": monthly_cost,
            "tracked_at": datetime.utcnow().isoformat()
        }

    def get_total_monthly_cost(self) -> float:
        """Calculate total monthly cost"""
        return sum(r["cost"] for r in self._costs.values())

    def get_cost_by_type(self) -> Dict[str, float]:
        """Cost breakdown by resource type"""
        costs = {}

        for resource in self._costs.values():
            resource_type = resource["type"]
            if resource_type not in costs:
                costs[resource_type] = 0
            costs[resource_type] += resource["cost"]

        return costs

    def identify_expensive_resources(self, top_n: int = 10) -> List[tuple]:
        """Find most expensive resources"""
        sorted_resources = sorted(
            self._costs.items(),
            key=lambda x: x[1]["cost"],
            reverse=True
        )

        return sorted_resources[:top_n]

    def find_optimization_opportunities(self) -> List[Dict]:
        """Suggest cost optimizations"""
        opportunities = []

        for resource_id, resource in self._costs.items():
            cost = resource["cost"]
            resource_type = resource["type"]

            # Heuristics
            if cost > 1000 and resource_type == "ec2":
                opportunities.append({
                    "resource": resource_id,
                    "type": "right-size",
                    "savings": cost * 0.3,  # estimate
                    "description": "Downsize instance"
                })

        return opportunities
'''

    return tracker


def generate_cost_system() -> dict:
    """Generate complete cost optimization system."""

    imports = '''from typing import Dict, List, Optional
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Cost Optimization: FinOps Principles

Optimize cloud spending (AWS, Google Cloud, Azure).

COST BREAKDOWN (typical SaaS):
- Compute (servers): 40%
- Storage (databases): 30%
- Network (data transfer): 20%
- Services (CDN, queues): 10%

OPTIMIZATION TECHNIQUES:

1. RIGHT-SIZE COMPUTE
   - Small instance: $50/month, using 10% CPU → downsize
   - Cost: $50 → $25 (50% savings)
   - Method: monitor CPU/memory, downsize what's unused

2. RESERVED INSTANCES
   - On-demand: $100/month
   - 1-year commitment: $60/month (40% discount)
   - Method: commit for baseline traffic, on-demand for spikes

3. SPOT INSTANCES (risky but cheap)
   - On-demand: $100/month
   - Spot: $10/month (90% cheaper)
   - Catch: AWS can reclaim anytime
   - Method: batch jobs, non-critical workloads

4. CLEANUP
   - Find: old EC2 instances, unattached EBS volumes, old snapshots
   - Cost: wasted $1000/month
   - Method: automated cleanup scripts, set lifetime limits

5. EFFICIENT QUERIES
   - Bad: N+1 queries (1000 queries per request)
   - Good: 1 query with join
   - Cost: RDS $10 → $1 per request
   - Method: use profiling, cache results

6. STORAGE OPTIMIZATION
   - Hot data (database): expensive tier
   - Warm data (archives): cheaper tier
   - Cold data (deleted): free (delete it!)
   - Method: lifecycle policies (S3 → Glacier after 30 days)

MONITORING:

Daily:
- Total spend vs budget
- Alert if trending high

Weekly:
- Cost by service
- Identify spikes

Monthly:
- Trend analysis
- Forecasting
- Optimization review

TARGETS:
- Reduce cost: 30% in 6 months
- Improve efficiency: cost per transaction down
- No surprises: accurate forecasting
"""
'''

    tracker = generate_cost_tracker()

    complete_code = imports + module_doc + "\n" + tracker

    return {
        "code": complete_code,
        "pattern": "Cost Optimization",
        "module": "phase5_cost_optimization.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate cost optimization")
    args = parser.parse_args()
    result = generate_cost_system()
    print(result["code"])


if __name__ == "__main__":
    main()
