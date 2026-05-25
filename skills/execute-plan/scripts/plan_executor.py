#!/usr/bin/env python3
"""
Skill: execute-plan
Plan Executor — Load and execute implementation plans task by task.

Input: Plan file (Markdown) or plan content
Output: Task list (JSON) + session state for resumable execution

Phases:
  1. load — Parse plan file, validate structure, return task list
  2. verify — Run a task's verify command, return pass/fail + output
  3. checkpoint — Mark task complete in session state
  4. resume — Read session state, return where to resume from

Session state persisted in .one-shot-execute-session.json at project root.
"""

import sys
import os
import re
import json
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

# Shared library imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent / ".." / ".." / ".." / "one-shot-generator" / "scripts"))

try:
    from lib.base_script import __version__, setup_logging, timed_run
except ImportError:
    # Fallback if lib not available
    __version__ = "1.0.0"
    def setup_logging(name, level=None):
        import logging
        logger = logging.getLogger(name)
        logger.setLevel(level or "WARNING")
        return logger

    from contextlib import contextmanager
    @contextmanager
    def timed_run(name):
        import time
        start = time.time()
        class Timer:
            elapsed_ms = 0
        timer = Timer()
        try:
            yield timer
        finally:
            timer.elapsed_ms = int((time.time() - start) * 1000)

__version__ = "1.0.0"
logger = setup_logging(__name__)


@dataclass
class Task:
    """Represents a single task from a plan."""
    task_id: int
    name: str
    goal: str
    file: str
    code: str
    verify_command: str
    checkpoint: str

    def to_dict(self) -> Dict:
        return asdict(self)


class PlanParser:
    """Parses Markdown plan files and extracts task structure."""

    # Markdown patterns for plan structure
    TASK_HEADER_PATTERN = r'^#### Task (\d+): (.+)$'
    FIELD_PATTERNS = {
        'goal': r'^\*\*Goal:\*\*\s+(.+)$',
        'file': r'^\*\*File:\*\*\s+(.+)$',
        'code': r'^\*\*Code:\*\*\s*\n```[\w]*\n([\s\S]*?)\n```',
        'verify': r'^\*\*Verify:\*\*\s+(.+)$',
        'checkpoint': r'^\*\*Checkpoint:\*\*\s+(.+)$',
    }

    def __init__(self, plan_text: str):
        self.plan_text = plan_text
        self.tasks: List[Task] = []

    def parse(self) -> Tuple[bool, List[Task], List[str]]:
        """Parse plan and return (success, tasks, errors)."""
        errors = []
        task_blocks = re.split(r'^#### Task \d+:', self.plan_text, flags=re.MULTILINE)[1:]

        for i, block in enumerate(task_blocks, 1):
            # Extract task number and name from first line
            lines = block.strip().split('\n')
            task_name_line = lines[0].strip()

            # Extract fields from this task block
            goal = self._extract_field(block, 'goal')
            file = self._extract_field(block, 'file')
            code = self._extract_field(block, 'code')
            verify = self._extract_field(block, 'verify')
            checkpoint = self._extract_field(block, 'checkpoint')

            # Validate required fields
            if not all([goal, file, code, verify, checkpoint]):
                missing = []
                if not goal: missing.append('Goal')
                if not file: missing.append('File')
                if not code: missing.append('Code')
                if not verify: missing.append('Verify')
                if not checkpoint: missing.append('Checkpoint')
                errors.append(f"Task {i}: Missing required fields: {', '.join(missing)}")
                continue

            # Check for placeholder text in code
            if re.search(r'(\.\.\.|TBD|\[placeholder\]|\[TODO\])', code, re.IGNORECASE):
                errors.append(f"Task {i}: Code contains placeholders — fix before executing")
                continue

            task = Task(
                task_id=i,
                name=task_name_line,
                goal=goal,
                file=file,
                code=code,
                verify_command=verify,
                checkpoint=checkpoint,
            )
            self.tasks.append(task)

        return len(errors) == 0, self.tasks, errors

    def _extract_field(self, block: str, field_name: str) -> str:
        """Extract a field value from a task block."""
        pattern = self.FIELD_PATTERNS.get(field_name, '')
        if not pattern:
            return ''

        match = re.search(pattern, block, re.MULTILINE | re.IGNORECASE)
        return match.group(1).strip() if match else ''


