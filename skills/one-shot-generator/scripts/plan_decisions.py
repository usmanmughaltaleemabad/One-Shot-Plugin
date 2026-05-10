#!/usr/bin/env python3
"""
Phase 0.1: Silent Planning Engine — Decision Scorer

Evaluates all major decisions WITHOUT asking user.
Scores each option 1-10, picks best, outputs JSON with reasoning.

Input: CODEBASE CONTEXT (from analyzer)
Output: JSON with 6 decisions (async, orm, testing, errors, logging, validation)

Usage: python plan_decisions.py < codebase_context.txt
"""

import sys
import json
import re
from typing import Dict, List, Tuple
from pathlib import Path

# Shared library imports
sys.path.insert(0, str(Path(__file__).parent))
from lib.base_script import __version__, setup_logging, timed_run

__version__ = "0.6.0"
logger = setup_logging(__name__)


class CodebaseAnalyzer:
    """Parse CODEBASE CONTEXT and extract key information."""

    def __init__(self, context_text: str):
        self.text = context_text
        self.frameworks = self._extract_frameworks()
        self.language = self._extract_language()
        self.key_libs = self._extract_key_libs()
        self.versions = self._extract_versions()
        self.patterns = self._extract_patterns()

    def _extract_frameworks(self) -> List[str]:
        """Extract detected frameworks from context."""
        frameworks = []
        if 'FastAPI' in self.text or 'fastapi' in self.text:
            frameworks.append('fastapi')
        if 'Django' in self.text or 'django' in self.text:
            frameworks.append('django')
        if 'Flask' in self.text or 'flask' in self.text:
            frameworks.append('flask')
        if 'Spring' in self.text or 'spring' in self.text:
            frameworks.append('spring')
        if 'NestJS' in self.text or 'nestjs' in self.text or '@nestjs/core' in self.text:
            frameworks.append('nestjs')
        if 'Express' in self.text or 'express' in self.text:
            frameworks.append('express')
        if 'Go' in self.text and ('main.go' in self.text or 'go.mod' in self.text):
            frameworks.append('go')
        # Also detect Go via lowercase indicators (dict-context format)
        text_lower = self.text.lower()
        if 'go' not in frameworks:
            go_signals = [
                'language: go',
                'framework: go',
                'has_go_mod',
                'go.mod',
                'main.go',
                'package_manager: go',
            ]
            if any(sig in text_lower for sig in go_signals):
                frameworks.append('go')
        return frameworks

    def _extract_language(self) -> str:
        """Extract primary language from context."""
        # First try explicit language declaration
        if 'Language:' in self.text:
            match = re.search(r'Language:\s*(\w+)', self.text)
            if match:
                return match.group(1).lower()

        # Detect by file extensions and frameworks
        text_lower = self.text.lower()

        if 'java' in text_lower or '.java' in text_lower:
            return 'java'
        if '.go' in text_lower or 'go' in self.frameworks:
            return 'go'
        if 'spring' in self.frameworks:
            return 'java'

        # Fallback: detect by Python frameworks
        if 'django' in self.frameworks or 'fastapi' in self.frameworks or 'flask' in self.frameworks:
            return 'python'
        if 'nestjs' in self.frameworks or 'express' in self.frameworks:
            return 'javascript'

        # Default to Python (most common)
        return 'python'

    def _extract_key_libs(self) -> List[str]:
        """Extract key libraries from context."""
        libs = []
        key_lib_patterns = [
            'sqlalchemy', 'django', 'fastapi', 'flask', 'pydantic', 'pytest',
            'jest', 'mocha', 'unittest', 'jpa', 'hibernate', 'spring',
            'structlog', 'loguru', 'winston', 'pino', 'zap', 'logrus',
            'requests', 'httpx', 'aiohttp', 'asyncio', 'nestjs', 'express',
            'nextjs', 'react', 'vue', 'zod', 'joi', 'marshmallow', 'cerberus',
            'log4j', 'junit', 'testify', 'validator'
        ]

        text_lower = self.text.lower()
        for lib in key_lib_patterns:
            if lib in text_lower:
                libs.append(lib)

        return libs

    def _extract_versions(self) -> Dict[str, str]:
        """Extract framework versions."""
        versions = {}

        # Django version
        match = re.search(r'Django\s+(\d+\.\d+)', self.text)
        if match:
            versions['django'] = match.group(1)

        # Python version
        match = re.search(r'Python\s+(\d+\.\d+)', self.text)
        if match:
            versions['python'] = match.group(1)

        return versions

    def _extract_patterns(self) -> Dict[str, List[str]]:
        """Extract coding patterns from context."""
        patterns = {
            'async': [],
            'sync': [],
            'orm': [],
            'raw_sql': [],
            'testing': []
        }

        text_lower = self.text.lower()

        # Async patterns
        if 'async def' in text_lower or 'async/' in text_lower or 'asyncio' in text_lower:
            patterns['async'].append('async/await detected')
        if 'await' in text_lower:
            patterns['async'].append('await keyword found')

        # Sync patterns (absence of async usually means sync)
        if 'def ' in text_lower and 'async def' not in text_lower:
            patterns['sync'].append('synchronous functions detected')

        # ORM patterns
        if 'sqlalchemy' in text_lower or 'django.db' in text_lower or 'jpa' in text_lower:
            patterns['orm'].append('ORM detected')
        if 'models.py' in text_lower or 'entity' in text_lower.lower():
            patterns['orm'].append('model files detected')

        # Raw SQL patterns
        if 'raw sql' in text_lower or 'sql(' in text_lower or '.sql' in text_lower:
            patterns['raw_sql'].append('raw SQL detected')
        if 'database/sql' in text_lower:
            patterns['raw_sql'].append('database/sql detected')

        # Testing patterns
        if 'pytest' in text_lower:
            patterns['testing'].append('pytest configured')
        if 'jest' in text_lower:
            patterns['testing'].append('Jest configured')
        if 'junit' in text_lower or 'junitplatform' in text_lower:
            patterns['testing'].append('JUnit configured')

        return patterns


