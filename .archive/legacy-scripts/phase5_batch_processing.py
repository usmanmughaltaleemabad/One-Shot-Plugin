#!/usr/bin/env python3
"""
Phase 5 Batch Processing: Job Orchestration & Distributed Computing

Batch Processing: Process large datasets offline (not real-time).

Problem: Real-time processing bottleneck
- Process 1M records in real-time: slow
- User waits: 10 seconds response time
- Resource waste: servers idle when done

Batch Processing (solution):
- Schedule job: process 1M records offline
- Distribute: split across workers
- Map-reduce: aggregate results
- Resilience: retry failures
- Efficiency: use off-peak hours
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime


def generate_batch_processing() -> str:
    """Generate batch processing system."""

    batch = '''
class BatchProcessor:
    """
    Orchestrate batch jobs across workers.

    Workflow:
    1. Submit job
    2. Split into partitions
    3. Map: process each partition (worker)
    4. Reduce: aggregate results
    5. Store results
    """

    def __init__(self):
        self._jobs = {}  # job_id → job
        self._partitions = {}  # partition_id → {status, worker, data}
        self._workers = []  # Available workers
        self._results = {}  # job_id → aggregated result

    def register_worker(self, worker_id: str, capacity: int) -> None:
        """Register a worker"""
        self._workers.append({
            "id": worker_id,
            "capacity": capacity,
            "current_load": 0,
            "status": "idle"
        })

    def submit_job(
        self,
        job_id: str,
        input_data: List,
        map_fn: Callable,
        reduce_fn: Callable
    ) -> str:
        """Submit batch job"""
        job = {
            "id": job_id,
            "input_size": len(input_data),
            "map_fn": map_fn,
            "reduce_fn": reduce_fn,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "partitions": []
        }

        self._jobs[job_id] = job

        # Split into partitions
        num_workers = len(self._workers)
        partition_size = max(1, len(input_data) // num_workers)

        for i in range(num_workers):
            start = i * partition_size
            end = start + partition_size if i < num_workers - 1 else len(input_data)

            partition_id = f"{job_id}-p{i}"
            self._partitions[partition_id] = {
                "id": partition_id,
                "job_id": job_id,
                "data": input_data[start:end],
                "status": "pending",
                "worker": None,
                "result": None
            }

            job["partitions"].append(partition_id)

        job["status"] = "partitioned"
        return job_id

    def assign_partitions(self, job_id: str) -> None:
        """Assign partitions to workers"""
        job = self._jobs.get(job_id)
        if not job:
            return

        for partition_id in job["partitions"]:
            partition = self._partitions[partition_id]

            # Find worker with capacity
            worker = next((w for w in self._workers if w["current_load"] < w["capacity"]), None)
            if not worker:
                continue

            partition["worker"] = worker["id"]
            partition["status"] = "assigned"
            worker["current_load"] += 1

        job["status"] = "assigned"

    def process_partition(self, partition_id: str) -> None:
        """Worker processes partition (map phase)"""
        partition = self._partitions.get(partition_id)
        if not partition:
            return

        job = self._jobs.get(partition["job_id"])
        if not job:
            return

        # Apply map function
        try:
            result = job["map_fn"](partition["data"])
            partition["result"] = result
            partition["status"] = "completed"
        except Exception as e:
            partition["status"] = "failed"
            partition["error"] = str(e)

    def reduce_job(self, job_id: str) -> None:
        """Reduce: aggregate results"""
        job = self._jobs.get(job_id)
        if not job:
            return

        # Collect results from all partitions
        partition_results = []
        for partition_id in job["partitions"]:
            partition = self._partitions[partition_id]
            if partition["status"] == "completed":
                partition_results.append(partition["result"])

        # Apply reduce function
        if partition_results:
            final_result = job["reduce_fn"](partition_results)
            self._results[job_id] = final_result
            job["status"] = "completed"
            job["completed_at"] = datetime.utcnow().isoformat()
        else:
            job["status"] = "failed"

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status"""
        return self._jobs.get(job_id)

    def get_job_result(self, job_id: str) -> Optional:
        """Get job result"""
        return self._results.get(job_id)

    def retry_failed_partitions(self, job_id: str) -> None:
        """Retry failed partitions"""
        job = self._jobs.get(job_id)
        if not job:
            return

        for partition_id in job["partitions"]:
            partition = self._partitions[partition_id]
            if partition["status"] == "failed":
                partition["status"] = "pending"
                partition["retry_count"] = partition.get("retry_count", 0) + 1
'''

    return batch


def generate_batch_system() -> dict:
    """Generate complete batch processing system."""

    imports = '''from typing import Dict, List, Optional, Callable
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Batch Processing: Job Orchestration & Distributed Computing

Process large datasets efficiently using map-reduce pattern (Apache Spark, Hadoop).

