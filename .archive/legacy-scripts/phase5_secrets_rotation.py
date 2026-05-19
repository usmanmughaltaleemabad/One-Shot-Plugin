#!/usr/bin/env python3
"""
Phase 5 Secrets Management: Automated Secret Rotation & Versioning

Secrets Rotation: Regularly change API keys, passwords, certificates.

Problem: Static secrets
- API key: never changed, in use for 5 years
- Database password: same across dev/staging/prod
- Certificate: expires (service breaks on expiry)
- Leak: compromised key affects all services

Rotation (solution):
- Automated rotation: change secrets periodically
- Versioning: multiple valid versions during transition
- Revocation: immediately disable compromised secret
- Audit: track all secret operations
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta


def generate_secrets_rotation() -> str:
    """Generate secrets rotation system."""

    rotation = '''
class SecretsManager:
    """
    Manage secrets with rotation, versioning, and revocation.

    Lifecycle:
    1. Create: generate secret
    2. Version: multiple versions active
    3. Rotate: generate new, retire old
    4. Revoke: disable compromised immediately
    """

    def __init__(self):
        self._secrets = {}  # secret_name → {versions: []}
        self._versions = {}  # version_id → {secret, created, status}
        self._rotations = []  # Rotation history
        self._audit_log = []  # All operations

    def create_secret(
        self,
        name: str,
        secret_value: str,
        rotation_period_days: int = 90
    ) -> str:
        """Create secret with rotation policy"""
        version_id = f"{name}-v1"

        self._secrets[name] = {
            "name": name,
            "rotation_period": rotation_period_days,
            "versions": [version_id],
            "current_version": version_id,
            "created_at": datetime.utcnow().isoformat()
        }

        self._versions[version_id] = {
            "id": version_id,
            "secret_name": name,
            "value": secret_value,  # Encrypted in practice
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=rotation_period_days)).isoformat()
        }

        self._log_event("CREATE", name, version_id)
        return version_id

    def get_secret(self, name: str) -> Optional[str]:
        """Get current active secret"""
        if name not in self._secrets:
            return None

        current_version_id = self._secrets[name]["current_version"]
        version = self._versions.get(current_version_id)

        if version and version["status"] == "active":
            self._log_event("READ", name, current_version_id)
            return version["value"]

        return None

    def rotate_secret(self, name: str, new_secret_value: str) -> str:
        """Rotate secret: create new version, keep old active temporarily"""
        if name not in self._secrets:
            return None

        secret = self._secrets[name]
        current_version_id = secret["current_version"]
        old_version = self._versions.get(current_version_id)

        # Create new version
        version_num = int(current_version_id.split("-v")[1]) + 1
        new_version_id = f"{name}-v{version_num}"

        new_version = {
            "id": new_version_id,
            "secret_name": name,
            "value": new_secret_value,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=secret["rotation_period"])).isoformat()
        }

        self._versions[new_version_id] = new_version

        # Mark old as deprecated (but keep it for a grace period)
        if old_version:
            old_version["status"] = "deprecated"
            old_version["deprecation_grace_period_ends"] = (
                datetime.utcnow() + timedelta(days=7)
            ).isoformat()

        # Update current
        secret["current_version"] = new_version_id
        secret["versions"].append(new_version_id)

        self._rotations.append({
            "secret_name": name,
            "old_version": current_version_id,
            "new_version": new_version_id,
            "rotated_at": datetime.utcnow().isoformat(),
            "reason": "periodic"
        })

        self._log_event("ROTATE", name, new_version_id)
        return new_version_id

    def revoke_secret(self, version_id: str, reason: str) -> None:
        """Revoke compromised secret immediately"""
        if version_id not in self._versions:
            return

        version = self._versions[version_id]
        version["status"] = "revoked"
        version["revoked_at"] = datetime.utcnow().isoformat()
        version["revocation_reason"] = reason

        secret_name = version["secret_name"]
        secret = self._secrets.get(secret_name)

        # If revoking current version, need immediate rotation
        if secret and secret["current_version"] == version_id:
            # Create emergency version
            version_num = int(version_id.split("-v")[1]) + 1
            emergency_version_id = f"{secret_name}-v{version_num}"
            # Would generate new secret here
            secret["current_version"] = emergency_version_id

        self._log_event("REVOKE", secret_name, version_id, reason)

    def get_version_status(self, name: str) -> Dict:
        """Get all versions for a secret"""
        if name not in self._secrets:
            return None

        secret = self._secrets[name]
        versions_info = []

        for version_id in secret["versions"]:
            version = self._versions.get(version_id)
            if version:
                versions_info.append({
                    "id": version_id,
                    "status": version["status"],
                    "created_at": version["created_at"],
                    "expires_at": version.get("expires_at"),
                    "is_current": version_id == secret["current_version"]
                })

        return {
            "secret_name": name,
            "current_version": secret["current_version"],
            "all_versions": versions_info
        }

    def get_audit_log(self, secret_name: str = None) -> List[Dict]:
        """Get audit log"""
        if secret_name:
            return [e for e in self._audit_log if e["secret"] == secret_name]
        return self._audit_log

    def _log_event(self, operation: str, secret_name: str, version_id: str, extra: str = "") -> None:
        """Log secret operation for audit"""
        self._audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "secret": secret_name,
            "version": version_id,
            "details": extra
        })
'''

    return rotation


def generate_rotation_system() -> dict:
    """Generate complete secrets rotation system."""

    imports = '''from typing import Dict, List, Optional
from datetime import datetime, timedelta


'''

    module_doc = '''"""
