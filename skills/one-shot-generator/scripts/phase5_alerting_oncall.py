#!/usr/bin/env python3
"""
Phase 5 Alerting & On-Call: Incident Routing & Escalation

Alerting: Notify humans when something is wrong.

Problem: Silent failures
- Database is down, but nobody knows
- Error rate is 50%, users are suffering
- On-call engineer is asleep

Alerting (solution):
- Rules: if metric > threshold for N minutes, alert
- Routing: route alert to right person
- Escalation: if not acknowledged, escalate
- Remediation: guide engineer to fix
"""

from typing import Dict, List, Optional
from datetime import datetime


def generate_alerting_oncall() -> str:
    """Generate alerting and on-call system."""

    alerting = '''
class AlertingRules:
    """
    Define and evaluate alerting rules.

    Rule: condition → action
    Example: if error_rate > 1% for 5 min → create incident
    """

    def __init__(self):
        self._rules = []  # Alert rules
        self._incidents = []  # Active incidents
        self._escalations = []  # Escalation history

    def add_rule(
        self,
        name: str,
        condition: str,  # "error_rate > 0.01"
        duration: int,  # 300 seconds (5 min)
        severity: str  # "critical", "warning"
    ) -> str:
        """Add alerting rule"""
        rule = {
            "id": f"rule-{len(self._rules)}",
            "name": name,
            "condition": condition,
            "duration": duration,
            "severity": severity,
            "created_at": datetime.utcnow().isoformat(),
            "active": True
        }

        self._rules.append(rule)
        return rule["id"]

    def evaluate_rule(
        self,
        rule_id: str,
        current_value: float,
        threshold: float
    ) -> Optional[Dict]:
        """Evaluate rule, create incident if triggered"""
        rule = next((r for r in self._rules if r["id"] == rule_id), None)
        if not rule or not rule["active"]:
            return None

        # Check condition
        if current_value > threshold:
            incident = {
                "id": f"inc-{len(self._incidents)}",
                "rule_id": rule_id,
                "rule_name": rule["name"],
                "severity": rule["severity"],
                "status": "firing",
                "created_at": datetime.utcnow().isoformat(),
                "acknowledged_at": None,
                "resolved_at": None
            }

            self._incidents.append(incident)
            return incident

        return None

    def acknowledge_incident(self, incident_id: str, engineer: str) -> None:
        """Acknowledge incident (stop escalation)"""
        incident = next((i for i in self._incidents if i["id"] == incident_id), None)
        if incident:
            incident["acknowledged_at"] = datetime.utcnow().isoformat()
            incident["acknowledged_by"] = engineer
            incident["status"] = "acknowledged"

    def resolve_incident(self, incident_id: str) -> None:
        """Resolve incident (close ticket)"""
        incident = next((i for i in self._incidents if i["id"] == incident_id), None)
        if incident:
            incident["resolved_at"] = datetime.utcnow().isoformat()
            incident["status"] = "resolved"

    def get_active_incidents(self) -> List[Dict]:
        """Get all active incidents"""
        return [i for i in self._incidents if i["status"] in ["firing", "acknowledged"]]


class OnCallSchedule:
    """Manage on-call rotations and escalation."""

    def __init__(self):
        self._schedule = []  # [{start, end, engineer}]
        self._escalations = []  # Escalation policies

    def set_on_call(self, engineer: str, start: str, end: str) -> None:
        """Set engineer on-call for time period"""
        self._schedule.append({
            "engineer": engineer,
            "start": start,
            "end": end
        })

    def get_on_call(self) -> Optional[str]:
        """Get current on-call engineer"""
        now = datetime.utcnow().isoformat()

        for entry in self._schedule:
            if entry["start"] <= now <= entry["end"]:
                return entry["engineer"]

        return None

    def add_escalation_policy(
        self,
        level: int,
        delay_minutes: int,
        target: str,
        action: str = "page"
    ) -> None:
        """Add escalation step"""
        self._escalations.append({
            "level": level,
            "delay": delay_minutes * 60,
            "target": target,
            "action": action
        })

    def escalate(self, incident_id: str) -> Dict:
        """Execute escalation chain"""
        if not self._escalations:
            return None

        # Level 1: page current on-call
        on_call = self.get_on_call()

        escalation = {
            "incident_id": incident_id,
            "timestamp": datetime.utcnow().isoformat(),
            "levels": []
        }

        for policy in sorted(self._escalations, key=lambda x: x["level"]):
            target = on_call if policy["level"] == 1 else policy["target"]

            escalation["levels"].append({
                "level": policy["level"],
                "target": target,
                "action": policy["action"],
                "delay_seconds": policy["delay"]
            })

        self._escalations_tracked.append(escalation)
        return escalation

    def __init__(self):
        self._schedule = []
        self._escalations = []
        self._escalations_tracked = []
'''

    return alerting


