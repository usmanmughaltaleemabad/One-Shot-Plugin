#!/usr/bin/env python3
"""Phase 5 Request Deduplication: Idempotency Keys & Saga Compensation"""

from typing import Dict, Optional
from datetime import datetime


def generate_request_deduplication() -> str:
    return '''
class IdempotencyManager:
    """Prevent duplicate request processing with idempotency keys."""

    def __init__(self):
        self._requests = {}  # idempotency_key → {status, response}

    def process_with_idempotency(
        self,
        idempotency_key: str,
        handler,
        args
    ) -> Dict:
        """Process request, deduplicate by key"""
        if idempotency_key in self._requests:
            cached = self._requests[idempotency_key]
            if cached["status"] == "completed":
                return cached["response"]

        # First time, process
        response = handler(*args)

        # Cache result
        self._requests[idempotency_key] = {
            "status": "completed",
            "response": response,
            "processed_at": datetime.utcnow().isoformat()
        }

        return response

    def get_request_status(self, idempotency_key: str) -> Optional[Dict]:
        """Check if request was already processed"""
        return self._requests.get(idempotency_key)


class SagaCompensation:
    """Compensate failed saga steps (undo completed steps)."""

    def __init__(self):
        self._compensations = {}  # step_id → compensation_fn

    def register_compensation(self, step_id: str, fn) -> None:
        """Register compensation function"""
        self._compensations[step_id] = fn

    def compensate(self, completed_steps: list) -> None:
        """Run compensations in reverse order"""
        for step_id in reversed(completed_steps):
            if step_id in self._compensations:
                self._compensations[step_id]()
'''
    return generate_request_deduplication()


if __name__ == "__main__":
    print(generate_request_deduplication())
