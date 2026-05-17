#!/usr/bin/env python3
"""
Phase 4 Compliance: GDPR Pattern

GDPR: General Data Protection Regulation (EU)

Requirements:
- Consent: get explicit consent before processing data
- Right to access: users can request their data
- Right to be forgotten: users can request deletion
- Data minimization: only collect what's needed
- Breach notification: notify users within 72 hours
- Privacy by design: security from the start

Implementation:
- Consent management (track what user agreed to)
- Data export (SAR - Subject Access Request)
- Data deletion (right to be forgotten)
- Audit logging (track all access)
- Encryption (data protection)
- Breach detection (alert on unauthorized access)

Usage:
    python phase4_gdpr_compliance.py --resource user-data

Input: Data resource type
Output: GDPR compliance patterns
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta


def generate_consent_manager() -> str:
    """Generate GDPR consent management."""

    consent = '''
class GDPRConsentManager:
    """
    Manage user consent for data processing.

    Requirements:
    - Explicit opt-in (not opt-out)
    - Record what user consented to
    - Record when they consented
    - Allow withdrawal anytime
    """

    def __init__(self):
        self._consents = {}  # user_id → {timestamp, purposes}

    def request_consent(
        self,
        user_id: str,
        purposes: List[str]
    ) -> Dict:
        """
        Request consent for specific purposes.

        Purposes: marketing, analytics, personalization, etc.
        """
        return {
            "user_id": user_id,
            "purposes": purposes,
            "message": f"We would like permission to process your data for: {', '.join(purposes)}",
            "timestamp": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat()
        }

    def record_consent(
        self,
        user_id: str,
        purposes: List[str],
        consent_given: bool
    ) -> None:
        """Record user's consent decision"""
        self._consents[user_id] = {
            "purposes": purposes,
            "consent_given": consent_given,
            "timestamp": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat()
        }

    def has_consent(self, user_id: str, purpose: str) -> bool:
        """Check if user consented to specific purpose"""
        if user_id not in self._consents:
            return False

        consent = self._consents[user_id]
        return consent.get("consent_given") and purpose in consent.get("purposes", [])

    def withdraw_consent(self, user_id: str) -> None:
        """User withdraws consent"""
        if user_id in self._consents:
            self._consents[user_id]["consent_given"] = False

    def get_user_consents(self, user_id: str) -> Optional[Dict]:
        """Get all consents for user"""
        return self._consents.get(user_id)
'''

    return consent


def generate_data_subject_rights() -> str:
    """Generate data subject rights."""

    rights = '''
class DataSubjectRights:
    """
    Implement GDPR data subject rights.

    1. Right to Access (SAR): User can request all their data
    2. Right to Erasure: User can request deletion
    3. Right to Rectification: User can correct inaccurate data
    4. Right to Restrict Processing: Limit how data is used
    5. Data Portability: Export data in standard format
    """

    def __init__(self, data_store):
        self.store = data_store
        self.sars = {}  # sar_id → request

    def request_subject_access(self, user_id: str) -> str:
        """Subject Access Request (SAR): User wants their data"""
        sar_id = f"sar-{user_id}-{datetime.utcnow().timestamp()}"

        self.sars[sar_id] = {
            "user_id": user_id,
            "requested_at": datetime.utcnow().isoformat(),
            "status": "pending",
            "deadline": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }

        return sar_id

    def fulfill_sar(self, sar_id: str) -> Dict:
        """Fulfill SAR: provide all user data"""
        sar = self.sars.get(sar_id)
        if not sar:
            return {}

        user_id = sar["user_id"]
        user_data = self.store.get_all_user_data(user_id)

        self.sars[sar_id]["status"] = "completed"
        self.sars[sar_id]["completed_at"] = datetime.utcnow().isoformat()

        return {
            "user_id": user_id,
            "data": user_data,
            "format": "JSON",
            "portable": True
        }

    def request_erasure(self, user_id: str) -> str:
        """Right to be forgotten: delete user data"""
        erasure_id = f"erase-{user_id}-{datetime.utcnow().timestamp()}"

        # Remove data
        self.store.delete_user_data(user_id)

        return erasure_id

    def request_rectification(self, user_id: str, corrections: Dict) -> None:
        """Right to rectification: fix inaccurate data"""
        self.store.update_user_data(user_id, corrections)
