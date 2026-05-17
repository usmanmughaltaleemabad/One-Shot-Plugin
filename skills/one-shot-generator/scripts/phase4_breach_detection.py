#!/usr/bin/env python3
"""
Phase 4 Breach Detection & Response

Threat: Unauthorized access to sensitive data.

Detection:
- Monitor for suspicious activity (many failed logins)
- Detect data exfiltration (unusual queries, exports)
- Track abnormal patterns (admin at 3 AM from new country)
- Alert on policy violations

Response:
- Isolate affected systems (stop bleeding)
- Notify users within legal timeframe (24h-72h)
- Preserve evidence for investigation
- Post-mortem: what happened, why, prevent future
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import json


def generate_breach_detection() -> str:
    """Generate breach detection system."""

    detection = '''
class BreachDetector:
    """
    Monitor for breach indicators.

    Detectors:
    - Multiple failed login attempts (brute force)
    - Unusual data queries (mass export)
    - System access from unusual location
    - Privilege escalation
    - Configuration changes
    """

    def __init__(self):
        self._rules = []  # Detection rules
        self._alerts = []  # Detected incidents

    def add_detection_rule(
        self,
        name: str,
        condition: Callable,
        severity: str  # low, medium, high, critical
    ) -> None:
        """Add detection rule"""
        self._rules.append({
            "name": name,
            "condition": condition,
            "severity": severity
        })

    def check_event(self, event: Dict) -> Optional[Dict]:
        """Check if event matches any detection rule"""
        for rule in self._rules:
            try:
                if rule["condition"](event):
                    alert = {
                        "rule": rule["name"],
                        "severity": rule["severity"],
                        "event": event,
                        "timestamp": datetime.utcnow().isoformat(),
                        "id": f"alert-{datetime.utcnow().timestamp()}"
                    }
                    self._alerts.append(alert)
                    return alert
            except Exception:
                pass

        return None

    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get alerts from last N hours"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [a for a in self._alerts
                if datetime.fromisoformat(a["timestamp"]) > cutoff]

    def get_critical_alerts(self) -> List[Dict]:
        """Get critical severity alerts"""
        return [a for a in self._alerts if a["severity"] == "critical"]
'''

    return detection


def generate_breach_response() -> str:
    """Generate breach response protocol."""

    response = '''
class BreachResponseProtocol:
    """
    Execute breach response: contain, notify, investigate.

    Timeline:
    - T+0: Detect & validate breach
    - T+1h: Contain (isolate systems)
    - T+4h: Notify security team
    - T+24h: Notify affected users (or regulators per law)
    - T+72h: Public disclosure (if required)
    - T+2w: Post-mortem investigation
    """

    def __init__(self):
        self._breaches = []
        self._notifications = []

    def report_breach(
        self,
        description: str,
        affected_users: int,
        data_types: List[str],
        severity: str  # low, medium, high, critical
    ) -> str:
        """Report a potential breach"""
        breach_id = f"breach-{datetime.utcnow().timestamp()}"

        breach = {
            "id": breach_id,
            "description": description,
            "affected_users": affected_users,
            "data_types": data_types,
            "severity": severity,
            "reported_at": datetime.utcnow().isoformat(),
            "status": "investigating"
        }

        self._breaches.append(breach)
        return breach_id

    def contain_breach(self, breach_id: str) -> None:
        """Isolate affected systems"""
        for breach in self._breaches:
            if breach["id"] == breach_id:
                breach["status"] = "contained"
                breach["contained_at"] = datetime.utcnow().isoformat()

    def notify_users(
        self,
        breach_id: str,
        user_emails: List[str],
        message: str
    ) -> Dict:
        """Notify affected users"""
        notification = {
            "breach_id": breach_id,
            "recipients": len(user_emails),
            "message": message,
            "sent_at": datetime.utcnow().isoformat(),
            "status": "sent"
        }

        self._notifications.append(notification)
        return notification

    def notify_regulators(
        self,
        breach_id: str,
        regulator: str,
        details: str
    ) -> Dict:
        """Notify regulatory bodies (if required)"""
        notification = {
            "breach_id": breach_id,
            "regulator": regulator,
            "details": details,
            "notified_at": datetime.utcnow().isoformat()
        }

        self._notifications.append(notification)
        return notification

    def get_breach(self, breach_id: str) -> Optional[Dict]:
        """Get breach details"""
        for breach in self._breaches:
            if breach["id"] == breach_id:
                return breach
        return None
'''

    return response


def generate_breach_system() -> dict:
    """Generate complete breach detection & response system."""

    imports = '''from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import json


'''

    module_doc = '''"""
Phase 4 Breach Detection & Notification

Detect unauthorized data access and respond quickly.

DETECTION METHODS:
1. Behavior Analysis
   - User login patterns (time, location, frequency)
   - Data access patterns (what, how much, when)
   - System changes (config, privileges, rules)

2. Log Analysis
   - Failed authentication (brute force detection)
   - Unusual queries (mass data export)
   - API abuse (rate limiting violations)

3. External Signals
   - Dark web scans (check if data sold)
   - Threat intelligence (known attacker patterns)
   - Customer reports ("I see my data on..."

RESPONSE TIMELINE (per law):
- Immediately: Contain (isolate systems, stop exfiltration)
- 24h: Notify users (GDPR, CCPA, state laws vary)
- 72h: Notify regulators (GDPR requirement)
- Public: Disclose if material impact

NOTIFICATION:
- What data was accessed
- When it happened
- What users should do (change password, monitor credit)
- What company doing to prevent future
- Contact info for questions

POST-MORTEM:
- How did breach happen
- What failed (detection, prevention)
- Root cause
- Improvements to prevent future
- Lessons learned shared with team
"""
'''

    detection = generate_breach_detection()
    response = generate_breach_response()

    complete_code = imports + module_doc + "\n" + detection + "\n" + response

    return {
        "code": complete_code,
        "pattern": "Breach Detection & Response",
        "module": "phase4_breach_detection.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate breach detection system")
    args = parser.parse_args()
    result = generate_breach_system()
    print(result["code"])


if __name__ == "__main__":
    main()
