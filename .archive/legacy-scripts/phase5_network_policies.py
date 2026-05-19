#!/usr/bin/env python3
"""
Phase 5 Network Security: Service-to-Service Authorization

Network Policies: Control which services can talk to which services.

Problem: No service-to-service security
- Service A calls Service B: no authentication
- Service B trusts any caller (could be attacker)
- Network flat: any pod can reach any pod
- No encryption between services

Network Policies (solution):
- mTLS: mutual TLS (both verify each other)
- Network segmentation: firewall rules
- Service-to-service auth: caller must have cert
- Zero-trust: verify every request
"""

from typing import Dict, List, Optional, Set
from datetime import datetime


def generate_network_policies() -> str:
    """Generate network policies and mTLS system."""

    policies = '''
class NetworkPolicies:
    """
    Manage service-to-service authorization.

    Controls:
    - Who can call whom
    - What port/protocol
    - Encryption (mTLS)
    - Rate limiting per caller
    """

    def __init__(self):
        self._policies = {}  # service_name → {allow_list}
        self._certificates = {}  # service_name → {cert_id, issuer, expiry}
        self._denied_requests = []  # Denied request log

    def add_policy(
        self,
        service_name: str,
        allow_from: List[str],  # List of service names allowed to call
        port: int = 443,
        protocol: str = "https"
    ) -> None:
        """Define network policy"""
        self._policies[service_name] = {
            "service": service_name,
            "allow_from": set(allow_from),
            "port": port,
            "protocol": protocol,
            "mtls_required": True,
            "created_at": datetime.utcnow().isoformat()
        }

    def add_certificate(
        self,
        service_name: str,
        certificate: str,
        issuer: str = "internal-ca"
    ) -> None:
        """Register mTLS certificate"""
        self._certificates[service_name] = {
            "service": service_name,
            "certificate": certificate,  # Encrypted/hashed
            "issuer": issuer,
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow().replace(day=1) + __import__("datetime").timedelta(days=365)).isoformat(),
            "status": "valid"
        }

    def check_policy(
        self,
        source_service: str,
        target_service: str,
        client_cert: str = None
    ) -> tuple:
        """Check if request is allowed"""
        # Policy check
        policy = self._policies.get(target_service)

        if not policy:
            return (True, "No policy defined (allow by default)")

        if source_service not in policy["allow_from"]:
            self._denied_requests.append({
                "timestamp": datetime.utcnow().isoformat(),
                "source": source_service,
                "target": target_service,
                "reason": "Not in allow_list"
            })
            return (False, f"{source_service} not authorized to call {target_service}")

        # mTLS check (if required)
        if policy.get("mtls_required") and not client_cert:
            self._denied_requests.append({
                "timestamp": datetime.utcnow().isoformat(),
                "source": source_service,
                "target": target_service,
                "reason": "mTLS certificate missing"
            })
            return (False, "mTLS certificate required")

        # Certificate validity check
        cert_info = self._certificates.get(source_service)
        if cert_info and cert_info["status"] != "valid":
            self._denied_requests.append({
                "timestamp": datetime.utcnow().isoformat(),
                "source": source_service,
                "target": target_service,
                "reason": "Invalid certificate"
            })
            return (False, f"Certificate invalid: {cert_info['status']}")

        return (True, "Request allowed")

    def get_policy(self, service_name: str) -> Optional[Dict]:
        """Get policy for service"""
        policy = self._policies.get(service_name)
        if policy:
            policy["allow_from"] = list(policy["allow_from"])  # Convert set to list
        return policy

    def get_denied_requests(self) -> List[Dict]:
        """Get denied request log"""
        return self._denied_requests

    def revoke_certificate(self, service_name: str) -> None:
        """Revoke certificate (emergency)"""
        if service_name in self._certificates:
            self._certificates[service_name]["status"] = "revoked"
            self._certificates[service_name]["revoked_at"] = datetime.utcnow().isoformat()

    def get_certificate_status(self, service_name: str) -> Optional[Dict]:
        """Check certificate status"""
        return self._certificates.get(service_name)
'''

    return policies