def generate_oncall_system() -> dict:
    """Generate complete on-call system."""

    imports = '''from typing import Dict, List, Optional
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Alerting & On-Call: Incident Routing & Escalation

Alert rules with intelligent escalation (PagerDuty pattern).

ALERT RULE LIFECYCLE:

1. RULE DEFINITION
   Name: "High Error Rate"
   Condition: error_rate > 1%
   Duration: 5 minutes
   Severity: critical

2. MONITORING
   Every 30 seconds: check error_rate

   Time 0:00: error_rate = 0.5% (OK)
   Time 0:30: error_rate = 0.7% (OK)
   Time 1:00: error_rate = 1.5% (BREACH! Start timer)
   Time 1:30: error_rate = 1.6% (Still breached, 1.5 min elapsed)
   Time 3:00: error_rate = 1.4% (Still breached, 3 min elapsed)
   Time 5:00: error_rate = 1.2% (Still breached, 5 min elapsed) → FIRE ALERT

3. INCIDENT CREATION
   Create incident: "High Error Rate (1.2%)"
   Severity: critical
   Status: firing
   Created: 2026-05-17T10:05:00Z

4. ROUTING
   Route to: current on-call engineer

5. NOTIFICATION
   Send: SMS, Slack, PagerDuty

6. ACKNOWLEDGMENT
   Engineer: "Acking. Investigating database issue"
   Status: acknowledged
   Time: 5 minutes after alert

7. RESOLUTION
   Engineer: "Fixed. Restarted database. Error rate now 0.2%"
   Status: resolved
   Time: 25 minutes after alert

ON-CALL ROTATION:

Week 1: Alice (Mon-Sun 00:00 UTC)
Week 2: Bob (Mon-Sun 00:00 UTC)
Week 3: Carol (Mon-Sun 00:00 UTC)
Week 4: Dave (Mon-Sun 00:00 UTC)
Weekly rotation ensures no burnout

During week, if Alice on-call:
- Alert fires → page Alice
- Alice has 5 minutes to ack
- No ack → escalate to Bob (backup)
- Bob has 5 minutes to ack
- No ack → page both Alice and Bob
- No ack → notify manager

ESCALATION POLICY:

Level 1: Page primary (on-call engineer)
- Delay: immediate
- Timeout: 5 min
- If no ack → go to Level 2

Level 2: Page backup
- Delay: 5 min
- Timeout: 5 min
- If no ack → go to Level 3

Level 3: Page manager
- Delay: 10 min
- Timeout: none (stay on until resolution)

Example: Alert at 10:00
- 10:00: Page Alice (primary)
- 10:05: No response, page Bob (backup)
- 10:10: Alice responds "on it"
- Alert acked, no further escalation

SEVERITY LEVELS:

CRITICAL (page immediately)
- Error rate > 5%
- Database down
- API endpoint returning 500s
- Escalate immediately

MAJOR (page within 10 min)
- Error rate 1-5%
- Database slow (>5s latency)
- Disk usage > 90%
- Escalate after 10 min

MINOR (log in ticket, no page)
- Error rate < 1%
- Slow query (>1s)
- High memory usage (80%)
- Manual review

INFO (no escalation)
- Service deployed
- Backup completed
- Metric reached milestone

EXAMPLE: Database Down (CRITICAL)

10:00:00 - Database crashes
10:00:30 - Prometheus detects: postgres_up = 0
10:01:00 - Alert fires: "Database unreachable"
10:01:00 - Page Alice (on-call)
10:01:15 - Alice's phone rings
10:01:20 - Alice acks in PagerDuty
10:01:20 - Escalation timer reset
10:02:00 - Alice ssh's to DB server
10:03:00 - Alice restarts postgres
10:03:30 - Database responding
10:03:30 - Alert auto-resolves (postgres_up = 1)
10:03:30 - Incident marked resolved
10:05:00 - Alice writes post-mortem (why did DB crash?)

COMMON MISTAKES:

❌ Alert storms: Every tiny blip triggers alert
   → Oncall ignores alerts, goes to sleep
   → Real problems missed
   → Solution: tune thresholds (1% error not 0.1%)

❌ No escalation: Alert fires, nobody notified
   → Issues persist for hours
   → Solution: configure escalation policy

❌ Too sensitive: Alert on every data point
   → False alarms
   → Solution: require condition true for N minutes

✓ Right tuning: Alert when users are impacted
   → 5% error rate = definitely a problem
   → 0.5% error rate = expected normal variation
"""
'''

    alerting = generate_alerting_oncall()

    complete_code = imports + module_doc + "\n" + alerting

    return {
        "code": complete_code,
        "pattern": "Alerting & On-Call",
        "module": "phase5_alerting_oncall.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate alerting and on-call system")
    args = parser.parse_args()
    result = generate_oncall_system()
    print(result["code"])


if __name__ == "__main__":
    main()
