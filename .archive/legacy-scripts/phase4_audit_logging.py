#!/usr/bin/env python3
"""
Phase 4 Audit Logging: System-wide Activity Tracking

Audit log: Immutable record of all important actions.

Requirements:
- WHO: User or service that performed action
- WHAT: Action taken (create, modify, delete, access)
- WHEN: Timestamp (precise, UTC)
- WHERE: System/component where action occurred
- WHY: Purpose or reason code
- RESULT: Success or failure, with error code

Uses:
- Compliance: Prove you're following regulations
- Security: Detect suspicious activity
- Operations: Troubleshoot issues
- Forensics: Reconstruct what happened

Immutability: Audit logs cannot be modified or deleted.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime


def generate_audit_log_system() -> str:
    """Generate enterprise audit logging."""

    audit = '''
class AuditLog:
    """
    System-wide immutable audit log.

    Records: ALL actions that matter
    - Authentication (login success/failure)
    - Authorization (access granted/denied)
    - Data modification (create, update, delete)
    - Configuration changes (settings modified)
    - Admin actions (user added, role changed)
    """

    def __init__(self):
        self._log = []  # Append-only

    def log_action(
        self,
        action: str,
        actor: str,  # user_id or service_name
        resource: str,  # what was acted upon
        result: str,  # success, failure, denied
        details: Optional[Dict] = None,
        reason_code: Optional[str] = None
    ) -> str:
        """Log an action"""
        entry = {
            "id": f"audit-{len(self._log)}-{datetime.utcnow().timestamp()}",
            "action": action,
            "actor": actor,
            "resource": resource,
            "result": result,
            "details": details or {},
            "reason_code": reason_code,
            "timestamp": datetime.utcnow().isoformat(),
            "signature": self._compute_signature(action, actor, resource)
        }

        self._log.append(entry)
        return entry["id"]

    def _compute_signature(self, action: str, actor: str, resource: str) -> str:
        """Compute signature for tamper detection"""
        # In production: use HMAC-SHA256
        data = f"{action}:{actor}:{resource}"
        return hash(data) % 1000000

    def verify_integrity(self) -> bool:
        """Verify log hasn't been tampered with"""
        for i, entry in enumerate(self._log):
            expected_sig = self._compute_signature(
                entry["action"],
                entry["actor"],
                entry["resource"]
            )
            if entry["signature"] != expected_sig:
                return False  # Tampered!
        return True

    def query_by_action(self, action: str) -> List[Dict]:
        """Find all instances of action"""
        return [e for e in self._log if e["action"] == action]

    def query_by_actor(self, actor: str) -> List[Dict]:
        """Find all actions by actor"""
        return [e for e in self._log if e["actor"] == actor]

    def query_by_resource(self, resource: str) -> List[Dict]:
        """Find all actions on resource"""
        return [e for e in self._log if e["resource"] == resource]

    def query_by_result(self, result: str) -> List[Dict]:
        """Find all failed/denied actions"""
        return [e for e in self._log if e["result"] == result]

    def export_log(self) -> List[Dict]:
        """Export full audit log (for regulatory review)"""
        return [dict(e) for e in self._log]  # Return copy

    def get_log_size(self) -> int:
        """Get audit log size"""
        return len(self._log)
'''

    return audit


def generate_audit_retention() -> str:
    """Generate audit log retention policies."""

    retention = '''
class AuditLogRetention:
    """
    Manage audit log lifecycle.

    Retention rules:
    - Access logs: 1 year (regulatory requirement)
    - Change logs: 7 years (financial/legal holds)
    - Authentication: 90 days (security analysis)
    - Admin actions: 7 years (compliance)

    Never delete audit logs (immutability).
    Archive to cold storage after retention period.
    """

    def __init__(self):
        self._retention_rules = {}
        self._archived_logs = []

    def set_retention_rule(self, log_type: str, days: int) -> None:
        """Set how long to keep log type"""
        self._retention_rules[log_type] = days

    def archive_old_logs(self, log_type: str, before_date: str) -> int:
        """Move old logs to archive (cold storage)"""
        count = 0
        # In production: move to S3 Glacier or equivalent
        self._archived_logs.append({
            "log_type": log_type,
            "before_date": before_date,
            "archived_at": datetime.utcnow().isoformat(),
            "count": count
        })
        return count

    def retrieve_archived_logs(self, log_type: str, date_range: str) -> List[Dict]:
        """Retrieve archived logs (slow, from cold storage)"""
        # In production: query S3 or archive system
        return []
'''

    return retention


def generate_audit_system() -> dict:
    """Generate complete audit logging system."""

    imports = '''from typing import Dict, List, Optional, Any
from datetime import datetime


'''

    module_doc = '''"""
Phase 4 Audit Logging: Immutable Activity Records

System-wide audit trail for compliance, security, forensics.

WHAT TO LOG:
✓ Authentication: Login success/failure, MFA, password change
✓ Authorization: Access granted/denied, permission change
✓ Data changes: Create/update/delete records
✓ Configuration: Settings changed, policies modified
✓ Admin actions: Users added, roles changed, accounts deleted
✓ System: Backups, migrations, deployments

WHAT NOT TO LOG:
✗ Passwords: Never log plaintext passwords
✗ Credit cards: Never log sensitive data
✗ Health info: Never log unless necessary

REQUIREMENTS:
1. IMMUTABLE: Cannot modify or delete logs
2. PRECISE: Accurate timestamps (UTC, with microseconds)
3. COMPLETE: Capture full context (who, what, when, why, result)
4. SEARCHABLE: Query by actor, action, resource, date
5. VERIFIED: Signatures to detect tampering
6. RETAINED: Keep per regulatory requirements
7. ACCESSIBLE: Provide to auditors, investigators

AUDIT QUERIES:
- "What did user_123 do?" → query_by_actor()
- "Who accessed customer_456?" → query_by_resource()
- "What failed actions happened today?" → query_by_result()
- "Give me login attempts on 2026-05-16" → query_by_action()

COMPLIANCE:
- GDPR: Article 32 requires audit logging
- HIPAA: CFR 164.312(b) requires audit controls
- PCI DSS: Requirement 10 requires audit logs
- SOC 2: CC7 requires access logging
- FINRA: Rules require transaction logging
"""
'''

    audit = generate_audit_log_system()
    retention = generate_audit_retention()

    complete_code = imports + module_doc + "\n" + audit + "\n" + retention

    return {
        "code": complete_code,
        "pattern": "Audit Logging System",
        "module": "phase4_audit_logging.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate audit logging system")
    args = parser.parse_args()
    result = generate_audit_system()
    print(result["code"])


if __name__ == "__main__":
    main()