def score_async_vs_sync(analyzer: CodebaseAnalyzer) -> Tuple[str, float, List[str]]:
    """Score async vs sync decision."""
    scores_async = []
    scores_sync = []

    # Framework detection
    if 'fastapi' in analyzer.frameworks:
        scores_async.append((9.0, 'FastAPI detected'))

    if 'django' in analyzer.frameworks:
        if 'django' in analyzer.versions:
            version = float(analyzer.versions['django'].split('.')[0])
            if version >= 3.1:
                scores_async.append((8.0, 'Django 3.1+ supports async'))
            else:
                scores_sync.append((9.0, 'Django < 3.1 (sync)'))
        else:
            scores_async.append((8.0, 'Django detected (assume modern)'))

    if 'nestjs' in analyzer.frameworks:
        scores_async.append((9.0, 'NestJS detected (async default)'))

    # Pattern detection
    if analyzer.patterns['async']:
        scores_async.append((8.0, 'Async code patterns detected'))
    if analyzer.patterns['sync']:
        scores_sync.append((8.0, 'Synchronous code patterns detected'))

    # Spring/Go/Express defaults
    if 'spring' in analyzer.frameworks or 'go' in analyzer.frameworks:
        scores_sync.append((9.0, 'Framework default: sync'))
    if 'express' in analyzer.frameworks:
        scores_sync.append((7.0, 'Express default: sync (async optional)'))

    # Fallback to sync
    if not scores_async and not scores_sync:
        scores_sync.append((5.0, 'No framework detected (fallback to sync)'))

    # Pick winner
    async_avg = sum(s[0] for s in scores_async) / len(scores_async) if scores_async else 0
    sync_avg = sum(s[0] for s in scores_sync) / len(scores_sync) if scores_sync else 0

    if async_avg >= sync_avg:
        choice_str = 'async'
        avg_score = async_avg if scores_async else 5.0
        reasons = [r for _, r in scores_async] if scores_async else ['Fallback: async']
    else:
        choice_str = 'sync'
        avg_score = sync_avg if scores_sync else 5.0
        reasons = [r for _, r in scores_sync] if scores_sync else ['Fallback: sync']

    return choice_str, avg_score, reasons


