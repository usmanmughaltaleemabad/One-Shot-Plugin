#!/usr/bin/env python3
"""
Phase 4 HIPAA: Health Insurance Portability & Accountability Act

HIPAA (US): Protects health information (PHI).

Requirements:
- Privacy Rule: How PHI can be used/disclosed
- Security Rule: Safeguard PHI with technical/administrative/physical controls
- Breach Notification Rule: Notify patients if data exposed
- Enforcement Rule: HHS audits + fines

PHI: Any health info that identifies individual
- Medical records, billing, diagnoses, treatment, genetic info, etc.

Implementation:
- Audit controls (logging all access to PHI)
- Encryption (data at rest, in transit)
- Access controls (role-based, minimum necessary)
- Integrity controls (verify data not altered)
- Transmission security (TLS, VPN)
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta


def generate_hipaa_audit_logging() -> str:
    """Generate HIPAA-specific audit logging."""

    audit = '''
class HIPAAAccessLog:
    """
    HIPAA Audit Controls: Log all PHI access.

    Must record:
    - WHO accessed data (user ID)
    - WHAT was accessed (record ID, field)
    - WHEN (timestamp)
    - WHY (purpose: treatment, payment, operations)
    - HOW (system that accessed)
    """

    def __init__(self):
        self._access_log = []

    def log_phi_access(
        self,
        user_id: str,
        record_id: str,
        phi_field: str,
        purpose: str,  # treatment, payment, operations
        system: str
    ) -> None:
        """Log access to Protected Health Information"""
        self._access_log.append({
            "user_id": user_id,
            "record_id": record_id,
            "phi_field": phi_field,
            "purpose": purpose,
            "system": system,
            "timestamp": datetime.utcnow().isoformat(),
            "access_granted": True
        })

    def log_denied_access(
        self,
        user_id: str,
        record_id: str,
        reason: str
    ) -> None:
        """Log denied access attempt"""
        self._access_log.append({
            "user_id": user_id,
            "record_id": record_id,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "access_granted": False
        })

    def get_access_log_for_record(self, record_id: str) -> List[Dict]:
        """Get all access to specific patient record"""
        return [e for e in self._access_log if e["record_id"] == record_id]

    def export_for_audit(self) -> List[Dict]:
        """Export log for HIPAA audit"""
        return self._access_log.copy()
'''

    return audit


def generate_hipaa_minimum_necessary() -> str:
    """Generate minimum necessary principle enforcement."""

    minimum = '''
class MinimumNecessaryPrinciple:
    """
    HIPAA Minimum Necessary: Use only PHI needed for purpose.

    If treating patient: access diagnosis + treatment
    Don't access: family health history, genetic testing (unless relevant)

    Enforcement:
    - Role-based access (doctor can access, HR cannot)
    - Field-level encryption (can't see password in logs)
    - Request logging (why was this record accessed)
    """

    def __init__(self):
        self._role_permissions = {}  # role → accessible_phi_fields
        self._access_requests = []

    def set_role_permissions(self, role: str, phi_fields: List[str]) -> None:
        """Define what PHI fields role can access"""
        self._role_permissions[role] = set(phi_fields)

    def can_access(self, user_role: str, phi_field: str) -> bool:
        """Check if role can access this PHI field"""
        if user_role not in self._role_permissions:
            return False
        return phi_field in self._role_permissions[user_role]

    def request_access(
        self,
        user_id: str,
        user_role: str,
        record_id: str,
        phi_fields: List[str],
        purpose: str
    ) -> Dict:
        """Request access to PHI fields"""
        # Verify minimum necessary
        allowed_fields = self._role_permissions.get(user_role, set())
        requested_fields = set(phi_fields)
        unauthorized = requested_fields - allowed_fields

        if unauthorized:
            return {
                "approved": False,
                "reason": f"Unauthorized fields: {unauthorized}",
                "allowed_fields": list(allowed_fields & requested_fields)
            }

        self._access_requests.append({
            "user_id": user_id,
            "record_id": record_id,
            "phi_fields": phi_fields,
            "purpose": purpose,
            "timestamp": datetime.utcnow().isoformat()
        })

        return {
            "approved": True,
            "allowed_fields": list(requested_fields)
        }
'''

    return minimum


def generate_hipaa_system() -> dict:
    """Generate complete HIPAA compliance system."""

    imports = '''from typing import Dict, List, Optional
from datetime import datetime, timedelta


'''

    module_doc = '''"""
Phase 4 HIPAA: Health Information Protection

US healthcare regulation: Protects patient data.

HIPAA Rules:
1. PRIVACY RULE
   - Who can access patient health info
   - How to disclose (with authorization)
   - Patient rights (access own records, correct errors, list disclosures)

2. SECURITY RULE (Technical safeguards)
   - Encryption for data at rest (AES-256)
   - Encryption for data in transit (TLS 1.3)
   - Access controls (username/password + MFA)
   - Audit logs (who accessed what, when)

3. BREACH NOTIFICATION RULE
   - Unauthorized access = breach
   - Notify patients within 60 days
   - Notify HHS + media (if 500+ patients)
   - Minimum harm standard

Implementation:
- Audit logging: record ALL PHI access
- Minimum necessary: users only access what needed
- De-identification: remove identifiers for analytics
- Encryption: all PHI encrypted
- Business associates: vendors sign BAA (Business Associate Agreement)

Penalties:
- $100-$50,000 per violation
- $1.5M+ per year for pattern/practice
- Criminal penalties: up to $250k + 10 years prison
"""
'''

    audit = generate_hipaa_audit_logging()
    minimum = generate_hipaa_minimum_necessary()

    complete_code = imports + module_doc + "\n" + audit + "\n" + minimum

    return {
        "code": complete_code,
        "pattern": "HIPAA Compliance",
        "module": "phase4_hipaa_compliance.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate HIPAA compliance patterns")
    args = parser.parse_args()
    result = generate_hipaa_system()
    print(result["code"])


if __name__ == "__main__":
    main()
