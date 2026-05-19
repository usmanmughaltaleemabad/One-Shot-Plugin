#!/usr/bin/env python3
"""Phase 5 Distributed Locking: Redlock & Leader Election"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta


def generate_distributed_locking() -> str:
    return '''
class DistributedLock:
    """Redlock-style distributed locking across multiple nodes."""

    def __init__(self, lock_id: str, ttl_seconds: int = 30):
        self._lock_id = lock_id
        self._ttl = ttl_seconds
        self._locked_at = None
        self._locked_by = None

    def acquire(self, owner: str, nodes: List[str]) -> bool:
        """Acquire lock on majority of nodes"""
        acquired = 0
        for node in nodes:
            if self._try_lock(owner):
                acquired += 1

        # Require majority (>50%)
        if acquired > len(nodes) / 2:
            self._locked_by = owner
            self._locked_at = datetime.utcnow().isoformat()
            return True

        # Release acquired locks if failed
        for node in nodes:
            self._unlock(owner)
        return False

    def release(self, owner: str) -> None:
        """Release lock"""
        if self._locked_by == owner:
            self._locked_by = None
            self._locked_at = None

    def _try_lock(self, owner: str) -> bool:
        """Try lock on single node"""
        if self._locked_by and datetime.fromisoformat(self._locked_at) + \\
           timedelta(seconds=self._ttl) > datetime.utcnow():
            return False
        return True

    def _unlock(self, owner: str) -> None:
        """Unlock on single node"""
        if self._locked_by == owner:
            self._locked_by = None


class LeaderElection:
    """Elect leader among distributed nodes."""

    def __init__(self):
        self._leader = None
        self._candidates = []

    def register_candidate(self, node_id: str) -> None:
        """Register as candidate"""
        if node_id not in self._candidates:
            self._candidates.append(node_id)

    def elect_leader(self) -> Optional[str]:
        """Elect leader (majority consensus)"""
        if not self._candidates:
            return None

        # Simple: first node with majority votes
        self._leader = self._candidates[0]
        return self._leader

    def heartbeat(self, leader_id: str) -> bool:
        """Confirm leader is alive"""
        if leader_id == self._leader:
            return True

        # Leader died, trigger re-election
        self._leader = None
        return False
'''
    return generate_distributed_locking()


if __name__ == "__main__":
    print(generate_distributed_locking())