def score_orm_vs_sql(analyzer: CodebaseAnalyzer) -> Tuple[str, float, List[str]]:
    """Score ORM vs Raw SQL decision.

    Score semantics: high score (8-9) means "use an ORM"; low score (1-2)
    means "use raw SQL". This makes downstream comparisons (e.g., score >= 7
    => ORM) intuitive.
    """
    orm_signals = []
    raw_sql_signals = []

    text_lower = analyzer.text.lower()

    # Library detection
    if 'sqlalchemy' in analyzer.key_libs:
        orm_signals.append((9.0, 'SQLAlchemy detected', 'SQLAlchemy'))

    if 'django' in analyzer.frameworks:
        orm_signals.append((9.0, 'Django ORM detected', 'Django ORM'))

    if 'pydantic' in analyzer.key_libs:
        orm_signals.append((8.0, 'Pydantic models detected', 'Pydantic + ORM'))

    if 'jpa' in analyzer.key_libs or 'hibernate' in analyzer.key_libs:
        orm_signals.append((9.0, 'JPA/Hibernate detected', 'JPA'))

    # Pattern detection
    if analyzer.patterns['orm']:
        orm_signals.append((8.0, 'ORM patterns in code', 'ORM'))
    if analyzer.patterns['raw_sql']:
        raw_sql_signals.append((9.0, 'Raw SQL patterns in code', 'raw SQL'))

    # Framework defaults
    if 'spring' in analyzer.frameworks:
        orm_signals.append((9.0, 'Spring/JPA default', 'JPA'))

    if 'go' in analyzer.frameworks:
        raw_sql_signals.append((9.0, 'Go stdlib (raw SQL)', 'raw SQL'))

    # Explicit context hints (dict-format)
    if 'orm_type: raw_sql' in text_lower or 'orm_usage: false' in text_lower:
        raw_sql_signals.append((9.0, 'Context indicates raw SQL', 'raw SQL'))

    # Decide based on which side has stronger signal
    if raw_sql_signals and not orm_signals:
        # Pure raw-SQL: very low ORM score
        avg_conf = sum(s[0] for s in raw_sql_signals) / len(raw_sql_signals)
        # Map high confidence in raw SQL to a low ORM score (1-2)
        orm_score = max(1.0, 10.0 - avg_conf)
        choice_str = raw_sql_signals[0][2]
        reasons = [r for _, r, _ in raw_sql_signals]
        return choice_str, round(orm_score, 1), reasons

    if orm_signals and not raw_sql_signals:
        avg = sum(s[0] for s in orm_signals) / len(orm_signals)
        choice_str = orm_signals[0][2]
        reasons = [r for _, r, _ in orm_signals]
        return choice_str, round(avg, 1), reasons

    if orm_signals and raw_sql_signals:
        # Mixed: pick stronger side
        orm_avg = sum(s[0] for s in orm_signals) / len(orm_signals)
        raw_avg = sum(s[0] for s in raw_sql_signals) / len(raw_sql_signals)
        if orm_avg >= raw_avg:
            reasons = [r for _, r, _ in orm_signals]
            return orm_signals[0][2], round(orm_avg, 1), reasons
        else:
            reasons = [r for _, r, _ in raw_sql_signals]
            return raw_sql_signals[0][2], round(max(1.0, 10.0 - raw_avg), 1), reasons

    # Fallback: assume ORM at modest confidence
    return 'ORM', 7.0, ['No database library detected (default to ORM)']


