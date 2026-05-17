#!/usr/bin/env python3
"""
Promote Rule — Tier 6 self-improvement closer

Takes a candidate from `.beads/proposed_patch_rules.jsonl` and emits a
ready-to-paste auto_patch.py rule function. The output goes to stdout
(or to a file with --out); the human still reviews and merges manually
— this script just removes the mechanical part of going from
"observed fix" to "deployable patch rule."

Workflow:

  1. auto_rule_extractor scans git for fixes to generated files
  2. After N occurrences, the same trigger pattern accumulates
  3. User runs: promote_rule.py --rule-id rule-20260518-001
  4. Script emits a `_patch_<name>(file) -> Optional[PatchAction]` stub
     with the trigger regex + replacement, plus the dispatch entry to
     splice into auto_patch.py's `patch()` function.
  5. Human reviews, tightens the regex if needed, merges.

CLI:
    python promote_rule.py --rule-id rule-20260518-001
    python promote_rule.py --rule-id ... --out skills/one-shot-generator/scripts/patches/P5_my_rule.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
from pathlib import Path
from typing import Dict, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


PROPOSALS_PATH = Path(".beads/proposed_patch_rules.jsonl")


def _load_candidate(repo_root: Path, rule_id: str) -> Optional[Dict]:
    path = repo_root / PROPOSALS_PATH
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if data.get("id") == rule_id:
            return data
    return None


def _sanitize_name(rule_id: str) -> str:
    # rule-20260518-001 → rule_20260518_001
    return re.sub(r"[^a-zA-Z0-9]+", "_", rule_id).strip("_")


def emit_rule_stub(candidate: Dict, rule_letter: str = "P5") -> str:
    name = _sanitize_name(candidate["id"])
    trigger = candidate["trigger_pattern"]
    replacement = candidate["replacement_template"]
    occurrences = candidate.get("occurrences", 1)
    sample = candidate.get("sample_files", [])[:3]

    # The trigger has already been re.escape()'d by the extractor, so
    # it's safe to interpolate directly. The replacement is literal.
    return textwrap.dedent(f'''
        # ─── Rule {rule_letter} — auto-promoted from candidate {candidate["id"]} ─

        # Observed {occurrences} time(s) in: {", ".join(sample) or "(no samples recorded)"}
        # Trigger pattern (regex, already escaped):
        #   {trigger[:80]}{"…" if len(trigger) > 80 else ""}
        # Replacement template:
        #   {replacement[:80]}{"…" if len(replacement) > 80 else ""}

        _RULE_{rule_letter}_TRIGGER = re.compile(
            r"""{trigger}""",
            re.MULTILINE,
        )

        _RULE_{rule_letter}_REPLACEMENT = """{replacement}"""


        def _patch_{name}(file: Path) -> Optional[PatchAction]:
            """{rule_letter} — {candidate["id"]}: auto-promoted rule.

            Review-required: confirm the regex doesn't over-match
            before merging this into the active patch dispatcher.
            """
            text = file.read_text(encoding="utf-8")
            new_text, count = _RULE_{rule_letter}_TRIGGER.subn(
                _RULE_{rule_letter}_REPLACEMENT, text)
            if not count:
                return None
            file.write_text(new_text, encoding="utf-8")
            return PatchAction(
                file=file.name,
                rule="{rule_letter}",
                description="auto-promoted from {candidate["id"]}",
            )


        # To activate, add to the dispatch in patch():
        #     for path in sandbox_path.rglob("*.py"):
        #         action = _patch_{name}(path)
        #         if action:
        #             report.actions.append(action)
    ''').strip() + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Promote a candidate rule into a ready-to-paste auto_patch.py stub"
    )
    parser.add_argument("--rule-id", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--rule-letter", default="P5",
                        help="The new rule's code letter (default: P5)")
    parser.add_argument("--out", default=None,
                        help="Write the stub to this file (default: stdout)")
    parser.add_argument("--mark-promoted", action="store_true",
                        help="Also call auto_rule_extractor promote on success")
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    cand = _load_candidate(repo, args.rule_id)
    if not cand:
        print(f"no candidate found with id {args.rule_id}", file=sys.stderr)
        sys.exit(1)

    stub = emit_rule_stub(cand, rule_letter=args.rule_letter)

    if args.out:
        Path(args.out).write_text(stub, encoding="utf-8")
        print(f"wrote stub to {args.out}", file=sys.stderr)
    else:
        print(stub)

    if args.mark_promoted:
        # Mark as promoted in proposals.jsonl
        import subprocess
        subprocess.run(
            [sys.executable,
             str(repo / "skills" / "one-shot-generator" / "scripts"
                 / "auto_rule_extractor.py"),
             "promote", "--rule-id", args.rule_id,
             "--repo-root", str(repo)],
            check=True,
        )

    print(
        "\nNext steps:\n"
        "  1. Review the regex — auto_rule_extractor uses re.escape() on\n"
        "     the original text, so the trigger is literal. Loosen the\n"
        "     regex if you want it to generalise.\n"
        "  2. Paste the stub into skills/one-shot-generator/scripts/auto_patch.py.\n"
        "  3. Add the patch dispatch in patch() (one line — see the\n"
        "     'To activate' comment in the stub).\n"
        "  4. Add a test in tests/test_tier2_pipeline.py exercising the\n"
        "     new rule on a sample fixture.\n",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
