#!/usr/bin/env python3
"""
L1 Memory Routing — decision tracing for the agentic pipeline.

Logs which layer (L1 Router, L2 Module Instructions, L3 Data Vault) made each
decision. Enables introspection: "where did this architecture decision come from?"

Layer definitions:
  - L1 Router: Dispatcher layer (templated vs agentic, curriculum hits, discovery)
  - L2 Module Instructions: Stage-specific logic (architect constraints, implementer hints)
  - L3 Data Vault: External data (curriculum beads, registry recommendations, imports)
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any


class RoutingTrace:
    """Records decision flow through the pipeline."""

    def __init__(self, session_id: str, project_root: str, output_file: Optional[str] = None):
        self.session_id = session_id
        self.project_root = project_root
        self.start_time = datetime.now().isoformat()
        self.decisions: list[dict[str, Any]] = []
        self.output_file = output_file or Path(project_root) / ".one-shot" / "routing_trace.jsonl"
        Path(self.output_file).parent.mkdir(parents=True, exist_ok=True)

    def log_decision(
        self,
        stage: str,
        layer: str,  # "L1_ROUTER", "L2_MODULE", "L3_DATA"
        decision: str,
        context: dict[str, Any],
        consequence: Optional[str] = None,
    ):
        """
        Log a routing decision.

        Args:
            stage: Pipeline stage (e.g., "PLAN.Stage0", "BUILD.Stage3.implementer")
            layer: Which layer made the decision
            decision: Human-readable description (e.g., "route_agentic")
            context: Details (e.g., {"flag": "--apply", "confidence": 0.92})
            consequence: What changed because of this decision
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "stage": stage,
            "layer": layer,
            "decision": decision,
            "context": context,
            "consequence": consequence,
        }
        self.decisions.append(entry)
        self._write_to_file(entry)

    def _write_to_file(self, entry: dict):
        """Append entry to JSONL file (immediate write for real-time introspection)."""
        with open(self.output_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def emit_summary(self) -> dict:
        """Emit routing summary for human inspection."""
        if not self.decisions:
            return {"summary": "no routing decisions recorded"}

        by_layer = {}
        by_stage = {}
        for d in self.decisions:
            layer = d["layer"]
            stage = d["stage"]
            by_layer[layer] = by_layer.get(layer, 0) + 1
            by_stage[stage] = by_stage.get(stage, 0) + 1

        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": datetime.now().isoformat(),
            "total_decisions": len(self.decisions),
            "by_layer": by_layer,
            "by_stage": by_stage,
            "trace_file": str(self.output_file),
        }


def get_or_create_trace(session_id: str, project_root: str) -> RoutingTrace:
    """Retrieve or create routing trace for this session."""
    return RoutingTrace(session_id, project_root)


if __name__ == "__main__":
    # Example: python routing_trace.py --init <session-id> <project-root>
    if len(sys.argv) < 3:
        print("Usage: routing_trace.py --init <session-id> <project-root>")
        sys.exit(1)

    if sys.argv[1] == "--init":
        session_id = sys.argv[2]
        project_root = sys.argv[3]
        trace = get_or_create_trace(session_id, project_root)
        summary = trace.emit_summary()
        print(json.dumps(summary, indent=2))
