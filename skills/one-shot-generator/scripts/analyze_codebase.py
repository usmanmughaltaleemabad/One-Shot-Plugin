#!/usr/bin/env python3
"""
Codebase Analyzer — v0.6.0-Foundation (Pieces #1 + #2)

Standalone script with zero external dependencies. Runs via ! injection in SKILL.md.
Detects: language, framework, patterns, conventions, dependencies, structure.
Outputs: compact context block <500 tokens for injection into generation prompt.

Usage: python analyze_codebase.py "add user auth endpoint @/path/to/project"
"""

import os
import sys
import re
from pathlib import Path

# Shared library imports
sys.path.insert(0, str(Path(__file__).parent))
from lib.base_script import __version__, setup_logging, timed_run

__version__ = "0.6.0"
logger = setup_logging(__name__)


# ─── Framework Detection ───────────────────────────────────────────────────────

PYTHON_FRAMEWORKS = {
    "django": ["django", "manage.py"],
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "starlette": ["starlette"],
}

JS_TS_FRAMEWORKS = {
    "nestjs": ["@nestjs/core"],
    "express": ["express"],
    "nextjs": ["next"],
    "fastify": ["fastify"],
}

JAVA_FRAMEWORKS = {
    "spring": ["spring-boot", "springframework"],
    "quarkus": ["quarkus"],
    "micronaut": ["micronaut"],
}

GO_FRAMEWORKS = {
    "gin": ['"github.com/gin-gonic/gin"'],
    "echo": ['"github.com/labstack/echo'],
    "fiber": ['"github.com/gofiber/fiber'],
    "go_stdlib": [],  # fallback
}

RUST_FRAMEWORKS = {
    "actix": ["actix-web"],
    "axum": ["axum"],
    "rocket": ["rocket"],
}

LOGGING_LIBRARIES = {
    "python": {
        "structlog": "structlog (structured)",
        "loguru": "loguru (structured)",
        "logging": "stdlib logging (formatted_string)",
    },
    "typescript": {
        "winston": "winston (structured)",
        "pino": "pino (structured)",
    },
    "go": {
        "zap": "uber-zap (structured)",
        "logrus": "logrus (structured)",
        "slog": "stdlib slog (structured)",
    },
}

VALIDATION_LIBRARIES = {
    "python": {
        "pydantic": "pydantic (class-based)",
        "marshmallow": "marshmallow (class-based)",
        "cerberus": "cerberus (schema-based)",
    },
    "typescript": {
        "zod": "zod (schema-based)",
        "joi": "joi (schema-based)",
        "class-validator": "class-validator (decorator-based)",
    },
}

TESTING_FRAMEWORKS = {
    "python": {
        "pytest": "pytest",
        "unittest": "unittest",
        "nose": "nose2",
    },
    "typescript": {
        "jest": "jest",
        "vitest": "vitest",
        "mocha": "mocha",
    },
    "go": {
        "testing": "stdlib testing + testify",
    },
    "java": {
        "junit": "JUnit 5",
        "testng": "TestNG",
    },
    "rust": {
        "#[test]": "cargo test (built-in)",
    },
}


# ─── Extraction Helpers ────────────────────────────────────────────────────────

