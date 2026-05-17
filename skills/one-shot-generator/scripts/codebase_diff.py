#!/usr/bin/env python3
"""
Codebase Diff Tracker — v1.0.0  (Tier 3 incremental memory)

Computes the delta between the cached ``CodebaseGraph`` and the current
state of the project. Used to keep the persistent graph cheap to refresh
between sessions and to let the orchestrator say::

    "Since last run you added Product.barcode and a new module 'returns/'.
     I'll factor those in before generating."

Output JSON:

    {
        "project": "/path/to/proj",
        "added":   ["returns/models.py"],
        "removed": ["legacy/scratch.py"],
        "modified": [{"file": "models.py", "new_classes": ["Tax"], "new_fields": {"Product": ["barcode"]}}],
        "signature_unchanged": false
    }

CLI:
    python codebase_diff.py <project>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from lib.base_script import bootstrap_runtime, setup_logging
from existing_codebase_scanner import scan, CodebaseGraph
from codebase_graph import (
    GRAPH_FILENAME, _project_signature, _graph_from_dict,
)
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Data shapes ─────────────────────────────────────────────────────────────

@dataclass
class FileModification:
    file: str
    new_classes: List[str] = field(default_factory=list)
    removed_classes: List[str] = field(default_factory=list)
    new_fields: Dict[str, List[str]] = field(default_factory=dict)
    removed_fields: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DiffReport:
    project: str
    signature_unchanged: bool
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    modified: List[FileModification] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict:
        return {
            "project": self.project,
            "signature_unchanged": self.signature_unchanged,
            "added": self.added,
            "removed": self.removed,
            "modified": [m.to_dict() for m in self.modified],
            "summary": self.summary,
        }


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _entities_by_file(graph: CodebaseGraph) -> Dict[str, Dict[str, Set[str]]]:
    """Index { file_path: { class_name: {field_name, ...} } }."""
    out: Dict[str, Dict[str, Set[str]]] = {}
    for ent in graph.entities:
        per_file = out.setdefault(ent.file, {})
        per_file[ent.name] = {f.name for f in ent.fields}
    return out


def _files_in_graph(graph: CodebaseGraph) -> Set[str]:
    return {ent.file for ent in graph.entities}


# ─── Public entry ────────────────────────────────────────────────────────────

def diff(project_path: str | Path) -> DiffReport:
    project = Path(project_path).expanduser().resolve()
    graph_file = project / GRAPH_FILENAME
    current_signature = _project_signature(project)
    current_graph = scan(project)

    if not graph_file.exists():
        # No prior graph — everything is "added"
        added = sorted({ent.file for ent in current_graph.entities})
        return DiffReport(
            project=str(project),
            signature_unchanged=False,
            added=added,
            removed=[],
            modified=[],
            summary=f"no prior graph; recording {len(added)} entity file(s) as new",
        )

    cached = json.loads(graph_file.read_text(encoding="utf-8"))
    signature_unchanged = cached.get("_signature") == current_signature
    if signature_unchanged:
        return DiffReport(
            project=str(project),
            signature_unchanged=True,
            summary="project signature unchanged since last scan",
        )

    cached_graph = _graph_from_dict(cached["graph"])
    cur_by_file = _entities_by_file(current_graph)
    cached_by_file = _entities_by_file(cached_graph)
    cur_files = set(cur_by_file)
    cached_files = set(cached_by_file)

    added = sorted(cur_files - cached_files)
    removed = sorted(cached_files - cur_files)
    modified: List[FileModification] = []
    for file in sorted(cur_files & cached_files):
        cur_classes = cur_by_file[file]
        cached_classes = cached_by_file[file]
        new_classes = sorted(set(cur_classes) - set(cached_classes))
        removed_classes = sorted(set(cached_classes) - set(cur_classes))
        new_fields: Dict[str, List[str]] = {}
        removed_fields: Dict[str, List[str]] = {}
        for cls in set(cur_classes) & set(cached_classes):
            new = sorted(cur_classes[cls] - cached_classes[cls])
            gone = sorted(cached_classes[cls] - cur_classes[cls])
            if new:
                new_fields[cls] = new
            if gone:
                removed_fields[cls] = gone
        if new_classes or removed_classes or new_fields or removed_fields:
            modified.append(FileModification(
                file=file,
                new_classes=new_classes,
                removed_classes=removed_classes,
                new_fields=new_fields,
                removed_fields=removed_fields,
            ))

    parts = []
    if added:
        parts.append(f"{len(added)} added")
    if removed:
        parts.append(f"{len(removed)} removed")
    if modified:
        parts.append(f"{len(modified)} modified")
    summary = ", ".join(parts) or "no entity-level changes since last scan"

    return DiffReport(
        project=str(project),
        signature_unchanged=False,
        added=added,
        removed=removed,
        modified=modified,
        summary=summary,
    )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Show what changed in the codebase since the cached graph"
    )
    parser.add_argument("project", help="Project root path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = diff(args.project)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return
    print(f"CODEBASE DIFF — {report.project}")
    print(f"  {report.summary}")
    for f in report.added:
        print(f"  + {f}")
    for f in report.removed:
        print(f"  - {f}")
    for m in report.modified:
        print(f"  ~ {m.file}")
        for cls in m.new_classes:
            print(f"      + class {cls}")
        for cls in m.removed_classes:
            print(f"      - class {cls}")
        for cls, fields in m.new_fields.items():
            print(f"      ~ {cls}: + " + ", ".join(fields))
        for cls, fields in m.removed_fields.items():
            print(f"      ~ {cls}: - " + ", ".join(fields))


if __name__ == "__main__":
    main()
