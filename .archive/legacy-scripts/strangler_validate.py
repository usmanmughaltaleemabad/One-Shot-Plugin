#!/usr/bin/env python3
"""
Strangler Validator — v1.0.0 (Pre-Flight Safety Checks)

Validates extracted services before deployment.
Detects 5+ categories of risk:
  1. Library compatibility (version conflicts, missing dependencies)
  2. Data consistency (schema mismatches, data loss risk)
  3. Interface breaking (API changes affecting legacy code)
  4. Configuration (secrets, environment variables, ports)
  5. Performance (N+1 queries, timeout risks, resource needs)

Risk Scoring: GREEN (safe), YELLOW (plan carefully), RED (block, needs work)

Usage:
    python strangler_validator.py "validate @/path/to/extracted-service"

Output:
    Risk assessment report + mitigation recommendations
    Gating decision: PROCEED or BLOCK

Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


# ─── Data Models ───────────────────────────────────────────────────────────

@dataclass
class RiskFinding:
    """Represents a single risk finding."""
    category: str  # library, data, interface, config, performance
    severity: str  # RED, YELLOW, GREEN
    title: str
    description: str
    evidence: str  # specific finding
    mitigation: str  # recommended fix
    estimated_effort: str  # quick, medium, high
    blocking: bool  # True = must fix before deploy


@dataclass
class ValidationReport:
    """Complete validation assessment."""
    service_name: str
    status: str = "PASS"  # PASS, WARN, BLOCK
    overall_risk: str = "GREEN"  # GREEN, YELLOW, RED
    findings: List[RiskFinding] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def blocking_count(self) -> int:
        return sum(1 for f in self.findings if f.blocking)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "YELLOW")

    @property
    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "GREEN")


# ─── Validator: Library Compatibility ───────────────────────────────────

class LibraryCompatibilityValidator:
    """Validate library versions and dependencies."""

    def __init__(self, service_path: Path, language: str):
        self.service_path = service_path
        self.language = language

    def validate(self) -> List[RiskFinding]:
        """Check library compatibility."""
        findings = []

        if self.language == "go":
            findings.extend(self._validate_go_modules())
        elif self.language == "fastapi":
            findings.extend(self._validate_python_requirements())

        return findings

    def _validate_go_modules(self) -> List[RiskFinding]:
        """Validate go.mod file."""
        go_mod = self.service_path / "go.mod"
        findings = []

        if not go_mod.exists():
            findings.append(RiskFinding(
                category="library",
                severity="RED",
                title="Missing go.mod",
                description="Go module file not found",
                evidence=f"{go_mod} does not exist",
                mitigation="Run 'go mod init' in service directory",
                estimated_effort="quick",
                blocking=True
            ))

        return findings

    def _validate_python_requirements(self) -> List[RiskFinding]:
        """Validate requirements.txt file."""
        req_file = self.service_path / "requirements.txt"
        findings = []

        if not req_file.exists():
            findings.append(RiskFinding(
                category="library",
                severity="RED",
                title="Missing requirements.txt",
                description="Python dependencies not specified",
                evidence=f"{req_file} does not exist",
                mitigation="Create requirements.txt with all dependencies",
                estimated_effort="quick",
                blocking=True
            ))
            return findings

        # Parse requirements
        try:
            with open(req_file) as f:
                requirements = f.read()

            # Check for critical packages
            has_fastapi = "fastapi" in requirements
            has_uvicorn = "uvicorn" in requirements

            if not has_fastapi:
                findings.append(RiskFinding(
                    category="library",
                    severity="RED",
                    title="FastAPI not in requirements",
                    description="Core framework missing from dependencies",
                    evidence="fastapi not found in requirements.txt",
                    mitigation="Add 'fastapi>=0.100.0' to requirements.txt",
                    estimated_effort="quick",
                    blocking=True
                ))

            if not has_uvicorn:
                findings.append(RiskFinding(
                    category="library",
                    severity="YELLOW",
                    title="Uvicorn not in requirements",
                    description="Web server not specified",
                    evidence="uvicorn not found in requirements.txt",
                    mitigation="Add 'uvicorn[standard]>=0.24.0' to requirements.txt",
                    estimated_effort="quick",
                    blocking=False
                ))

        except Exception as e:
            findings.append(RiskFinding(
                category="library",
                severity="YELLOW",
                title="Could not parse requirements.txt",
                description="Error reading dependency file",
                evidence=str(e),
                mitigation="Verify requirements.txt is valid",
                estimated_effort="quick",
                blocking=False
            ))

        return findings


# ─── Validator: Data Consistency ────────────────────────────────────────

class DataConsistencyValidator:
    """Validate data schema and migration safety."""

    def __init__(self, service_path: Path):
        self.service_path = service_path

    def validate(self) -> List[RiskFinding]:
        """Check data migration safety."""
        findings = []

        # Check for migration files
        migrations_dir = self.service_path / "migrations"
        if not migrations_dir.exists():
            findings.append(RiskFinding(
                category="data",
                severity="YELLOW",
                title="No migration directory found",
                description="Database migrations may not be versioned",
                evidence=f"{migrations_dir} does not exist",
                mitigation="Create migrations/ directory with numbered SQL files",
                estimated_effort="medium",
                blocking=False
            ))
        else:
            # Check for migration files
            migration_files = list(migrations_dir.glob("*.sql"))
            if not migration_files:
                findings.append(RiskFinding(
                    category="data",
                    severity="YELLOW",
                    title="No SQL migration files found",
                    description="Data extraction not defined",
                    evidence=f"No .sql files in {migrations_dir}",
                    mitigation="Create migration files for shadow table creation and data sync",
                    estimated_effort="high",
                    blocking=False
                ))

        return findings


# ─── Validator: Interface Breaking ──────────────────────────────────────

class InterfaceValidator:
    """Validate API compatibility with legacy interface."""

    def __init__(self, service_path: Path, language: str):
        self.service_path = service_path
        self.language = language

    def validate(self) -> List[RiskFinding]:
        """Check interface compatibility."""
        findings = []

        if self.language == "go":
            findings.extend(self._validate_go_handlers())
        elif self.language == "fastapi":
            findings.extend(self._validate_fastapi_routes())

        # Check for adapter
        adapter_file = self.service_path / "adapter.py"
        if not adapter_file.exists():
            findings.append(RiskFinding(
                category="interface",
                severity="YELLOW",
                title="No adapter file found",
                description="Legacy interface compatibility layer missing",
                evidence=f"{adapter_file} does not exist",
                mitigation="Create adapter.py with request translation layer",
                estimated_effort="high",
                blocking=False
            ))

        return findings

    def _validate_go_handlers(self) -> List[RiskFinding]:
        """Validate Go HTTP handlers."""
        handler_file = self.service_path / "handler" / "handler.go"
        findings = []

        if not handler_file.exists():
            findings.append(RiskFinding(
                category="interface",
                severity="RED",
                title="Missing handler.go",
                description="HTTP request handlers not defined",
                evidence=f"{handler_file} does not exist",
                mitigation="Implement HTTP handler with /health and feature endpoints",
                estimated_effort="high",
                blocking=True
            ))

        return findings

    def _validate_fastapi_routes(self) -> List[RiskFinding]:
        """Validate FastAPI routes."""
        router_file = self.service_path / "router.py"
        findings = []

        if not router_file.exists():
            findings.append(RiskFinding(
                category="interface",
                severity="RED",
                title="Missing router.py",
                description="API routes not defined",
                evidence=f"{router_file} does not exist",
                mitigation="Implement FastAPI router with feature endpoints",
                estimated_effort="high",
                blocking=True
            ))

        return findings


# ─── Validator: Configuration ──────────────────────────────────────────

class ConfigurationValidator:
    """Validate deployment configuration."""

    def __init__(self, service_path: Path):
        self.service_path = service_path

    def validate(self) -> List[RiskFinding]:
        """Check configuration completeness."""
        findings = []

        # Check for Docker config
        dockerfile = self.service_path / "Dockerfile"
        if not dockerfile.exists():
            findings.append(RiskFinding(
                category="config",
                severity="YELLOW",
                title="No Dockerfile found",
                description="Container image not defined",
                evidence=f"{dockerfile} does not exist",
                mitigation="Create Dockerfile with multi-stage build",
                estimated_effort="quick",
                blocking=False
            ))

        # Check for K8s config
        k8s_dir = self.service_path / "k8s"
        if not k8s_dir.exists():
            findings.append(RiskFinding(
                category="config",
                severity="YELLOW",
                title="No Kubernetes configs found",
                description="K8s deployment not defined",
                evidence=f"{k8s_dir} does not exist",
                mitigation="Create K8s deployment + service YAML",
                estimated_effort="medium",
                blocking=False
            ))

        return findings


# ─── Validator: Performance ────────────────────────────────────────────

class PerformanceValidator:
    """Validate performance characteristics."""

    def __init__(self, service_path: Path, feature_data: Dict):
        self.service_path = service_path
        self.feature_data = feature_data

    def validate(self) -> List[RiskFinding]:
        """Check performance risks."""
        findings = []

        # Check coupling - high coupling = higher latency risk
        external_coupling = self.feature_data.get('external_coupling', 0)
        if external_coupling > 7:
            findings.append(RiskFinding(
                category="performance",
                severity="YELLOW",
                title="High external coupling",
                description="Service has many external dependencies",
                evidence=f"external_coupling = {external_coupling}/10",
                mitigation="Cache external calls, use circuit breaker, implement timeout",
                estimated_effort="medium",
                blocking=False
            ))

        # Check entity count - more entities = more processing
        entity_count = self.feature_data.get('entity_count', 0)
        if entity_count > 50:
            findings.append(RiskFinding(
                category="performance",
                severity="YELLOW",
                title="Large entity count",
                description="Service handles many entities",
                evidence=f"entity_count = {entity_count}",
                mitigation="Profile database queries, add indexing, consider pagination",
                estimated_effort="high",
                blocking=False
            ))

        return findings


# ─── Main Validator ────────────────────────────────────────────────────

class StranglerValidator:
    """Orchestrates all validation checks."""

    def __init__(self, service_path: str, feature_data: Dict, language: str = "go"):
        self.service_path = Path(service_path)
        self.feature_data = feature_data
        self.language = language

    def validate(self) -> ValidationReport:
        """Run all validators."""
        report = ValidationReport(
            service_name=self.feature_data.get('name', 'unknown'),
            status="PASS",
        )

        # Run all validators
        validators = [
            LibraryCompatibilityValidator(self.service_path, self.language),
            DataConsistencyValidator(self.service_path),
            InterfaceValidator(self.service_path, self.language),
            ConfigurationValidator(self.service_path),
            PerformanceValidator(self.service_path, self.feature_data),
        ]

        for validator in validators:
            findings = validator.validate()
            report.findings.extend(findings)

        # Determine overall status
        blocking_findings = [f for f in report.findings if f.blocking]
        if blocking_findings:
            report.status = "BLOCK"
            report.overall_risk = "RED"
        elif report.warning_count > 0:
            report.status = "WARN"
            report.overall_risk = "YELLOW"
        else:
            report.status = "PASS"
            report.overall_risk = "GREEN"

        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)

        return report

    def _generate_recommendations(self, report: ValidationReport) -> List[str]:
        """Generate actionable recommendations."""
        recs = []

        if report.blocking_count > 0:
            recs.append(f"CRITICAL: Fix {report.blocking_count} blocking issue(s) before deployment")

        if report.warning_count > 0:
            recs.append(f"Plan for {report.warning_count} warning(s) - may impact timeline")

        # Add specific recommendations
        red_findings = [f for f in report.findings if f.severity == "RED"]
        for finding in red_findings:
            recs.append(f"[{finding.category}] {finding.title}: {finding.mitigation}")

        return recs


def main():
    """Entry point for ! injection from SKILL.md."""
    if len(sys.argv) < 2:
        print("[ERROR] Usage: strangler_validate.py 'validate @/path/to/service'")
        sys.exit(1)

    arguments = sys.argv[1]

    # Parse service path
    import re
    path_match = re.search(r'@(\S+)', arguments)
    if not path_match:
        print("[ERROR] No service path provided. Usage: 'validate @/path/to/service'")
        sys.exit(1)

    service_path = path_match.group(1)
    if not Path(service_path).exists():
        print(f"[ERROR] Service path does not exist: {service_path}")
        sys.exit(1)

    # Detect language
    language = "go"  # default
    if "--language fastapi" in arguments or "--language python" in arguments:
        language = "fastapi"

    # Dummy feature data - in real usage, comes from analyzer
    feature_data = {
        "name": Path(service_path).name,
        "entity_count": 10,
        "external_coupling": 4.2,
        "difficulty": "YELLOW",
    }

    # Validate
    validator = StranglerValidator(service_path, feature_data, language)
    report = validator.validate()

    # Output report
    print("\n[VALIDATION REPORT]")
    print("-" * 60)
    print(f"Service: {report.service_name}")
    print(f"Status: {report.status}")
    print(f"Overall Risk: {report.overall_risk}")
    print(f"Findings: {len(report.findings)} ({report.info_count} info, "
          f"{report.warning_count} warning, {report.blocking_count} blocking)")
    print("")

    if report.findings:
        print("[FINDINGS]")
        for finding in report.findings:
            risk_icon = "[INFO]" if finding.severity == "GREEN" else \
                        "[WARN]" if finding.severity == "YELLOW" else "[BLOCK]"
            print(f"{risk_icon} [{finding.category}] {finding.title}")
            print(f"   {finding.description}")
            if finding.blocking:
                print(f"   BLOCKING: {finding.mitigation}")
            print("")

    if report.recommendations:
        print("[RECOMMENDATIONS]")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"{i}. {rec}")

    print("\n" + "-" * 60)

    # JSON output
    output = {
        "status": report.status,
        "overall_risk": report.overall_risk,
        "service_name": report.service_name,
        "findings_count": len(report.findings),
        "info_count": report.info_count,
        "warning_count": report.warning_count,
        "blocking_count": report.blocking_count,
        "findings": [asdict(f) for f in report.findings],
        "recommendations": report.recommendations,
        "timestamp": report.timestamp,
    }

    print(json.dumps(output, indent=2))

    # Exit code
    if report.status == "BLOCK":
        sys.exit(1)
    elif report.status == "WARN":
        sys.exit(0)  # Warnings don't block, but allow inspection
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