MAP-REDUCE PATTERN:

Input: 1,000,000 sales transactions
Goal: Calculate total revenue by region

MAP (process):
- Worker 1: transactions 0-250k → sum by region
  Result: {US: $50M, EU: $30M, APAC: $20M}
- Worker 2: transactions 250k-500k → sum by region
  Result: {US: $45M, EU: $35M, APAC: $25M}
- Worker 3: transactions 500k-750k → sum by region
  Result: {US: $55M, EU: $25M, APAC: $30M}
- Worker 4: transactions 750k-1M → sum by region
  Result: {US: $48M, EU: $32M, APAC: $28M}

REDUCE (aggregate):
- Combine all regions:
  {US: 50+45+55+48 = $198M, EU: 30+35+25+32 = $122M, APAC: 20+25+30+28 = $103M}

Output: Total revenue by region

WORKFLOW:

1. SUBMIT JOB
   Input: 1M transactions
   Map function: sum_by_region(batch)
   Reduce function: combine_regions([results])

2. SPLIT (partition)
   Divide input: 1M transactions / 4 workers = 250k each
   Partition 1: transactions 0-250k
   Partition 2: transactions 250k-500k
   Partition 3: transactions 500k-750k
   Partition 4: transactions 750k-1M

3. ASSIGN
   Worker 1: Partition 1
   Worker 2: Partition 2
   Worker 3: Partition 3
   Worker 4: Partition 4

4. MAP (parallel)
   Time: all 4 workers process simultaneously
   Duration: ~1 minute (for 1M transactions)
   vs. single-worker: ~4 minutes (4x faster)

5. REDUCE
   Collect results from 4 workers
   Sum by region
   Duration: seconds

6. STORE RESULT
   Write result to database/storage
   Update status: COMPLETED
   Total time: ~2 minutes

RESILIENCE:

Failure scenarios:
- Worker 1 crashes (mid-process)
- Network partition (can't reach worker)
- Data corruption (bad data in partition)

Handling:
- Detect: heartbeat timeout, error response
- Retry: assign partition to another worker
- Backpressure: wait for resources
- Dead letter: if 3 retries fail, skip partition

Example:
Worker 1 assigned Partition 1
→ Worker 1 crashes
→ Detect failure (timeout)
→ Reassign Partition 1 to Worker 3
→ Worker 3 processes partition
→ Result available

SCHEDULING:

Immediate:
- Job runs ASAP
- Use when: small jobs, interactive
- Cost: higher (use premium hours)

Scheduled:
- Job runs at specific time (e.g., 2am)
- Use when: large jobs, off-peak
- Cost: lower (off-peak pricing)

Priority:
- Job 1: priority=HIGH → runs first
- Job 2: priority=LOW → runs when resources free

Example: Nightly Batch
- Schedule: 2am daily
- Input: all transactions from previous day
- Map: classify by category
- Reduce: generate daily report
- Store: database, ready for dashboard
- Run time: 30 minutes
- Users wake up: report ready

SCALABILITY:

Small job (10k records):
- 1 worker sufficient
- Time: 10 seconds
- Cost: minimal

Medium job (1M records):
- 4 workers
- Time: 2 minutes
- Cost: moderate

Large job (100M records):
- 100 workers
- Time: 2 minutes (same, more parallel)
- Cost: higher (more resources)

Huge job (1B records, Petabytes):
- 1000 workers (distributed)
- Time: still ~2 minutes
- Cost: significant
- Scalability: linear (more data = more workers)

ERROR HANDLING:

Transient error (network blip):
- Retry: up to 3 times
- Backoff: exponential (1s, 2s, 4s)
- Result: usually succeeds on retry

Permanent error (bad data):
- Retry: 3x fails
- Skip partition: log error
- Result: completed with missing data
- Alert: investigate corrupt data

Resource exhaustion:
- All workers busy
- Backpressure: queue job
- Wait: resources free (other job completes)
- Result: job runs when space available

COMMON PITFALLS:

❌ No partitioning: single worker processes all
   → Serial processing, no speedup
   → Solution: partition by size or key

❌ No retry: first failure = job fails
   → Fragile, network hiccups break jobs
   → Solution: retry with exponential backoff

❌ No monitoring: don't know job status
   → Takes forever? Crashed? Who knows?
   → Solution: track progress, log events

✓ Good batch:
   - Partitioned: scales with workers
   - Resilient: retries transient failures
   - Observable: progress tracked
   - Efficient: uses off-peak hours
"""
'''

    batch = generate_batch_processing()

    complete_code = imports + module_doc + "\n" + batch

    return {
        "code": complete_code,
        "pattern": "Batch Processing",
        "module": "phase5_batch_processing.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate batch processing")
    args = parser.parse_args()
    result = generate_batch_system()
    print(result["code"])


if __name__ == "__main__":
    main()