Phase 5 Secrets Management: Automated Secret Rotation & Versioning

Rotate secrets on schedule, support multiple versions, revoke immediately (HashiCorp Vault pattern).

ROTATION WORKFLOW:

Day 1: Secret created
- API key: v1 = "sk_live_abc123"
- Status: ACTIVE
- Expires: Day 91

Day 30-45: Rotation scheduled automatically
- Create new secret: v2 = "sk_live_xyz789"
- Status: ACTIVE
- Update all services to use v2

Day 45-50: Grace period
- v1 Status: DEPRECATED (in grace period)
- v2 Status: ACTIVE
- Allow time for all services to update

Day 50: Grace period ends
- v1 Status: DEPRECATED (expired)
- v2 Status: ACTIVE
- Old key no longer accepted

Day 91: v2 expires
- Cycle repeats: create v3, deprecate v2

TRANSITION STRATEGY:

Linear transition (simple):
- 1 week: generate v2
- 2 weeks: v1 deprecated, v2 primary
- 3 weeks: v1 removed

Canary transition (safer):
- Day 1: v2 created (0% traffic)
- Day 2: v2 gets 10% new connections
- Day 5: v2 gets 50% new connections
- Day 7: v2 gets 100% new connections
- Day 14: v1 removed

REVOCATION (Emergency):

Scenario: API key leaked to GitHub

Immediate:
1. Revoke: status = REVOKED
2. Check: who has this key cached?
3. Force: services must refresh (error on next use)
4. Alert: security team, customers

Actions:
- v1 status: REVOKED
- v1 expiration: NOW (not 90 days)
- v2 generated: immediately
- Services: get error on next v1 use, forced to fetch v2

Timeline:
- T+0 min: Key leak discovered
- T+2 min: Key revoked in vault
- T+5 min: Services notice (next API call)
- T+10 min: All services using v2
- T+30 min: Post-mortem begun

VERSIONING:

Multiple versions active during rotation:
- v1 (deprecated): still works for 7 days (grace period)
- v2 (active): preferred, newly rotated
- v3 (future): could pre-generate

This allows:
- Services update at different times
- No coordination required
- Backward compatibility
- Graceful degradation

AUDIT REQUIREMENTS:

Every secret operation logged:
- WHO: which user/service accessed
- WHAT: read secret, rotated, revoked
- WHEN: timestamp of operation
- WHY: rotate reason, revoke reason

Example audit log:
```
2026-05-17T10:00:00Z READ db_password v5 by scheduled_job
2026-05-17T10:00:01Z READ api_key v2 by app_server_1
2026-05-17T14:00:00Z ROTATE api_key v2→v3 by automated_rotation
2026-05-17T14:00:05Z DEPRECATE api_key v2 reason=rotated
2026-05-17T18:00:00Z REVOKE api_key v2 reason=leaked_to_github
```

CERTIFICATE ROTATION:

Special case: certificates (TLS, SSH)

Problem: certificate expires, service breaks
Solution: rotate before expiry

Workflow:
- Certificate expires: 2026-08-17
- Generate new: 2026-07-17 (30 days before)
- Test new certificate: 2 weeks
- Deploy to staging: 2 weeks before prod
- Deploy to production: 1 week before expiry
- Old certificate: keep 1 month after expiry (during grace)

Monitoring:
- Alert: 60 days before expiry
- Alert: 30 days before expiry
- Alert: 7 days before expiry
- Alert: certificate about to expire
- Alert: CRITICAL if expired (service down)

COMMON MISTAKES:

❌ No rotation: same key for years
   → Increased risk (key might be compromised)
   → Compliance failure
   → Solution: rotate every 90 days

❌ Immediate removal: old key invalid immediately
   → Services crash if still using old key
   → Outage during rotation
   → Solution: grace period (7 days)

❌ No audit: don't track who accessed what
   → Compliance failure
   → Can't investigate if key leaked
   → Solution: log all operations

✓ Good rotation:
   - Automated: not manual
   - Staged: multiple versions active
   - Audited: all operations logged
   - Fast revocation: compromised keys revoked immediately
"""
'''

    rotation = generate_secrets_rotation()

    complete_code = imports + module_doc + "\n" + rotation

    return {
        "code": complete_code,
        "pattern": "Secrets Rotation",
        "module": "phase5_secrets_rotation.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate secrets rotation")
    args = parser.parse_args()
    result = generate_rotation_system()
    print(result["code"])


if __name__ == "__main__":
    main()