def score_testing_framework(analyzer: CodebaseAnalyzer) -> Tuple[str, float, List[str]]:
    """Score testing framework decision."""
    scores = []
    choice_detail = None

    # Explicit configuration
    if 'pytest' in analyzer.key_libs:
        scores.append((9.0, 'pytest configured'))
        choice_detail = 'pytest'

    if 'jest' in analyzer.key_libs:
        scores.append((9.0, 'Jest configured'))
        choice_detail = 'Jest'

    if 'unittest' in analyzer.key_libs:
        scores.append((8.0, 'unittest configured'))
        if not choice_detail:
            choice_detail = 'unittest'

    # Framework defaults
    if 'django' in analyzer.frameworks:
        scores.append((9.0, 'Django community standard: pytest-django'))
        if not choice_detail:
            choice_detail = 'pytest-django'

    if 'fastapi' in analyzer.frameworks:
        scores.append((9.0, 'FastAPI community standard: pytest-asyncio'))
        if not choice_detail:
            choice_detail = 'pytest-asyncio'

    if 'spring' in analyzer.frameworks:
        scores.append((9.0, 'Spring standard: JUnit 5'))
        if not choice_detail:
            choice_detail = 'JUnit 5'

    if 'nestjs' in analyzer.frameworks:
        scores.append((9.0, 'NestJS standard: Jest'))
        if not choice_detail:
            choice_detail = 'Jest'

    if 'go' in analyzer.frameworks:
        scores.append((9.0, 'Go standard: testing + testify'))
        if not choice_detail:
            choice_detail = 'Go testing + testify'

    # Fallback by language
    if not scores:
        if analyzer.language == 'python':
            scores.append((7.0, 'Python default: pytest'))
            choice_detail = 'pytest'
        elif analyzer.language in ['javascript', 'typescript']:
            scores.append((7.0, 'JavaScript default: Jest'))
            choice_detail = 'Jest'
        elif analyzer.language == 'go':
            scores.append((7.0, 'Go default: testing'))
            choice_detail = 'testing'
        else:
            scores.append((5.0, 'Unknown language (default pytest)'))
            choice_detail = 'pytest'

    avg_score = sum(s[0] for s in scores) / len(scores)
    reasons = [r for _, r in scores]
    choice_str = choice_detail if choice_detail else 'pytest'

    return choice_str, avg_score, reasons


def score_error_handling(analyzer: CodebaseAnalyzer) -> Tuple[str, float, List[str]]:
    """Score error handling pattern decision."""
    scores = []

    # Language/framework defaults
    if analyzer.language == 'python' or 'django' in analyzer.frameworks or 'fastapi' in analyzer.frameworks:
        scores.append((8.0, 'Python convention: exceptions'))

    if analyzer.language == 'go':
        scores.append((9.0, 'Go convention: error returns'))

    if analyzer.language == 'java' or 'spring' in analyzer.frameworks:
        scores.append((9.0, 'Java convention: checked exceptions'))

    # Pattern detection
    if 'try:' in analyzer.text or 'try {' in analyzer.text or 'try/' in analyzer.text:
        scores.append((9.0, 'try/except pattern detected'))

    if 'error' in analyzer.text.lower() and 'return' in analyzer.text:
        scores.append((8.0, 'error return pattern detected'))

    # Fallback
    if not scores:
        if analyzer.language == 'python':
            scores.append((8.0, 'Python default: exceptions'))
        elif analyzer.language == 'go':
            scores.append((9.0, 'Go default: error returns'))
        else:
            scores.append((8.0, 'Default: exceptions'))

    avg_score = sum(s[0] for s in scores) / len(scores)
    reasons = [r for _, r in scores]
    choice_str = 'exceptions' if any('exception' in r.lower() for r in reasons) else 'error returns'

    return choice_str, avg_score, reasons


def score_logging_library(analyzer: CodebaseAnalyzer) -> Tuple[str, float, List[str]]:
    """Score logging library decision."""
    scores = []
    choice_detail = None

    # Python
    if analyzer.language == 'python':
        if 'structlog' in analyzer.key_libs:
            scores.append((9.0, 'structlog configured'))
            choice_detail = 'structlog'
        elif 'loguru' in analyzer.key_libs:
            scores.append((9.0, 'loguru configured'))
            choice_detail = 'loguru'
        elif 'logging' in analyzer.key_libs or 'stdlib logging' in analyzer.text:
            scores.append((8.0, 'stdlib logging detected'))
            choice_detail = 'stdlib logging'
        else:
            scores.append((7.0, 'Python default: structlog'))
            choice_detail = 'structlog'

    # JavaScript/TypeScript
    elif analyzer.language in ['javascript', 'typescript']:
        if 'winston' in analyzer.key_libs:
            scores.append((9.0, 'winston configured'))
            choice_detail = 'winston'
        elif 'pino' in analyzer.key_libs:
            scores.append((9.0, 'pino configured'))
            choice_detail = 'pino'
        else:
            scores.append((7.0, 'JavaScript default: winston'))
            choice_detail = 'winston'

    # Java
    elif analyzer.language == 'java':
        if 'log4j' in analyzer.key_libs:
            scores.append((9.0, 'Log4j 2 configured'))
            choice_detail = 'Log4j 2'
        elif 'logback' in analyzer.text.lower() or 'slf4j' in analyzer.text.lower():
            scores.append((9.0, 'Logback/SLF4J configured'))
            choice_detail = 'Logback'
        else:
            scores.append((8.0, 'Java default: Logback'))
            choice_detail = 'Logback'

    # Go
    elif analyzer.language == 'go':
        if 'zap' in analyzer.key_libs:
            scores.append((9.0, 'zap configured'))
            choice_detail = 'zap'
        elif 'logrus' in analyzer.key_libs:
            scores.append((9.0, 'logrus configured'))
            choice_detail = 'logrus'
        else:
            scores.append((7.0, 'Go default: zap'))
            choice_detail = 'zap'

    # Fallback
    if not scores:
        scores.append((5.0, 'No logging library detected'))
        choice_detail = 'structlog' if analyzer.language == 'python' else 'winston'

    avg_score = sum(s[0] for s in scores) / len(scores)
    reasons = [r for _, r in scores]
    choice_str = choice_detail if choice_detail else 'structlog'

    return choice_str, avg_score, reasons