class SessionState:
    """Manages execution session state (persisted to JSON)."""

    SESSION_FILE = '.one-shot-execute-session.json'

    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root)
        self.session_file = self.project_root / self.SESSION_FILE
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load session from disk, or return empty state."""
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load session file: {e}. Starting fresh.")
                return self._empty_state()
        return self._empty_state()

    def _empty_state(self) -> Dict[str, Any]:
        """Return empty state template."""
        return {
            'plan_file': None,
            'total_tasks': 0,
            'completed_tasks': [],
            'current_task': 0,
            'status': 'not_started',  # not_started | running | paused | completed | failed
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'errors': [],
        }

    def start(self, plan_file: str, total_tasks: int):
        """Mark session as started with plan info."""
        self.data['plan_file'] = plan_file
        self.data['total_tasks'] = total_tasks
        self.data['status'] = 'running'
        self.data['current_task'] = 1 if total_tasks > 0 else 0
        self.data['updated_at'] = datetime.now().isoformat()
        self.save()

    def mark_complete(self, task_id: int):
        """Mark a task as completed."""
        if task_id not in self.data['completed_tasks']:
            self.data['completed_tasks'].append(task_id)
        self.data['current_task'] = task_id + 1
        self.data['updated_at'] = datetime.now().isoformat()
        self.save()

    def mark_paused(self, task_id: int, error: str = ''):
        """Pause execution at a task."""
        self.data['status'] = 'paused'
        self.data['current_task'] = task_id
        if error:
            self.data['errors'].append({'task': task_id, 'error': error, 'timestamp': datetime.now().isoformat()})
        self.data['updated_at'] = datetime.now().isoformat()
        self.save()

    def mark_completed(self):
        """Mark entire plan as completed."""
        self.data['status'] = 'completed'
        self.data['updated_at'] = datetime.now().isoformat()
        self.save()

    def save(self):
        """Write session state to disk."""
        try:
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.session_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save session: {e}")

    def get_resume_point(self) -> Tuple[int, List[int]]:
        """Return (next_task_id, completed_task_ids) for resuming."""
        return self.data['current_task'], self.data['completed_tasks']


class VerifyCommandRunner:
    """Runs a task's verify command and captures output."""

    def run(self, command: str, cwd: Optional[str] = None) -> Tuple[bool, str]:
        """
        Run a verify command safely.

        Uses shlex.split + shell=False to prevent shell injection from
        user-supplied plan file commands. Returns: (success: bool, output: str)
        """
        import shlex
        try:
            args = shlex.split(command)
            if not args:
                return False, "ERROR: empty command"
            result = subprocess.run(
                args,
                shell=False,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=cwd or '.',
            )
            output = result.stdout + result.stderr
            success = result.returncode == 0
            return success, output
        except subprocess.TimeoutExpired:
            return False, "TIMEOUT: Verify command took > 30 seconds"
        except Exception as e:
            return False, f"ERROR: {str(e)}"


def main():
    """CLI entry point for plan_executor."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Execute implementation plans task by task'
    )
    parser.add_argument('--phase', required=True,
                       choices=['load', 'verify', 'checkpoint', 'resume'],
                       help='Execution phase')
    parser.add_argument('--plan', default='', help='Plan file path or content')
    parser.add_argument('--task', type=int, help='Task ID (for verify/checkpoint)')
    parser.add_argument('--command', default='', help='Verify command to run')
    parser.add_argument('--cwd', default='.', help='Working directory for verify')

    args = parser.parse_args()

    with timed_run(f'plan_executor_{args.phase}'):
        if args.phase == 'load':
            result = phase_load(args.plan)
        elif args.phase == 'verify':
            result = phase_verify(args.task, args.command, args.cwd)
        elif args.phase == 'checkpoint':
            result = phase_checkpoint(args.task)
        elif args.phase == 'resume':
            result = phase_resume()
        else:
            result = {'error': 'Unknown phase'}

    print(json.dumps(result, indent=2))
    return 0 if 'error' not in result else 1


def phase_load(plan_input: str) -> Dict[str, Any]:
    """Load and parse a plan file."""
    try:
        # Determine if input is a file path or inline content
        plan_path = Path(plan_input)
        if plan_path.exists() and plan_path.is_file():
            with open(plan_path, 'r') as f:
                plan_text = f.read()
            plan_file = str(plan_path)
        else:
            # Assume it's inline content
            plan_text = plan_input
            plan_file = '<inline>'

        parser = PlanParser(plan_text)
        success, tasks, errors = parser.parse()

        if not success:
            return {
                'error': 'Plan validation failed',
                'errors': errors,
                'tasks': [],
            }

        # Initialize session state
        session = SessionState()
        session.start(plan_file, len(tasks))

        return {
            'success': True,
            'plan_file': plan_file,
            'total_tasks': len(tasks),
            'tasks': [t.to_dict() for t in tasks],
        }
    except Exception as e:
        return {'error': f'Failed to load plan: {str(e)}'}


def phase_verify(task_id: int, command: str, cwd: str) -> Dict[str, Any]:
    """Run a task's verify command."""
    try:
        if not task_id or not command:
            return {'error': 'task_id and command required'}

        runner = VerifyCommandRunner()
        passed, output = runner.run(command, cwd)

        return {
            'task_id': task_id,
            'passed': passed,
            'output': output,
        }
    except Exception as e:
        return {'error': f'Verify failed: {str(e)}'}


def phase_checkpoint(task_id: int) -> Dict[str, Any]:
    """Mark a task as completed."""
    try:
        if not task_id:
            return {'error': 'task_id required'}

        session = SessionState()
        session.mark_complete(task_id)

        return {
            'task_id': task_id,
            'marked_complete': True,
            'next_task': task_id + 1,
        }
    except Exception as e:
        return {'error': f'Checkpoint failed: {str(e)}'}


def phase_resume() -> Dict[str, Any]:
    """Read session state and return resume point."""
    try:
        session = SessionState()
        resume_task, completed = session.get_resume_point()

        return {
            'resume_at_task': resume_task,
            'completed_tasks': completed,
            'status': session.data['status'],
            'plan_file': session.data['plan_file'],
        }
    except Exception as e:
        return {'error': f'Resume failed: {str(e)}'}


if __name__ == '__main__':
    sys.exit(main())