'''

    return rights


def generate_gdpr_audit_logging() -> str:
    """Generate GDPR audit logging."""

    audit = '''
class GDPRAuditLog:
    """
    Audit log for GDPR compliance.

    Log all data access and processing:
    - Who accessed what data
    - When
    - Why (purpose)
    - Result
    """

    def __init__(self):
        self._log = []

    def log_access(
        self,
        user_id: str,
        data_type: str,
        accessor: str,
        purpose: str
    ) -> None:
        """Log data access"""
        entry = {
            "user_id": user_id,
            "data_type": data_type,
            "accessor": accessor,
            "purpose": purpose,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._log.append(entry)

    def log_processing(
        self,
        user_id: str,
        processing_type: str,
        result: str
    ) -> None:
        """Log data processing"""
        entry = {
            "user_id": user_id,
            "processing_type": processing_type,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._log.append(entry)

    def get_user_access_log(self, user_id: str) -> List[Dict]:
        """Get all accesses to user data"""
        return [e for e in self._log if e.get("user_id") == user_id]

    def export_audit_log(self) -> List[Dict]:
        """Export full audit log (for regulatory review)"""
        return self._log.copy()
'''

    return audit


def generate_gdpr_system() -> dict:
    """Generate complete GDPR compliance system."""

    imports = '''from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


'''

    module_doc = '''"""
Phase 4 Compliance: GDPR Compliance Pattern

General Data Protection Regulation (EU/GDPR) requirements implementation.

Key GDPR Principles:

1. CONSENT
   - Get explicit opt-in (not opt-out)
   - Users must consent to specific purposes
   - Can withdraw anytime
   - Record what they consented to

2. DATA MINIMIZATION
   - Only collect what's needed
   - Delete when no longer needed
   - No "just in case" collection

3. DATA SUBJECT RIGHTS
   - Right to Access: users can request all their data (SAR)
   - Right to Erasure: users can request deletion
   - Right to Rectification: users can correct data
   - Right to Restrict: users can limit usage
   - Data Portability: export data

4. BREACH NOTIFICATION
   - Detect unauthorized access
   - Notify users within 72 hours
   - Log all incidents

5. PRIVACY BY DESIGN
   - Security from the start
   - Encryption for stored data
   - Encryption for transmitted data
   - Audit logging

Timeline:
- User creates account → request consent for specific purposes
- User can withdraw → stop all processing
- User requests SAR → provide all data within 30 days
- User requests erasure → delete within 30 days
- Data breach → notify within 72 hours

Example: E-commerce Site

User signup:
- "We'd like to send you marketing emails" (opt-in)
- "We'd like to process your payment" (required)
- "We'd like to improve our site with analytics" (optional)

User dashboard:
- "Download my data" (SAR)
- "Delete my account" (erasure)
- "Withdraw from marketing" (restrict processing)

Audit log:
- 2026-05-16 14:30: Payment processing for order #123
- 2026-05-16 14:31: Email sent to user
- 2026-05-16 14:35: User viewed their profile
"""
'''

    consent = generate_consent_manager()
    rights = generate_data_subject_rights()
    audit = generate_gdpr_audit_logging()

    complete_code = imports + module_doc + "\n" + consent + "\n" + rights + "\n" + audit

    return {
        "code": complete_code,
        "pattern": "GDPR Compliance",
        "module": "phase4_gdpr_compliance.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate GDPR compliance patterns")
    parser.add_argument("--resource", help="Data resource type")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_gdpr_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
