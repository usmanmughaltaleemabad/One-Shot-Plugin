#!/usr/bin/env python3
"""
Persistent Codebase Graph — v0.8.0

Wraps ``existing_codebase_scanner`` with on-disk persistence. The graph is
stored at ``<project>/.osp_codebase_graph.json`` and updated incrementally:

  * On first run for a project, a full scan is performed.
  * Subsequent runs check ``mtime`` of the manifest plus a sample of source
    files; if nothing has materially changed, the cached graph is returned.
  * Future sessions can read the cached graph in milliseconds, giving the
    generator a persistent semantic memory of the codebase.

This is the foundation for the "remember-what-you-generated-last-week"
feature without resorting to an embedded database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from lib.base_script import bootstrap_runtime, setup_logging
from existing_codebase_scanner import scan, CodebaseGraph
bootstrap_runtime()

logger = setup_logging(__name__)

GRAPH_FILENAME = ".osp_codebase_graph.json"


def _project_signature(project: Path) -> str:
    """Stable signature of the project's manifest + source mtimes.

    Used to decide whether the cached graph is still valid.
    """
    h = hashlib.sha256()
    for candidate in ("requirements.txt", "pyproject.toml", "package.json",
                      "go.mod", "pom.xml", "manage.py"):
        p = project / candidate
        if p.exists():
            try:
                h.update(p.read_bytes())
            except Exception:
                continue
    # Sample 50 .py files' mtimes (cheap stand-in for full hashing)
    py_files = list(project.rglob("*.py"))[:50]
    for p in py_files:
        try:
            h.update(str(p.stat().st_mtime_ns).encode())
            h.update(str(p).encode())
        except FileNotFoundError:
            continue
    return h.hexdigest()


def load_or_build(project: str | Path, *, force_rebuild: bool = False) -> CodebaseGraph:
    project_path = Path(project).expanduser().resolve()
    graph_file = project_path / GRAPH_FILENAME
    signature = _project_signature(project_path)

    if not force_rebuild and graph_file.exists():
        try:
            cached = json.loads(graph_file.read_text(encoding="utf-8"))
            if cached.get("_signature") == signature:
                logger.info("using cached codebase graph at %s", graph_file)
                return _graph_from_dict(cached["graph"])
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("cached graph unreadable (%s) — rebuilding", exc)

    graph = scan(project_path)
    payload = {"_signature": signature, "graph": graph.to_dict()}
    try:
        graph_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        logger.info("wrote codebase graph to %s", graph_file)
    except OSError as exc:
        logger.warning("could not persist codebase graph: %s", exc)
    return graph


def _graph_from_dict(data: dict) -> CodebaseGraph:
    """Reconstruct CodebaseGraph from its JSON form (round-trip safe)."""
    from existing_codebase_scanner import ExistingEntity, ExistingField, ImportRef
    entities = [
        ExistingEntity(
            name=e["name"],
            file=e["file"],
            kind=e["kind"],
            fields=[ExistingField(**f) for f in e["fields"]],
            base_classes=e.get("base_classes", []),
        )
        for e in data.get("entities", [])
    ]
    imports = {k: ImportRef(**v) for k, v in data.get("imports", {}).items()}
    return CodebaseGraph(
        project_path=data["project_path"],
        language=data["language"],
        framework=data["framework"],
        entities=entities,
        imports=imports,
        router_style=data.get("router_style"),
        test_layout=data.get("test_layout"),
        conventions=data.get("conventions", {}),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Load or rebuild the persistent codebase graph"
    )
    parser.add_argument("project", help="Project root path")
    parser.add_argument("--rebuild", action="store_true",
                        help="Ignore cache and rescan from scratch")
    parser.add_argument("--summary", action="store_true",
                        help="Print a one-page summary instead of full JSON")
    args = parser.parse_args()

    graph = load_or_build(args.project, force_rebuild=args.rebuild)
    if args.summary:
        print(f"CODEBASE GRAPH ({graph.project_path})")
        print(f"  {graph.language}/{graph.framework}   entities: {len(graph.entities)}   "
              f"router: {graph.router_style or '—'}")
        for ent in graph.entities[:15]:
            print(f"   • {ent.name:<22} [{ent.kind}]")
        if len(graph.entities) > 15:
            print(f"   … and {len(graph.entities) - 15} more")
        return
    print(json.dumps(graph.to_dict(), indent=2))


if __name__ == "__main__":
    main()
