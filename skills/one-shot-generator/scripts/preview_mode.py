#!/usr/bin/env python3
"""
v0.9.5: Dual-Mode Workflow — Optional Preview-First

A user can pass ``--preview`` to see a structured outline (file list, key
decisions, integration time estimate) BEFORE the full multi-file response
is produced. Default behaviour stays flow-first; preview is an opt-in
safety rail for enterprise procurement / cautious users.

Public API:
    preview = PreviewBuilder(framework='fastapi')
    text = preview.build(
        feature='Rate limiter',
        files=[{'name': 'rate_limiter.py', 'loc': 180}, ...],
        decisions=[('Algorithm', 'sliding window'), ...],
        estimated_minutes=17,
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class PreviewFile:
    name: str
    loc: int
    purpose: str = ''


class PreviewBuilder:
    """Builds the structured preview block."""

    def __init__(self, framework: str = 'fastapi'):
        self.framework = framework.lower()

    def build(self,
              feature: str,
              files: List[Dict],
              decisions: List[Tuple[str, str]],
              estimated_minutes: int = 0) -> str:
        out = []
        out.append(f"## PREVIEW — `{feature}`\n")
        out.append("This is what will be generated. Run again without `--preview` to commit.\n")

        out.append("### File structure")
        out.append("```")
        for f in files:
            pf = self._coerce(f)
            tag = f" — {pf.purpose}" if pf.purpose else ""
            out.append(f"- {pf.name} ({pf.loc} LOC){tag}")
        out.append("```\n")

        out.append("### Key decisions")
        for label, value in decisions:
            out.append(f"- **{label}:** {value}")
        out.append("")

        if estimated_minutes:
            out.append("### Estimated integration time")
            out.append(f"- ~{estimated_minutes} minutes (read + wire + run tests)\n")

        out.append("### Continue?")
        out.append("- ✅  Rerun the same prompt without `--preview` to generate everything.")
        out.append("- ✏️  Adjust the prompt (e.g., `--token-bucket` instead of sliding window) and rerun preview.")
        out.append("- ❌  Stop here.\n")
        return "\n".join(out)

    @staticmethod
    def _coerce(f) -> PreviewFile:
        if isinstance(f, PreviewFile):
            return f
        return PreviewFile(
            name=f.get('name', 'unknown'),
            loc=int(f.get('loc', 0)),
            purpose=f.get('purpose', ''),
        )


def main():
    pb = PreviewBuilder()
    print(pb.build(
        feature='Rate limiter',
        files=[
            {'name': 'rate_limiter.py', 'loc': 180, 'purpose': 'core algorithm + bus glue'},
            {'name': 'tests/test_rate_limiter.py', 'loc': 220, 'purpose': 'edge cases + integration'},
            {'name': 'README.md', 'loc': 140, 'purpose': 'usage + tuning notes'},
        ],
        decisions=[
            ('Algorithm', 'sliding window log'),
            ('Storage', 'in-memory dict (replace with Redis for distributed)'),
            ('Failure mode', 'drop excess + emit `rate.exceeded`'),
        ],
        estimated_minutes=17,
    ))


if __name__ == '__main__':
    main()