def score_validation_library(analyzer: CodebaseAnalyzer) -> Tuple[str, float, List[str]]:
    """Score validation library decision."""
    scores = []
    choice_detail = None

    # Python
    if analyzer.language == 'python':
        if 'pydantic' in analyzer.key_libs:
            scores.append((9.0, 'Pydantic v2 detected'))
            choice_detail = 'Pydantic v2'
        elif 'marshmallow' in analyzer.key_libs:
            scores.append((9.0, 'Marshmallow detected'))
            choice_detail = 'Marshmallow'
        else:
            scores.append((8.0, 'Python default: Pydantic v2'))
            choice_detail = 'Pydantic v2'

    # JavaScript/TypeScript
    elif analyzer.language in ['javascript', 'typescript']:
        if 'zod' in analyzer.key_libs:
            scores.append((9.0, 'Zod detected'))
            choice_detail = 'Zod'
        elif 'joi' in analyzer.key_libs:
            scores.append((9.0, 'Joi detected'))
            choice_detail = 'Joi'
        elif 'class-validator' in analyzer.key_libs:
            scores.append((9.0, 'class-validator detected'))
            choice_detail = 'class-validator'
        else:
            scores.append((7.0, 'JavaScript default: Zod'))
            choice_detail = 'Zod'

    # Java
    elif analyzer.language == 'java':
        scores.append((9.0, 'Java standard: Bean Validation'))
        choice_detail = 'Bean Validation'

    # Go
    elif analyzer.language == 'go':
        if 'validator' in ' '.join(analyzer.key_libs):
            scores.append((9.0, 'go-playground/validator detected'))
            choice_detail = 'go-playground/validator'
        else:
            scores.append((6.0, 'Go: manual validation'))
            choice_detail = 'manual validation'

    # Fallback
    if not scores:
        scores.append((5.0, 'No validation library detected'))
        choice_detail = 'Pydantic v2'

    avg_score = sum(s[0] for s in scores) / len(scores)
    reasons = [r for _, r in scores]
    choice_str = choice_detail if choice_detail else 'Pydantic v2'

    return choice_str, avg_score, reasons


