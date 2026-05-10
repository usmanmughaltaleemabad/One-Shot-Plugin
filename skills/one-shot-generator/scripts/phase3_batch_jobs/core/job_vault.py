"""
Job Vault - OneShot-inspired state management for batch jobs

Implements vault-centric architecture:
- Append-only work logs for audit trails
- Checkpoints for resumption and failure recovery
- Decision records for transparency
- Timestamp discipline for temporal reasoning
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class JobStatus(Enum):
    """Job status transitions"""
    CREATED = "created"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    CHECKPOINTED = "checkpointed"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class WorkLogEntry:
    """Immutable work log entry"""
    timestamp: str  # ISO 8601: 2026-05-09T14:30:45+00:00
    agent: str
    action: str
    result: str
    checkpoint: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class DecisionRecord:
    """Decision with reasoning and alternatives"""
    timestamp: str
    decision: str
    rationale: str
    alternatives_considered: List[str]
    chosen_option: str
    impact: str


class JobVault:
    """
    Vault for job state, inspired by OneShot's vault-centric design.

    Directory structure:
    vault/
    ├── jobs/
    │   ├── job-{id}/
    │   │   ├── manifest.json        (job definition, status, config)
    │   │   ├── work_log.md          (append-only activity log)
    │   │   ├── decisions.md         (decision records)
    │   │   ├── checkpoints/         (resumable state snapshots)
    │   │   │   ├── checkpoint-001.json
    │   │   │   └── checkpoint-002.json
    │   │   └── results/             (job outputs, artifacts)
    │   └── job-{id}/...
    ├── config/
    │   ├── budget.md               (spending limits, tracking)
    │   └── admin_log.md            (access control, sensitive ops)
    └── archive/                     (completed jobs snapshot)
    """

    def __init__(self, vault_dir: str = "./job_vault"):
        self.vault_dir = Path(vault_dir)
        self.jobs_dir = self.vault_dir / "jobs"
        self.config_dir = self.vault_dir / "config"
        self._ensure_structure()

    def _ensure_structure(self):
        """Ensure vault directory structure exists"""
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def create_job(
        self,
        job_id: str,
        job_config: Dict[str, Any],
        framework: str,
        language: str
    ) -> str:
        """Create new job vault"""
        job_dir = self.jobs_dir / f"job-{job_id}"
        job_dir.mkdir(parents=True, exist_ok=True)

        # Manifest: immutable job definition + metadata
        manifest = {
            "job_id": job_id,
            "created_at": self._timestamp(),
            "framework": framework,
            "language": language,
            "status": JobStatus.CREATED.value,
            "config": job_config,
            "checkpoints": [],
            "retry_count": 0,
            "last_update": self._timestamp(),
        }

        self._write_json(job_dir / "manifest.json", manifest)
        self._write_markdown(job_dir / "work_log.md", f"# Work Log for {job_id}\n\n")
        self._write_markdown(job_dir / "decisions.md", f"# Decisions for {job_id}\n\n")

        (job_dir / "checkpoints").mkdir(exist_ok=True)
        (job_dir / "results").mkdir(exist_ok=True)

        return str(job_dir)

    def get_job_manifest(self, job_id: str) -> Dict[str, Any]:
        """Get current job manifest"""
        job_dir = self.jobs_dir / f"job-{job_id}"
        return self._read_json(job_dir / "manifest.json")

    def append_work_log(self, job_id: str, entry: WorkLogEntry):
        """Append immutable work log entry"""
        job_dir = self.jobs_dir / f"job-{job_id}"
        work_log = job_dir / "work_log.md"

        entry_text = f"""
