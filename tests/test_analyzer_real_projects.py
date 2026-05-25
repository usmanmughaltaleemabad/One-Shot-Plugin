"""Tests for analyze_codebase.py against realistic project structures.

These tests use synthetic temp-dir projects that mimic the structure of
real external repos — they do NOT shell-clone anything (no network needed,
no long CI timeouts). Each fixture reproduces the exact file layout that
exposed the bug being tested.

Bug 1 — Monorepo blind spot (fastapi/full-stack-fastapi-template):
  Root pyproject.toml is a uv workspace definition with no [project]
  dependencies. The FastAPI app lives in backend/pyproject.toml.
  Previous behaviour: Framework: Unknown.
  Expected: Framework: fastapi, ORM: SQLModel, Database: PostgreSQL.

Bug 2 — TOML parsed as requirements.txt (key_libs garbage):
  pyproject.toml dependencies are quoted TOML strings. Requirements.txt
  parser turned them into noise like '[tool.uv.workspace]', 'members'.
  Expected: clean package names like ['fastapi', 'sqlmodel', 'pydantic'].
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ANALYZER = REPO_ROOT / "skills" / "one-shot-generator" / "scripts" / "analyze_codebase.py"


def _run_analyzer(project_path: Path, task: str) -> str:
    """Run the analyzer script and return stdout.

    Quotes the project path to handle paths with spaces (e.g. Windows user
    directories like 'Usman Mughal' — found in pytest's tmp_path on this
    machine and caught as a real bug in the analyzer's @(\\S+) regex).
    """
    result = subprocess.run(
        [sys.executable, str(ANALYZER), f'@"{project_path}" {task}'],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, f"Analyzer exited {result.returncode}: {result.stderr}"
    return result.stdout


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestMonorepoDetection:
    """Bug 1: root pyproject.toml is workspace file; real deps in backend/."""

    def test_fastapi_detected_in_backend_pyproject(self, tmp_path: Path) -> None:
        # Root workspace config — no [project] deps
        _write_file(tmp_path / "pyproject.toml", """
[tool.uv.workspace]
members = ["backend"]

[dependency-groups]
dev = ["pytest"]
""")
        # Backend has the real FastAPI app
        _write_file(tmp_path / "backend" / "pyproject.toml", """
[project]
name = "app"
dependencies = [
    "fastapi[standard]>=0.114.2",
    "pydantic>2.0",
    "sqlmodel>=0.0.21",
    "psycopg[binary]>=3.1.13",
    "alembic>=1.12.1",
]
""")
        output = _run_analyzer(tmp_path, "add rate limiting per user")
        assert "fastapi" in output.lower(), f"FastAPI not detected. Output:\n{output}"
        assert "unknown" not in output.lower().split("framework")[1][:30], \
            f"Framework Unknown after fix. Output:\n{output}"

    def test_orm_detected_from_backend_pyproject(self, tmp_path: Path) -> None:
        _write_file(tmp_path / "pyproject.toml", "[tool.uv.workspace]\nmembers = ['backend']\n")
        _write_file(tmp_path / "backend" / "pyproject.toml", """
[project]
dependencies = ["fastapi>=0.114.0", "sqlmodel>=0.0.21", "psycopg>=3.1.0"]
""")
        output = _run_analyzer(tmp_path, "add endpoint")
        assert "sqlmodel" in output.lower() or "sqlalchemy" in output.lower(), \
            f"ORM not detected. Output:\n{output}"

    def test_database_detected_from_backend_pyproject(self, tmp_path: Path) -> None:
        _write_file(tmp_path / "pyproject.toml", "[tool.uv.workspace]\nmembers = ['backend']\n")
        _write_file(tmp_path / "backend" / "pyproject.toml", """
[project]
dependencies = ["fastapi>=0.114.0", "psycopg[binary]>=3.1.13"]
""")
        output = _run_analyzer(tmp_path, "add endpoint")
        assert "postgresql" in output.lower(), f"PostgreSQL not detected. Output:\n{output}"

    def test_root_pyproject_without_subproject_still_works(self, tmp_path: Path) -> None:
        """If root has [project] deps, use them — no subdirectory search needed."""
        _write_file(tmp_path / "pyproject.toml", """
[project]
name = "my-api"
dependencies = ["django>=5.0", "psycopg2-binary>=2.9"]
""")
        output = _run_analyzer(tmp_path, "add endpoint")
        assert "django" in output.lower(), f"Django not detected from root. Output:\n{output}"


class TestKeyLibsExtraction:
    """Bug 2: TOML pyproject.toml parsed as requirements.txt → garbage in key_libs."""

    def test_no_toml_section_headers_in_key_libs(self, tmp_path: Path) -> None:
        _write_file(tmp_path / "pyproject.toml", """
[project]
name = "app"
dependencies = [
    "fastapi[standard]>=0.114.2",
    "pydantic>2.0",
    "sqlmodel>=0.0.21",
]

[tool.uv.workspace]
members = ["backend"]

[dependency-groups]
dev = ["pytest"]
""")
        output = _run_analyzer(tmp_path, "add feature")
        # TOML section names must not appear as key libs
        for noise in ("[tool.uv.workspace]", "members", "[dependency-groups]", "dev"):
            assert noise not in output, f"TOML noise '{noise}' appeared in output:\n{output}"

    def test_clean_package_names_from_toml(self, tmp_path: Path) -> None:
        _write_file(tmp_path / "pyproject.toml", """
[project]
dependencies = [
    "fastapi[standard]<1.0.0,>=0.114.2",
    "pydantic>2.0",
    "sqlmodel>=0.0.21",
    "alembic>=1.12.0",
]
""")
        output = _run_analyzer(tmp_path, "add feature")
        assert "fastapi" in output.lower(), f"fastapi not in key_libs. Output:\n{output}"
        assert "[standard]" not in output, f"extras bracket leaked into output:\n{output}"
        assert "pydantic" in output.lower(), f"pydantic not in key_libs. Output:\n{output}"

    def test_editable_install_not_in_key_libs(self, tmp_path: Path) -> None:
        _write_file(tmp_path / "requirements.txt", """
-e .[brotli,cli,http2,socks]
chardet>=3.0.4
httpx>=0.25.0
""")
        output = _run_analyzer(tmp_path, "add feature")
        assert "-e" not in output, f"Editable install marker in output:\n{output}"
        assert "brotli" not in output or "chardet" in output, f"Unexpected output:\n{output}"

    def test_requirements_txt_still_works(self, tmp_path: Path) -> None:
        """Ensure requirements.txt projects didn't regress."""
        _write_file(tmp_path / "requirements.txt", """
Django==5.0.3
psycopg2-binary==2.9.9
gunicorn==21.2.0
whitenoise==6.6.0
""")
        output = _run_analyzer(tmp_path, "add feature")
        assert "django" in output.lower(), f"Django not detected. Output:\n{output}"
        assert "gunicorn" in output.lower() or "whitenoise" in output.lower(), \
            f"Requirements.txt libs not extracted. Output:\n{output}"


class TestFrameworkDetection:
    """Regression tests for the three frameworks tested against real projects."""

    def test_fastapi_monorepo_end_to_end(self, tmp_path: Path) -> None:
        """Full structure mirroring tiangolo/full-stack-fastapi-template."""
        _write_file(tmp_path / "pyproject.toml", "[tool.uv.workspace]\nmembers = ['backend']\n")
        _write_file(tmp_path / "backend" / "app" / "main.py", "from fastapi import FastAPI\napp = FastAPI()\n")
        _write_file(tmp_path / "backend" / "pyproject.toml", """
[project]
dependencies = [
    "fastapi[standard]>=0.114.2",
    "sqlmodel>=0.0.21",
    "psycopg[binary]>=3.1.13",
    "pydantic>2.0",
    "alembic>=1.12.0",
    "pyjwt>=2.8.0",
]
""")
        output = _run_analyzer(tmp_path, "add per-user rate limiting using Redis")
        assert "fastapi" in output.lower()
        assert "postgresql" in output.lower()

    def test_django_requirements_txt_end_to_end(self, tmp_path: Path) -> None:
        """Full structure mirroring wsvincent/djangox."""
        _write_file(tmp_path / "requirements.txt", "Django==5.0.3\npsycopg2-binary==2.9.9\n")
        _write_file(tmp_path / "manage.py", "import django\n")
        output = _run_analyzer(tmp_path, "add user activity logging")
        assert "django" in output.lower()

    def test_pure_library_framework_unknown_is_ok(self, tmp_path: Path) -> None:
        """httpx is a library, not a framework — Unknown is correct."""
        _write_file(tmp_path / "requirements.txt", "chardet>=3.0\nhttpcore>=1.0\nanyio>=4.0\n")
        output = _run_analyzer(tmp_path, "add retry middleware")
        # Should detect Python language even without a framework
        assert "python" in output.lower()
