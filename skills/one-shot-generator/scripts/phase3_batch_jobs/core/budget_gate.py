"""
Budget Gate - Cost management and spending controls

Inspired by OneShot's metering and spending limits:
- Per-job budget enforcement
- Daily/monthly spending caps
- Operation cost tracking
- Pause/resume on budget limits
- Admin approval gates for high-cost operations
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from enum import Enum


class BudgetDecision(Enum):
    """Budget decision outcomes"""
    APPROVED = "approved"
    DENIED = "denied"
    NEEDS_APPROVAL = "needs_approval"
    PAUSED_BUDGET_LIMIT = "paused_budget_limit"


class BudgetGate:
    """
    Cost gate for batch jobs.

    Enforces:
    - Per-job budget
    - Daily limit
    - Monthly limit
    - Per-operation cost checks
    - Spending transparency
    """

    def __init__(self, vault_dir: str = "./job_vault"):
        self.vault_dir = Path(vault_dir)
        self.config_dir = self.vault_dir / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def check_operation_cost(
        self,
        job_id: str,
        operation: str,
        estimated_cost: float,
        approval_required_above: float = 50.0
    ) -> Tuple[BudgetDecision, str]:
        """
        Check if operation cost is within budget.

        Returns: (decision, reason)
        """
        job_dir = self.vault_dir / "jobs" / f"job-{job_id}"
        manifest_file = job_dir / "manifest.json"

        with open(manifest_file) as f:
            manifest = json.load(f)

        # Get budget config
        job_budget = manifest.get("config", {}).get("budget", float("inf"))
        current_spent = manifest.get("total_cost", 0.0)

        # Check job-level budget
        if current_spent + estimated_cost > job_budget:
            return BudgetDecision.DENIED, \
                f"Job budget exceeded: ${current_spent:.2f} + ${estimated_cost:.2f} > ${job_budget:.2f}"

        # Check if approval needed
        if estimated_cost > approval_required_above:
            return BudgetDecision.NEEDS_APPROVAL, \
                f"High-cost operation requires approval: ${estimated_cost:.2f}"

        # Check daily limit
        daily_limit = manifest.get("config", {}).get("daily_limit", float("inf"))
        daily_spent = self._get_daily_spending(job_id)

        if daily_spent + estimated_cost > daily_limit:
            return BudgetDecision.PAUSED_BUDGET_LIMIT, \
                f"Daily limit would be exceeded: ${daily_spent:.2f} + ${estimated_cost:.2f} > ${daily_limit:.2f}"

        return BudgetDecision.APPROVED, \
            f"Cost approved: ${estimated_cost:.2f} (total job: ${current_spent + estimated_cost:.2f})"

    def record_operation(
        self,
        job_id: str,
        operation: str,
        actual_cost: float,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Record completed operation cost.

        Returns: spending record
        """
        job_dir = self.vault_dir / "jobs" / f"job-{job_id}"
        manifest_file = job_dir / "manifest.json"

        with open(manifest_file) as f:
            manifest = json.load(f)

        # Update total cost
        manifest["total_cost"] = manifest.get("total_cost", 0.0) + actual_cost

        # Create spending record
        spending_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "operation": operation,
            "cost": actual_cost,
            "description": description,
            "running_total": manifest["total_cost"],
        }

        # Append to spending log
        if "spending_log" not in manifest:
            manifest["spending_log"] = []
        manifest["spending_log"].append(spending_record)

        # Save manifest
        with open(manifest_file, "w") as f:
            json.dump(manifest, f, indent=2, default=str)

        # Also update global spending log for admin visibility
        self._append_global_spending_log(job_id, spending_record)

        return spending_record

    def get_job_spending_summary(self, job_id: str) -> Dict[str, Any]:
        """Get detailed spending summary for a job"""
        job_dir = self.vault_dir / "jobs" / f"job-{job_id}"
        manifest_file = job_dir / "manifest.json"

        with open(manifest_file) as f:
            manifest = json.load(f)

        spending_log = manifest.get("spending_log", [])
        config = manifest.get("config", {})

        return {
            "job_id": job_id,
            "budget": config.get("budget", "unlimited"),
            "total_spent": manifest.get("total_cost", 0.0),
            "daily_limit": config.get("daily_limit", "unlimited"),
            "daily_spent": self._get_daily_spending(job_id),
            "spending_by_operation": self._group_by_operation(spending_log),
            "transaction_count": len(spending_log),
            "last_operation": spending_log[-1] if spending_log else None,
        }

    def require_approval(
        self,
        job_id: str,
        operation: str,
        reason: str,
        approver: str
    ) -> bool:
        """
        Record approval requirement.

        Used for high-cost or sensitive operations.
        """
        approval_log_file = self.config_dir / "approvals.json"

        approvals = []
        if approval_log_file.exists():
            with open(approval_log_file) as f:
                approvals = json.load(f)

        approval = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "job_id": job_id,
            "operation": operation,
            "reason": reason,
            "approver": approver,
            "status": "pending",
        }

        approvals.append(approval)

        with open(approval_log_file, "w") as f:
            json.dump(approvals, f, indent=2, default=str)

        return True

    def set_pause_on_budget_limit(self, job_id: str) -> Dict[str, Any]:
        """
        Pause job execution when budget limit reached.

        Returns: pause record for audit
        """
        job_dir = self.vault_dir / "jobs" / f"job-{job_id}"
        manifest_file = job_dir / "manifest.json"

        with open(manifest_file) as f:
            manifest = json.load(f)

        pause_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "reason": "budget_limit_reached",
            "total_spent": manifest.get("total_cost", 0.0),
            "budget": manifest.get("config", {}).get("budget"),
            "resume_requires": "manual_approval",
        }

        # Log pause
        if "pauses" not in manifest:
            manifest["pauses"] = []
        manifest["pauses"].append(pause_record)

        # Set status
        manifest["status"] = "paused_budget"

        with open(manifest_file, "w") as f:
            json.dump(manifest, f, indent=2, default=str)

        self._log_admin_action(
            f"Job {job_id} paused due to budget limit",
            "budget_pause",
            pause_record
        )

        return pause_record

    def get_spending_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate spending report across all jobs.

        Dates in ISO 8601 format (2026-05-09T14:30:45Z)
        """
        global_log_file = self.config_dir / "global_spending.json"

        if not global_log_file.exists():
            return {"total_jobs": 0, "total_spent": 0.0, "jobs": []}

        with open(global_log_file) as f:
            spending_data = json.load(f)

        # Filter by date if specified
        transactions = spending_data.get("transactions", [])
        if start_date or end_date:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00")) if start_date else None
            end = datetime.fromisoformat(end_date.replace("Z", "+00:00")) if end_date else None

            filtered = []
            for tx in transactions:
                tx_time = datetime.fromisoformat(tx["timestamp"].replace("Z", "+00:00"))
                if start and tx_time < start:
                    continue
                if end and tx_time > end:
                    continue
                filtered.append(tx)
            transactions = filtered

        # Aggregate
        total_spent = sum(t["cost"] for t in transactions)
        jobs = set(t["job_id"] for t in transactions)

        return {
            "total_jobs": len(jobs),
            "total_spent": total_spent,
            "transaction_count": len(transactions),
            "jobs": list(jobs),
            "date_range": {
                "start": start_date or "all",
                "end": end_date or "all",
            },
        }

    # Private helpers
    def _get_daily_spending(self, job_id: str) -> float:
        """Get spending for today"""
        job_dir = self.vault_dir / "jobs" / f"job-{job_id}"
        manifest_file = job_dir / "manifest.json"

        with open(manifest_file) as f:
            manifest = json.load(f)

        spending_log = manifest.get("spending_log", [])
        today = datetime.utcnow().date()

        daily_total = 0.0
        for entry in spending_log:
            entry_date = datetime.fromisoformat(
                entry["timestamp"].replace("Z", "+00:00")
            ).date()
            if entry_date == today:
                daily_total += entry["cost"]

        return daily_total

    def _group_by_operation(self, spending_log: list) -> Dict[str, float]:
        """Group spending by operation type"""
        grouped = {}
        for entry in spending_log:
            op = entry["operation"]
            grouped[op] = grouped.get(op, 0.0) + entry["cost"]
        return grouped

    def _append_global_spending_log(self, job_id: str, record: Dict[str, Any]):
        """Append to global spending log"""
        log_file = self.config_dir / "global_spending.json"

        data = {"transactions": []}
        if log_file.exists():
            with open(log_file) as f:
                data = json.load(f)

        record["job_id"] = job_id
        data["transactions"].append(record)

        with open(log_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _log_admin_action(self, action: str, action_type: str, details: Dict[str, Any]):
        """Log admin-level action"""
        log_file = self.config_dir / "admin_log.json"

        actions = []
        if log_file.exists():
            with open(log_file) as f:
                actions = json.load(f)

        actions.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": action,
            "type": action_type,
            "details": details,
        })

        with open(log_file, "w") as f:
            json.dump(actions, f, indent=2, default=str)