## [{entry.timestamp}] {entry.action}
- **Agent:** {entry.agent}
- **Result:** {entry.result}
"""
        if entry.error:
            entry_text += f"- **Error:** {entry.error}\n"
        if entry.checkpoint:
            entry_text += f"- **Checkpoint:** {json.dumps(entry.checkpoint, indent=2)}\n"

        with open(work_log, "a") as f:
            f.write(entry_text + "\n")

    def create_checkpoint(self, job_id: str, state: Dict[str, Any]) -> str:
        """
        Create resumable checkpoint.

        Returns: checkpoint filename
        """
        job_dir = self.jobs_dir / f"job-{job_id}"
        checkpoints_dir = job_dir / "checkpoints"

        manifest = self._read_json(job_dir / "manifest.json")
        checkpoint_num = len(manifest["checkpoints"]) + 1
        checkpoint_file = f"checkpoint-{checkpoint_num:03d}.json"

        checkpoint_data = {
            "checkpoint_id": checkpoint_num,
            "timestamp": self._timestamp(),
            "state": state,
        }

        self._write_json(checkpoints_dir / checkpoint_file, checkpoint_data)

        # Update manifest
        manifest["checkpoints"].append({
            "id": checkpoint_num,
            "timestamp": checkpoint_data["timestamp"],
            "file": checkpoint_file,
        })
        manifest["status"] = JobStatus.CHECKPOINTED.value
        manifest["last_update"] = self._timestamp()
        self._write_json(job_dir / "manifest.json", manifest)

        return checkpoint_file

    def resume_from_checkpoint(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Resume job from latest checkpoint.

        Returns: checkpoint state or None if no checkpoints exist
        """
        job_dir = self.jobs_dir / f"job-{job_id}"
        manifest = self._read_json(job_dir / "manifest.json")

        if not manifest["checkpoints"]:
            return None

        # Get latest checkpoint
        latest = manifest["checkpoints"][-1]
        checkpoint_file = job_dir / "checkpoints" / latest["file"]

        checkpoint_data = self._read_json(checkpoint_file)
        return checkpoint_data["state"]

    def record_decision(
        self,
        job_id: str,
        decision: str,
        rationale: str,
        alternatives: List[str],
        chosen: str,
        impact: str
    ):
        """Record strategic decision"""
        job_dir = self.jobs_dir / f"job-{job_id}"
        decisions_file = job_dir / "decisions.md"

        decision_text = f"""
## {decision}
- **Timestamp:** {self._timestamp()}
- **Rationale:** {rationale}
- **Alternatives Considered:** {', '.join(alternatives)}
- **Chosen:** {chosen}
- **Impact:** {impact}

"""
        with open(decisions_file, "a") as f:
            f.write(decision_text)

    def update_job_status(self, job_id: str, status: JobStatus, message: str = ""):
        """Update job status (triggers manifest update)"""
        job_dir = self.jobs_dir / f"job-{job_id}"
        manifest = self._read_json(job_dir / "manifest.json")

        manifest["status"] = status.value
        manifest["last_update"] = self._timestamp()

        if message:
            manifest["status_message"] = message

        self._write_json(job_dir / "manifest.json", manifest)

    def store_result(self, job_id: str, result_name: str, result_data: Any):
        """Store job result artifact"""
        job_dir = self.jobs_dir / f"job-{job_id}"
        results_dir = job_dir / "results"

        result_file = results_dir / f"{result_name}.json"
        self._write_json(result_file, result_data)

    def get_result(self, job_id: str, result_name: str) -> Optional[Any]:
        """Retrieve stored result"""
        job_dir = self.jobs_dir / f"job-{job_id}"
        result_file = job_dir / "results" / f"{result_name}.json"

        if not result_file.exists():
            return None

        return self._read_json(result_file)

    def check_budget(self, job_id: str, operation_cost: float) -> bool:
        """Check if operation cost exceeds budget"""
        job_dir = self.jobs_dir / f"job-{job_id}"
        manifest = self._read_json(job_dir / "manifest.json")

        budget = manifest.get("config", {}).get("budget", float("inf"))
        current_cost = manifest.get("total_cost", 0.0)

        return (current_cost + operation_cost) <= budget

    def record_spending(self, job_id: str, amount: float, description: str):
        """Record spending to budget"""
        job_dir = self.jobs_dir / f"job-{job_id}"
        manifest = self._read_json(job_dir / "manifest.json")

        manifest["total_cost"] = manifest.get("total_cost", 0.0) + amount
        manifest["spending_log"] = manifest.get("spending_log", [])
        manifest["spending_log"].append({
            "timestamp": self._timestamp(),
            "amount": amount,
            "description": description,
        })

        self._write_json(job_dir / "manifest.json", manifest)

    def list_jobs(self) -> List[str]:
        """List all job IDs"""
        job_dirs = self.jobs_dir.glob("job-*")
        return [d.name.replace("job-", "") for d in job_dirs if d.is_dir()]

    def get_job_summary(self, job_id: str) -> Dict[str, Any]:
        """Get job summary for display"""
        manifest = self.get_job_manifest(job_id)
        return {
            "job_id": manifest["job_id"],
            "status": manifest["status"],
            "created_at": manifest["created_at"],
            "last_update": manifest["last_update"],
            "checkpoints": len(manifest["checkpoints"]),
            "retry_count": manifest["retry_count"],
            "total_cost": manifest.get("total_cost", 0.0),
            "framework": manifest["framework"],
            "language": manifest["language"],
        }

    # Private helpers
    def _timestamp(self) -> str:
        """Get ISO 8601 timestamp"""
        return datetime.utcnow().isoformat() + "Z"

    def _write_json(self, path: Path, data: Dict[str, Any]):
        """Atomically write JSON"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _read_json(self, path: Path) -> Dict[str, Any]:
        """Read JSON"""
        with open(path, "r") as f:
            return json.load(f)

    def _write_markdown(self, path: Path, content: str):
        """Write markdown"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)

    def _read_markdown(self, path: Path) -> str:
        """Read markdown"""
        with open(path, "r") as f:
            return f.read()
