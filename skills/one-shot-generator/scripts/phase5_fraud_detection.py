#!/usr/bin/env python3
"""Phase 5 Fraud Detection: Anomaly Detection & Real-time Scoring"""

from typing import Dict, List, Optional


def generate_fraud_detection() -> str:
    return '''
class AnomalyDetector:
    """Detect fraudulent transactions using anomaly detection."""

    def __init__(self):
        self._baseline = {}  # user_id → {normal_pattern}
        self._anomalies = []

    def learn_baseline(self, user_id: str, transactions: List[Dict]) -> None:
        """Learn normal transaction pattern"""
        if not transactions:
            return

        avg_amount = sum(t.get("amount", 0) for t in transactions) / len(transactions)
        avg_frequency = len(transactions) / 30  # per day

        self._baseline[user_id] = {
            "avg_amount": avg_amount,
            "avg_frequency": avg_frequency,
            "typical_merchants": self._extract_merchants(transactions)
        }

    def score_transaction(self, user_id: str, transaction: Dict) -> float:
        """Score transaction (0.0 = normal, 1.0 = fraud)"""
        baseline = self._baseline.get(user_id)
        if not baseline:
            return 0.5  # Unknown user

        amount = transaction.get("amount", 0)
        merchant = transaction.get("merchant", "")

        # Heuristics
        score = 0.0

        # Amount deviation
        if amount > baseline["avg_amount"] * 5:
            score += 0.3
        elif amount > baseline["avg_amount"] * 2:
            score += 0.1

        # Unusual merchant
        if merchant not in baseline["typical_merchants"]:
            score += 0.2

        return min(score, 1.0)

    def flag_anomaly(self, transaction: Dict, score: float) -> None:
        """Flag high-risk transaction"""
        if score > 0.7:
            self._anomalies.append({
                "transaction": transaction,
                "risk_score": score,
                "action": "BLOCK" if score > 0.9 else "REVIEW"
            })

    def _extract_merchants(self, transactions: List[Dict]) -> set:
        """Extract typical merchants"""
        return {t.get("merchant") for t in transactions if t.get("merchant")}
'''
    return generate_fraud_detection()


if __name__ == "__main__":
    print(generate_fraud_detection())