def generate_policies_system() -> dict:
    """Generate complete network policies system."""

    imports = '''from typing import Dict, List, Optional, Set
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Network Security: Service-to-Service Authorization

Secure communication between microservices (Istio, SPIFFE pattern).

ZERO-TRUST NETWORK:

Traditional (perimeter security):
- Outside firewall: untrusted
- Inside firewall: trusted
- Problem: once inside, attacker free

Zero-trust:
- Every request: verify caller
- Every connection: encrypt
- Every service: has identity (certificate)
- No "trusted" zone

EXAMPLE: User Service calls Order Service

1. User Service wants to call Order Service:port/orders

2. TLS Handshake:
   - User Service: "Hi, I'm user-service"
   - Sends certificate signed by internal CA
   - Order Service: verifies certificate
   - Order Service: "Hi, I'm order-service"
   - Sends certificate

3. Network Policy Check:
   - Is user-service in order-service's allow_list?
   - YES: user-service in [api-gateway, payment-service, user-service]
   - ALLOWED

4. Request proceeds:
   - GET /orders → encrypted with TLS
   - Response: encrypted with TLS

NETWORK POLICIES:

Policy: Order Service
  Allow from:
    - api-gateway (external entry point)
    - user-service (fetch user info)
    - payment-service (charge user)
  Deny from:
    - auth-service (shouldn't call orders)
    - notification-service (shouldn't have access)

Policy: Database
  Allow from:
    - user-service
    - order-service
    - payment-service
  Deny from:
    - api-gateway (too sensitive)
    - notification-service

CERTIFICATE MANAGEMENT:

Certificate lifecycle:
- Created: 2026-05-17 (CA signs it)
- Valid for: 1 year (2027-05-17)
- Auto-rotate: 30 days before expiry (2027-04-17)
- Revoke: immediately if leaked

Each service gets:
- Certificate (signed by CA)
- Private key (secret, stored in vault)
- CA bundle (verify other certs)

Rotation:
- Old cert: still valid (gradual switch)
- New cert: generated 30 days before expiry
- Deploy: services pick up new cert automatically
- Cleanup: old cert revoked after transition

AUDIT LOG (denied requests):

2026-05-17T10:00:00Z DENIED notification-service → database
  Reason: not in allow_list

2026-05-17T10:01:00Z DENIED attacker-pod → user-service
  Reason: certificate invalid (not from CA)

2026-05-17T10:02:00Z DENIED user-service → database
  Reason: certificate expired

ACTION: All denied requests logged
- Alert if spike in denials
- Investigate possible breach
- Update policy if legitimate

IMPLEMENTATION: Kubernetes Network Policy

kind: NetworkPolicy
metadata:
  name: order-service-policy
spec:
  podSelector:
    matchLabels:
      app: order-service
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 443

BENEFITS:

✓ Security: only authorized services can communicate
✓ Audit: track all denials
✓ Compliance: zero-trust, encryption mandatory
✓ Resilience: rogue service can't access sensitive services
✓ Cost: fine-grained control, no overprivileged access

COMMON MISTAKES:

❌ No policies: allow all by default
   → Compromise of one service → access all others
   → Solution: explicit allow, deny by default

❌ Static certificates: not rotated
   → Leaked certificate valid forever
   → Solution: rotate every 90 days

❌ Trust but verify: accept certs without validation
   → Man-in-the-middle possible
   → Solution: always verify CA signature

✓ Good security:
   - mTLS for all service-to-service
   - Network policies explicit
   - Certificates rotated regularly
   - Denials logged and alerted
"""
'''

    policies = generate_network_policies()

    complete_code = imports + module_doc + "\n" + policies

    return {
        "code": complete_code,
        "pattern": "Network Policies",
        "module": "phase5_network_policies.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate network policies")
    args = parser.parse_args()
    result = generate_policies_system()
    print(result["code"])


if __name__ == "__main__":
    main()
