#!/usr/bin/env python3
"""
Phase 5 High Availability: Database Replication

Replication: Keep copies of data synchronized.

Problem: Single database failure = downtime
- Database crashes
- Users can't access data
- Manual failover = 30 minutes downtime

Replication (solution):
- Primary: receives writes
- Replicas: copy of data (read-only or failover)
- Synchronous: replica confirms before return (safe, slow)
- Asynchronous: return before replica copies (fast, risk of loss)

Strategies:
- Leader-Follower: one primary, many replicas
- Multi-Leader: multiple primaries (conflict complexity)
- Peer-to-Peer: all equal (eventual consistency)
"""

from typing import Dict, List, Optional
from datetime import datetime


def generate_database_replication() -> str:
    """Generate database replication system."""

    replication = '''
class DatabaseReplication:
    """
    Replicate data to standby databases.

    Modes:
    - Async: Primary returns immediately, replicas catch up
    - Sync: Primary waits for replica confirmation
    - Semi-sync: Wait for one replica, not all
    """

    def __init__(self):
        self._primary = None
        self._replicas = []
        self._replication_lag = {}  # replica → lag_ms

    def register_replica(self, replica_id: str, connection_string: str) -> None:
        """Register read replica"""
        self._replicas.append({
            "id": replica_id,
            "connection": connection_string,
            "status": "connecting",
            "lag_ms": 0
        })

    def write_to_primary(self, data: Dict) -> bool:
        """Write to primary (synchronous)"""
        # Write to primary
        success = self._primary.insert(data)

        if not success:
            return False

        # Replicate to followers
        for replica in self._replicas:
            try:
                replica["connection"].insert(data)
                replica["lag_ms"] = 0
            except Exception as e:
                replica["lag_ms"] = 1000  # Mark as lagged

        return True

    def get_replica_lag(self) -> Dict[str, int]:
        """Monitor replication lag"""
        return {
            r["id"]: r["lag_ms"]
            for r in self._replicas
        }

    def promote_replica(self, replica_id: str) -> bool:
        """Promote replica to primary (failover)"""
        replica = next((r for r in self._replicas if r["id"] == replica_id), None)

        if not replica:
            return False

        # Make replica the new primary
        self._primary = replica["connection"]
        self._replicas.remove(replica)

        return True
'''

    return replication


def generate_replication_system() -> dict:
    """Generate complete replication system."""

    imports = '''from typing import Dict, List, Optional
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Database Replication: High Availability

Keep database copies synchronized (PostgreSQL streaming replication, MySQL binlog).

ARCHITECTURE:

Primary (Write-only):
- Receives all writes
- Writes to WAL (Write-Ahead Log)
- Sends WAL to replicas

Replicas (Read-only):
- Apply WAL entries in order
- Always lag behind primary (milliseconds to seconds)
- Serve read traffic
- Promote to primary if needed

REPLICATION MODES:

1. ASYNCHRONOUS (fast, risky)
   - Primary: commit write immediately
   - Replica: copies lag by 100-500ms
   - Risk: if primary crashes, last writes lost
   - Use: analytics (lose OK), non-critical data

2. SYNCHRONOUS (slow, safe)
   - Primary: wait for replica confirmation
   - Replica: confirms receipt
   - Data safe: won't lose writes
   - Cost: slower commits (network latency)
   - Use: financial data, user accounts

3. SEMI-SYNCHRONOUS (balanced)
   - Primary: wait for 1 replica (not all)
   - Fast enough, safer than async
   - Use: most production systems

FAILOVER STRATEGY:

Detect Primary Down:
- Health check fails
- Connection refused
- No heartbeat

Automatic Failover:
- Pick best replica (least lag)
- Promote to primary
- Redirect traffic (update DNS/app)
- Time: < 1 minute

Manual Failover:
- DBA decides which replica to promote
- Data consistency check
- Redirect traffic
- Post-mortem on why primary failed

MONITORING:

- Replication lag: replica_lag_bytes, replication_lag_seconds
- Disk usage: transaction log size
- Network bandwidth: replication traffic
- Alert if: lag > 30 seconds
"""
'''

    replication = generate_database_replication()

    complete_code = imports + module_doc + "\n" + replication

    return {
        "code": complete_code,
        "pattern": "Database Replication",
        "module": "phase5_database_replication.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate database replication")
    args = parser.parse_args()
    result = generate_replication_system()
    print(result["code"])


if __name__ == "__main__":
    main()