class PlanDecisionEngine:
    """Public API for silent planning engine."""

    def __init__(self, context):
        """Initialize with codebase context dict."""
        if isinstance(context, dict):
            # Convert dict to text format for analyzer
            context_text = self._dict_to_text(context)
        else:
            context_text = context
        self.analyzer = CodebaseAnalyzer(context_text)

    def _dict_to_text(self, context_dict) -> str:
        """Convert context dict to text format."""
        lines = []
        for key, value in context_dict.items():
            if isinstance(value, list):
                lines.append(f"{key}: {', '.join(str(v) for v in value)}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def score_all_decisions(self) -> Dict:
        """Score all 6 decisions and return as dict.

        Returns each decision under both its canonical key
        (async_sync / persistence / testing) and a friendly alias
        (async_decision / orm_decision / testing_framework) so callers can
        use whichever they prefer.
        """
        async_choice, async_score, async_reasons = score_async_vs_sync(self.analyzer)
        orm_choice, orm_score, orm_reasons = score_orm_vs_sql(self.analyzer)
        testing_choice, testing_score, testing_reasons = score_testing_framework(self.analyzer)
        errors_choice, errors_score, errors_reasons = score_error_handling(self.analyzer)
        logging_choice, logging_score, logging_reasons = score_logging_library(self.analyzer)
        validation_choice, validation_score, validation_reasons = score_validation_library(self.analyzer)

        async_block = {
            "choice": async_choice,
            "score": round(async_score, 1),
            "reasoning": async_reasons,
        }
        orm_block = {
            "choice": orm_choice,
            "score": round(orm_score, 1),
            "reasoning": orm_reasons,
        }
        testing_block = {
            "choice": testing_choice,
            "score": round(testing_score, 1),
            "reasoning": testing_reasons,
        }
        errors_block = {
            "choice": errors_choice,
            "score": round(errors_score, 1),
            "reasoning": errors_reasons,
        }
        logging_block = {
            "choice": logging_choice,
            "score": round(logging_score, 1),
            "reasoning": logging_reasons,
        }
        validation_block = {
            "choice": validation_choice,
            "score": round(validation_score, 1),
            "reasoning": validation_reasons,
        }

        return {
            # Canonical keys
            "async_sync": async_block,
            "persistence": orm_block,
            "testing": testing_block,
            "error_handling": errors_block,
            "logging": logging_block,
            "validation": validation_block,
            # Aliases for backward/test compatibility
            "async_decision": async_block,
            "orm_decision": orm_block,
            "testing_framework": testing_block,
            "error_decision": errors_block,
            "logging_decision": logging_block,
            "validation_decision": validation_block,
        }


def main():
    """Main entry point: read context, score all decisions, output JSON."""

    with timed_run("plan_decisions") as timer:
        # Read CODEBASE CONTEXT from stdin
        context_text = sys.stdin.read()
        logger.debug(f"Received context ({len(context_text)} chars)")

        # Parse context
        analyzer = CodebaseAnalyzer(context_text)

        # Score all 6 decisions
        logger.debug("Scoring async vs sync...")
        async_choice, async_score, async_reasons = score_async_vs_sync(analyzer)
        logger.debug(f"  → {async_choice} ({async_score:.1f})")

        logger.debug("Scoring persistence (ORM vs SQL)...")
        orm_choice, orm_score, orm_reasons = score_orm_vs_sql(analyzer)
        logger.debug(f"  → {orm_choice} ({orm_score:.1f})")

        logger.debug("Scoring testing framework...")
        testing_choice, testing_score, testing_reasons = score_testing_framework(analyzer)
        logger.debug(f"  → {testing_choice} ({testing_score:.1f})")

        logger.debug("Scoring error handling...")
        errors_choice, errors_score, errors_reasons = score_error_handling(analyzer)
        logger.debug(f"  → {errors_choice} ({errors_score:.1f})")

        logger.debug("Scoring logging library...")
        logging_choice, logging_score, logging_reasons = score_logging_library(analyzer)
        logger.debug(f"  → {logging_choice} ({logging_score:.1f})")

        logger.debug("Scoring validation library...")
        validation_choice, validation_score, validation_reasons = score_validation_library(analyzer)
        logger.debug(f"  → {validation_choice} ({validation_score:.1f})")

        # Build output
        decisions = {
            "async_sync": {
                "choice": async_choice,
                "score": round(async_score, 1),
                "reasoning": async_reasons
            },
            "persistence": {
                "choice": orm_choice,
                "score": round(orm_score, 1),
                "reasoning": orm_reasons
            },
            "testing": {
                "choice": testing_choice,
                "score": round(testing_score, 1),
                "reasoning": testing_reasons
            },
            "error_handling": {
                "choice": errors_choice,
                "score": round(errors_score, 1),
                "reasoning": errors_reasons
            },
            "logging": {
                "choice": logging_choice,
                "score": round(logging_score, 1),
                "reasoning": logging_reasons
            },
            "validation": {
                "choice": validation_choice,
                "score": round(validation_score, 1),
                "reasoning": validation_reasons
            }
        }

        # Output as JSON
        print(json.dumps(decisions, indent=2))

    logger.debug(f"plan_decisions completed in {timer.elapsed_ms:.0f}ms")


if __name__ == "__main__":
    main()