def read_file_safe(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def detect_language_and_framework(project_path):
    p = Path(project_path)
    language = "unknown"
    framework = "unknown"
    version = ""
    orm = ""
    database = ""
    key_libs = []

    # Python
    req_file = p / "requirements.txt"
    pyproject = p / "pyproject.toml"
    setup_py = p / "setup.py"

    if req_file.exists() or pyproject.exists() or setup_py.exists():
        language = "python"
        deps_text = ""
        if req_file.exists():
            deps_text = read_file_safe(req_file).lower()
        elif pyproject.exists():
            deps_text = read_file_safe(pyproject).lower()

        for fw, markers in PYTHON_FRAMEWORKS.items():
            if any(m.lower() in deps_text for m in markers):
                framework = fw
                # extract version
                m = re.search(rf"{fw}[=~><!]+([0-9.]+)", deps_text)
                if m:
                    version = m.group(1)
                break

        if (p / "manage.py").exists() and framework == "unknown":
            framework = "django"

        # ORM detection
        if "django" in deps_text:
            orm = "Django ORM"
        elif "sqlalchemy" in deps_text:
            orm = "SQLAlchemy"
        elif "tortoise" in deps_text:
            orm = "Tortoise ORM"

        # DB detection
        if "psycopg" in deps_text or "postgresql" in deps_text:
            database = "PostgreSQL"
        elif "pymysql" in deps_text or "mysql" in deps_text:
            database = "MySQL"
        elif "sqlite" in deps_text:
            database = "SQLite"
        elif "motor" in deps_text or "pymongo" in deps_text:
            database = "MongoDB"

        # Key libs (top 5)
        lib_candidates = []
        for line in deps_text.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                name = re.split(r"[=~><!@]", line)[0].strip()
                if name and len(name) > 1:
                    lib_candidates.append(name)
        key_libs = lib_candidates[:5]

    # Go
    elif (p / "go.mod").exists():
        language = "go"
        go_mod = read_file_safe(p / "go.mod")
        framework = "go_stdlib"
        for fw, markers in GO_FRAMEWORKS.items():
            if fw == "go_stdlib":
                continue
            if any(m in go_mod for m in markers):
                framework = fw
                break
        # extract module name as key lib
        m = re.search(r"module\s+(\S+)", go_mod)
        if m:
            key_libs = [m.group(1).split("/")[-1]]

    # TypeScript / JavaScript
    elif (p / "package.json").exists():
        language = "typescript"
        pkg = read_file_safe(p / "package.json").lower()
        framework = "unknown"
        for fw, markers in JS_TS_FRAMEWORKS.items():
            if any(m.lower() in pkg for m in markers):
                framework = fw
                break
        # collect deps
        deps_match = re.findall(r'"(@?[a-z][a-z0-9/-]*)"\s*:', pkg)
        key_libs = [d for d in deps_match if d not in ["scripts", "dependencies", "devdependencies"]][:5]

    # Java
    elif (p / "pom.xml").exists() or (p / "build.gradle").exists():
        language = "java"
        pom = read_file_safe(p / "pom.xml") + read_file_safe(p / "build.gradle")
        framework = "unknown"
        for fw, markers in JAVA_FRAMEWORKS.items():
            if any(m.lower() in pom.lower() for m in markers):
                framework = fw
                break

    # Rust
    elif (p / "Cargo.toml").exists():
        language = "rust"
        cargo = read_file_safe(p / "Cargo.toml").lower()
        framework = "unknown"
        for fw, markers in RUST_FRAMEWORKS.items():
            if any(m.lower() in cargo for m in markers):
                framework = fw
                break

    return language, framework, version, orm, database, key_libs


def detect_patterns(project_path, language):
    p = Path(project_path)
    patterns = {}

    # Logging
    all_py = list(p.rglob("*.py"))[:20] if language == "python" else []
    all_ts = list(p.rglob("*.ts"))[:20] if language == "typescript" else []
    all_go = list(p.rglob("*.go"))[:20] if language == "go" else []
    source_files = all_py + all_ts + all_go

    combined = " ".join(read_file_safe(f) for f in source_files[:15])

    # Logging
    if language == "python":
        for lib, desc in LOGGING_LIBRARIES["python"].items():
            if f"import {lib}" in combined or f"from {lib}" in combined:
                patterns["logging"] = desc
                break
    elif language == "typescript":
        for lib, desc in LOGGING_LIBRARIES["typescript"].items():
            if lib in combined:
                patterns["logging"] = desc
                break
    elif language == "go":
        for lib, desc in LOGGING_LIBRARIES["go"].items():
            if lib in combined:
                patterns["logging"] = desc
                break

    # Validation
    if language == "python":
        for lib, desc in VALIDATION_LIBRARIES["python"].items():
            if lib in combined:
                patterns["validation"] = desc
                break
    elif language == "typescript":
        for lib, desc in VALIDATION_LIBRARIES["typescript"].items():
            if lib in combined:
                patterns["validation"] = desc
                break

    # Testing
    test_files = list(p.rglob("test_*.py")) + list(p.rglob("*_test.py")) + \
                 list(p.rglob("*.spec.ts")) + list(p.rglob("*_test.go"))
    if language in TESTING_FRAMEWORKS:
        test_combined = " ".join(read_file_safe(f) for f in test_files[:5])
        for lib, desc in TESTING_FRAMEWORKS[language].items():
            if lib in test_combined or (test_files and lib == "pytest" and language == "python"):
                patterns["testing"] = desc
                break

    # conftest location
    conftest = p / "tests" / "conftest.py"
    if conftest.exists():
        patterns["fixtures"] = "tests/conftest.py"

    # Error handling style
    if language == "python":
        if "class" in combined and "Exception" in combined:
            patterns["error_handling"] = "custom_exceptions"
        elif "try:" in combined:
            patterns["error_handling"] = "try/except"
    elif language == "go":
        if "if err != nil" in combined:
            patterns["error_handling"] = "explicit error returns"

    return patterns


def detect_conventions(project_path, language):
    conventions = {}
    if language == "python":
        conventions["naming"] = "snake_case functions, PascalCase classes, _ prefix private"
        conventions["type_hints"] = "required"
        # detect docstring style from source
        p = Path(project_path)
        sample = " ".join(read_file_safe(f) for f in list(p.rglob("*.py"))[:5])
        if "Args:" in sample and "Returns:" in sample:
            conventions["docstrings"] = "Google style"
        elif ":param" in sample:
            conventions["docstrings"] = "Sphinx style"
        else:
            conventions["docstrings"] = "minimal"
    elif language == "typescript":
        conventions["naming"] = "camelCase functions, PascalCase classes, _ prefix private"
        conventions["type_hints"] = "TypeScript types required"
    elif language == "go":
        conventions["naming"] = "camelCase private, PascalCase exported"
        conventions["type_hints"] = "explicit types"
    elif language == "java":
        conventions["naming"] = "camelCase methods, PascalCase classes"
        conventions["type_hints"] = "explicit types"
    elif language == "rust":
        conventions["naming"] = "snake_case functions, PascalCase types"
        conventions["type_hints"] = "explicit types"
    return conventions


def detect_structure(project_path):
    p = Path(project_path)
    structure = {}

    # App root
    for candidate in ["src", "app", "apps", "lib"]:
        if (p / candidate).is_dir():
            structure["app_root"] = candidate
            break

    # Test root
    for candidate in ["tests", "test", "spec", "__tests__"]:
        if (p / candidate).is_dir():
            structure["test_root"] = candidate
            break

    # Config root
    for candidate in ["config", "conf", "settings"]:
        if (p / candidate).is_dir():
            structure["config_root"] = candidate
            break

    # Migrations
    for pattern in ["**/migrations", "**/migrate"]:
        dirs = list(p.glob(pattern))
        if dirs:
            structure["migrations"] = str(dirs[0].relative_to(p))
            break

    # IaC / Deployment
    iac = []
    if (p / "Dockerfile").exists() or (p / "docker-compose.yml").exists():
        iac.append("Docker")
    if list(p.rglob("*.tf")):
        iac.append("Terraform")
    if list(p.rglob("*.yaml")) or list(p.rglob("*.yml")):
        k8s = [f for f in p.rglob("*.yaml") if "kind:" in read_file_safe(f)]
        if k8s:
            iac.append("Kubernetes")
    if (p / ".github" / "workflows").is_dir():
        iac.append("GitHub Actions")
    structure["iac"] = iac

    return structure


# ─── Output Formatting ─────────────────────────────────────────────────────────

def format_context(language, framework, version, orm, database, key_libs,
                   patterns, conventions, structure, task):
    lines = ["CODEBASE CONTEXT:"]

    # Language & Framework
    fw_display = framework.replace("_", " ").title()
    ver_display = f" {version}" if version else ""
    lines.append(f"Language: {language.title()} | Framework: {fw_display}{ver_display}")

    # Infrastructure
    infra = []
    if orm:
        infra.append(f"ORM: {orm}")
    if database:
        infra.append(f"Database: {database}")
    if infra:
        lines.append(" | ".join(infra))

    # Key libs
    if key_libs:
        lines.append(f"Key Libs: {', '.join(key_libs[:5])}")

    lines.append("")
    lines.append("PATTERNS:")

    if patterns.get("error_handling"):
        lines.append(f"- Error Handling: {patterns['error_handling']}")
    if patterns.get("logging"):
        lines.append(f"- Logging: {patterns['logging']}")
    if patterns.get("validation"):
        lines.append(f"- Validation: {patterns['validation']}")
    if patterns.get("testing"):
        fixture = patterns.get("fixtures", "")
        if fixture:
            lines.append(f"- Testing: {patterns['testing']} (fixtures at {fixture})")
        else:
            lines.append(f"- Testing: {patterns['testing']}")

    lines.append("")
    lines.append("CONVENTIONS:")
    if conventions.get("naming"):
        lines.append(f"- Naming: {conventions['naming']}")
    if conventions.get("docstrings") or conventions.get("type_hints"):
        doc = conventions.get("docstrings", "none")
        hints = conventions.get("type_hints", "optional")
        lines.append(f"- Docstrings: {doc} | Type Hints: {hints}")

    lines.append("")
    lines.append("STRUCTURE:")
    dirs = []
    if structure.get("app_root"):
        dirs.append(f"App: {structure['app_root']}/")
    if structure.get("test_root"):
        dirs.append(f"Tests: {structure['test_root']}/")
    if dirs:
        lines.append(f"- {' | '.join(dirs)}")
    if structure.get("config_root"):
        lines.append(f"- Config: {structure['config_root']}/")
    if structure.get("migrations"):
        lines.append(f"- Migrations: {structure['migrations']}/")
    if structure.get("iac"):
        lines.append(f"- IaC/CI: {', '.join(structure['iac'])}")

    if task:
        lines.append("")
        lines.append(f"TASK: {task}")

    return "\n".join(lines)


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    with timed_run("analyze_codebase") as timer:
        # Join all arguments into one string
        args_str = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""

        # Extract @path argument
        path_match = re.search(r"@(\S+)", args_str)
        if path_match:
            project_path = path_match.group(1)
            task = args_str[:path_match.start()].strip() + args_str[path_match.end():].strip()
            task = task.strip()
        else:
            project_path = os.getcwd()
            task = args_str.strip()

        # Normalize path
        project_path = os.path.expanduser(project_path)
        project_path = os.path.abspath(project_path)

        logger.debug(f"Analyzing project at: {project_path}")
        logger.debug(f"Task: {task}")

        if not os.path.isdir(project_path):
            logger.warning(f"Project path not found: {project_path}")
            print(f"CODEBASE CONTEXT:\nPath not found: {project_path}\nUsing manual mode — describe your stack in the task.\n\nTASK: {task}")
            return

        # Analyze
        logger.debug("Detecting language and framework...")
        language, framework, version, orm, database, key_libs = detect_language_and_framework(project_path)
        logger.debug(f"Detected: {language}/{framework} (v{version})")

        logger.debug("Detecting patterns...")
        patterns = detect_patterns(project_path, language)
        logger.debug("Detecting conventions...")
        conventions = detect_conventions(project_path, language)
        logger.debug("Analyzing structure...")
        structure = detect_structure(project_path)

        # Fallback defaults for testing
        if not patterns.get("testing") and language == "python":
            test_files = list(Path(project_path).rglob("test_*.py"))
            if test_files:
                patterns["testing"] = "pytest"

        output = format_context(language, framework, version, orm, database, key_libs,
                                patterns, conventions, structure, task)
        print(output)

    logger.debug(f"analyze_codebase completed in {timer.elapsed_ms:.0f}ms")


if __name__ == "__main__":
    main()
