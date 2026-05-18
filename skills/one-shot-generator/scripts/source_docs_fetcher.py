#!/usr/bin/env python3
"""
Source Docs Fetcher — v1.0.0  (Stage 2.3 — Source-Driven Development)

The implementer agents emit code from training data + body_hints. For
post-cutoff API changes (Pydantic v2, FastAPI 0.110+ Annotated deps,
Django 5.x ORM tweaks, Spring Boot 3.x jakarta.* package rename, etc.)
training data can be wrong.

This helper detects the *exact* framework version from the project's
dependency manifest, then emits an opinionated **doc-lookup plan**: a
JSON document listing which official-doc URLs the orchestrator should
WebFetch BEFORE handing the spec to the implementer agents.

The orchestrator does the actual WebFetch calls (we don't from a
subprocess), then passes the doc excerpts into each implementer's
prompt context as "source-of-truth examples." This is the seam that
turns the plugin from "trust the training data" to "verify against
current docs."

Inspired by Addy Osmani's source-driven-development skill.

CLI:
    source_docs_fetcher.py --project <dir> [--features ...] [--json]

Outputs (JSON to stdout):
    {
      "framework": "fastapi",
      "detected_version": "0.115.6",
      "manifest": "requirements.txt",
      "lookups": [
        {
          "topic": "sqlalchemy_v2_orm",
          "why": "model emission uses Mapped[T] + mapped_column() syntax",
          "url": "https://docs.sqlalchemy.org/en/20/orm/quickstart.html",
          "anchor_keywords": ["Mapped", "mapped_column", "DeclarativeBase"]
        },
        ...
      ],
      "skip_reason": null     // populated if no version detected
    }

Exit codes:
    0   plan emitted
    1   bad args
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


# ─── Framework + manifest detection ─────────────────────────────────────────

# Order matters: more-specific manifests first (poetry/pdm before pip).
_MANIFEST_DETECTORS: List[Tuple[str, str]] = [
    ("pyproject.toml",    "python"),
    ("requirements.txt",  "python"),
    ("Pipfile",           "python"),
    ("pom.xml",           "java"),
    ("build.gradle",      "java"),
    ("build.gradle.kts",  "java"),
    ("package.json",      "node"),
    ("go.mod",            "go"),
]


# Framework signatures within each language. Tuple of (regex, framework_name).
_FRAMEWORK_PATTERNS: Dict[str, List[Tuple[re.Pattern, str]]] = {
    "python": [
        (re.compile(r"\bfastapi\b",  re.I), "fastapi"),
        (re.compile(r"\bdjango\b",   re.I), "django"),
    ],
    "java": [
        (re.compile(r"spring-boot", re.I), "spring"),
    ],
    "node": [
        (re.compile(r'"@nestjs/'),    "nestjs"),
        (re.compile(r'"express"'),    "nodejs"),
    ],
    "go": [
        (re.compile(r"github\.com/gin-gonic/gin"),  "go"),
        (re.compile(r"github\.com/labstack/echo"),  "go"),
        (re.compile(r"github\.com/go-chi/chi"),     "go"),
    ],
}


_VERSION_PATTERNS: Dict[str, re.Pattern] = {
    # pip-style: fastapi==0.115.6, fastapi>=0.110, fastapi~=0.115
    "fastapi": re.compile(r"fastapi\s*[=~><]+\s*(\d+\.\d+(?:\.\d+)?)", re.I),
    "django":  re.compile(r"django\s*[=~><]+\s*(\d+\.\d+(?:\.\d+)?)",  re.I),
    # pom.xml: <artifactId>spring-boot-...</artifactId><version>X.Y.Z</version>
    # Also matches build.gradle: 'org.springframework.boot' version '3.2.1'
    "spring":  re.compile(
        r"spring-boot[^>]*</artifactId>\s*<version>\s*(\d+\.\d+(?:\.\d+)?)"
        r"|spring(?:framework)?\.boot['\"]?\s+version\s+['\"](\d+\.\d+(?:\.\d+)?)",
        re.I,
    ),
    "nestjs":  re.compile(r'"@nestjs/core"\s*:\s*"\^?(\d+\.\d+\.\d+)"'),
    "nodejs":  re.compile(r'"express"\s*:\s*"\^?(\d+\.\d+\.\d+)"'),
    "go":      re.compile(r"^go\s+(\d+\.\d+)", re.M),
}


def _read_manifest(project: Path) -> Tuple[Optional[Path], Optional[str], Optional[str]]:
    """Return (manifest_path, manifest_content, language) for the first
    detector that hits, or (None, None, None) if nothing matches."""
    for filename, language in _MANIFEST_DETECTORS:
        path = project / filename
        if path.exists():
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            return path, content, language
    return None, None, None


def detect(project: Path) -> Dict[str, Optional[str]]:
    """Detect (framework, version, manifest_path). Best-effort —
    returns None fields when manifests are ambiguous or absent."""
    manifest_path, content, language = _read_manifest(project)
    if not (manifest_path and content and language):
        return {"framework": None, "version": None, "manifest": None,
                "skip_reason": "no_manifest_found"}

    framework: Optional[str] = None
    for pattern, name in _FRAMEWORK_PATTERNS.get(language, []):
        if pattern.search(content):
            framework = name
            break
    if framework is None:
        return {"framework": None, "version": None,
                "manifest": str(manifest_path.name),
                "skip_reason": "framework_not_recognised"}

    version: Optional[str] = None
    vp = _VERSION_PATTERNS.get(framework)
    if vp:
        m = vp.search(content)
        if m:
            # Some patterns have multiple capture groups (alternatives) —
            # pick the first non-None.
            for g in m.groups():
                if g:
                    version = g
                    break

    return {
        "framework": framework,
        "version": version,
        "manifest": str(manifest_path.name),
        "skip_reason": None if version else "version_pin_missing",
    }


# ─── Lookup catalogue ───────────────────────────────────────────────────────
#
# Per (framework, broad-version) → list of (topic, why, url, anchor_keywords).
# The orchestrator WebFetches each URL with a prompt like:
#     "Extract <anchor_keywords>; return idiomatic example signatures."
# and the result is appended to each implementer's prompt context.

def _fastapi_lookups(version: Optional[str]) -> List[Dict[str, object]]:
    # FastAPI 0.95+ uses Annotated[Depends]; SQLAlchemy 2.0+ uses Mapped[T]
    major, minor = _parse_minor(version)
    out: List[Dict[str, object]] = [
        {
            "topic": "fastapi_dependencies",
            "why": "router endpoints declare DB session + auth via Depends",
            "url": "https://fastapi.tiangolo.com/tutorial/dependencies/",
            "anchor_keywords": ["Depends", "Annotated", "Generator", "yield"],
        },
        {
            "topic": "pydantic_v2_models",
            "why": "schemas use Pydantic v2 model_config + Field syntax",
            "url": "https://docs.pydantic.dev/latest/concepts/models/",
            "anchor_keywords": ["model_config", "ConfigDict", "from_attributes", "Field"],
        },
        {
            "topic": "sqlalchemy_v2_orm",
            "why": "models use Mapped[T] + mapped_column() (SQLAlchemy 2.0 syntax)",
            "url": "https://docs.sqlalchemy.org/en/20/orm/quickstart.html",
            "anchor_keywords": ["Mapped", "mapped_column", "DeclarativeBase", "relationship"],
        },
    ]
    # Annotated-deps tutorial only correct on 0.95+
    if (major, minor) >= (0, 95):
        out.append({
            "topic": "fastapi_annotated_deps",
            "why": "Depends() now lives inside Annotated[T, Depends(...)] — pre-0.95 syntax breaks",
            "url": "https://fastapi.tiangolo.com/release-notes/#0950",
            "anchor_keywords": ["Annotated", "type alias", "DbSession"],
        })
    return out


def _django_lookups(version: Optional[str]) -> List[Dict[str, object]]:
    major, minor = _parse_minor(version)
    out: List[Dict[str, object]] = [
        {
            "topic": "drf_viewsets",
            "why": "router emits ModelViewSet — confirm permission_classes API",
            "url": "https://www.django-rest-framework.org/api-guide/viewsets/",
            "anchor_keywords": ["ModelViewSet", "permission_classes", "get_queryset"],
        },
        {
            "topic": "django_orm_async",
            "why": "Django 4.1+ supports async ORM (aget, acreate, ...)",
            "url": "https://docs.djangoproject.com/en/stable/topics/async/",
            "anchor_keywords": ["aget", "acreate", "asave", "aiter"],
        },
    ]
    if (major, minor) >= (5, 0):
        out.append({
            "topic": "django_v5_features",
            "why": "Django 5 adds GeneratedField + DB-default; surface if model uses computed cols",
            "url": "https://docs.djangoproject.com/en/5.0/releases/5.0/",
            "anchor_keywords": ["GeneratedField", "db_default", "Field"],
        })
    return out


def _spring_lookups(version: Optional[str]) -> List[Dict[str, object]]:
    major, _ = _parse_minor(version)
    out: List[Dict[str, object]] = [
        {
            "topic": "spring_boot_3_jakarta",
            "why": "Spring Boot 3 renamed javax.* → jakarta.* — imports break otherwise",
            "url": "https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.0-Migration-Guide",
            "anchor_keywords": ["jakarta.persistence", "jakarta.validation", "jakarta.servlet"],
        },
        {
            "topic": "spring_data_jpa",
            "why": "repository derived queries + @Modifying conventions",
            "url": "https://docs.spring.io/spring-data/jpa/reference/jpa/query-methods.html",
            "anchor_keywords": ["JpaRepository", "@Modifying", "@Query"],
        },
    ]
    if major >= 3:
        out.append({
            "topic": "spring_security_6",
            "why": "Spring Security 6 (bundled in Boot 3) deprecated WebSecurityConfigurerAdapter",
            "url": "https://docs.spring.io/spring-security/reference/migration-7/configuration.html",
            "anchor_keywords": ["SecurityFilterChain", "HttpSecurity", "@Bean"],
        })
    return out


def _nestjs_lookups(_: Optional[str]) -> List[Dict[str, object]]:
    return [
        {
            "topic": "nestjs_dependency_injection",
            "why": "module providers + custom providers (useFactory, useExisting)",
            "url": "https://docs.nestjs.com/fundamentals/custom-providers",
            "anchor_keywords": ["useFactory", "useExisting", "forwardRef"],
        },
        {
            "topic": "typeorm_v0_3",
            "why": "TypeORM 0.3 dropped Connection in favor of DataSource",
            "url": "https://typeorm.io/data-source",
            "anchor_keywords": ["DataSource", "initialize", "@InjectDataSource"],
        },
    ]


def _nodejs_lookups(_: Optional[str]) -> List[Dict[str, object]]:
    return [
        {
            "topic": "express_v5_router",
            "why": "Express 5 made async error handling automatic + dropped certain patterns",
            "url": "https://expressjs.com/en/guide/migrating-5.html",
            "anchor_keywords": ["asyncHandler", "app.del", "req.param"],
        },
        {
            "topic": "sequelize_v6_models",
            "why": "Sequelize 6 introduced Model.init class pattern + paranoid soft delete",
            "url": "https://sequelize.org/docs/v6/core-concepts/model-basics/",
            "anchor_keywords": ["Model.init", "paranoid", "DataTypes", "associations"],
        },
    ]


def _go_lookups(_: Optional[str]) -> List[Dict[str, object]]:
    return [
        {
            "topic": "gorm_v2_api",
            "why": "GORM v2 changed Session config + transaction patterns vs v1",
            "url": "https://gorm.io/docs/index.html",
            "anchor_keywords": ["gorm.Session", "Transaction", "WithContext"],
        },
        {
            "topic": "go_context_propagation",
            "why": "every repo/service method should accept ctx context.Context",
            "url": "https://pkg.go.dev/context",
            "anchor_keywords": ["context.Context", "WithCancel", "WithTimeout"],
        },
    ]


_LOOKUP_BUILDERS = {
    "fastapi": _fastapi_lookups,
    "django":  _django_lookups,
    "spring":  _spring_lookups,
    "nestjs":  _nestjs_lookups,
    "nodejs":  _nodejs_lookups,
    "go":      _go_lookups,
}


def _parse_minor(version: Optional[str]) -> Tuple[int, int]:
    if not version:
        return (0, 0)
    parts = version.split(".")
    try:
        return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
    except ValueError:
        return (0, 0)


# ─── Plan emission ──────────────────────────────────────────────────────────

def plan(project: Path, features: Optional[List[str]] = None) -> Dict:
    det = detect(project)
    framework = det["framework"]
    if not framework:
        return {
            "framework": None,
            "detected_version": det.get("version"),
            "manifest": det.get("manifest"),
            "lookups": [],
            "skip_reason": det.get("skip_reason") or "framework_not_recognised",
        }

    builder = _LOOKUP_BUILDERS.get(framework)
    lookups = builder(det["version"]) if builder else []

    # Filter by user-supplied feature keywords if provided. This is
    # deliberately lenient — substring match across topic + anchor_keywords.
    if features:
        f_lower = {f.lower() for f in features}
        def matches(l: Dict[str, object]) -> bool:
            blob = (str(l.get("topic", "")) + " " +
                    " ".join(str(k) for k in l.get("anchor_keywords", []))).lower()
            return any(f in blob for f in f_lower)
        lookups = [l for l in lookups if matches(l)] or lookups   # don't drop everything on miss

    return {
        "framework": framework,
        "detected_version": det["version"],
        "manifest": det["manifest"],
        "lookups": lookups,
        "skip_reason": det.get("skip_reason"),  # populated if version_pin_missing
    }


# ─── CLI ────────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Stage 2.3 — emit doc-lookup plan for source-driven implementer prompts."
    )
    p.add_argument("--project", required=True, type=Path,
                   help="Path to the target project (where the manifest lives).")
    p.add_argument("--features", nargs="*", default=None,
                   help="Optional feature keywords to filter lookups.")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.project.exists():
        print(f"project path not found: {args.project}", file=sys.stderr)
        return 1
    result = plan(args.project, args.features)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
