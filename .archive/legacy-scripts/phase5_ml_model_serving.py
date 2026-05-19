#!/usr/bin/env python3
"""
Phase 5 ML Model Serving: A/B Testing & Canary Deployment

Model Serving: Predict on live traffic using trained models.

Problem: Single model deployment
- Deploy new model: all traffic affected
- New model has bug: all requests fail
- No way to compare models

Model Serving (solution):
- Model registry: version models
- Canary deployment: 10% traffic to new model
- A/B testing: split traffic, measure business metrics
- Inference batching: multiple predictions in one call
"""

from typing import Dict, List, Optional
from datetime import datetime


def generate_ml_model_serving() -> str:
    """Generate ML model serving system."""

    serving = '''
class MLModelServing:
    """
    Serve ML models with A/B testing and canary deployment.

    Features:
    - Model registry: track model versions
    - A/B testing: compare models on real traffic
    - Canary deployment: gradual rollout
    - Inference batching: efficient predictions
    """

    def __init__(self):
        self._models = {}  # model_id → {version, stage, metrics}
        self._deployments = []  # Active deployments
        self._experiment = None  # Current A/B test
        self._predictions = []  # Prediction history

    def register_model(
        self,
        model_id: str,
        version: int,
        model_path: str
    ) -> str:
        """Register model for serving"""
        self._models[model_id] = {
            "id": model_id,
            "version": version,
            "path": model_path,
            "stage": "dev",
            "registered_at": datetime.utcnow().isoformat(),
            "prediction_count": 0
        }

        return model_id

    def deploy_canary(
        self,
        stable_model_id: str,
        canary_model_id: str,
        canary_percentage: int
    ) -> str:
        """Deploy new model as canary (percentage of traffic)"""
        if not 0 < canary_percentage < 100:
            raise ValueError("Canary % must be 1-99")

        deployment = {
            "id": f"deploy-{datetime.utcnow().timestamp()}",
            "stable": stable_model_id,
            "canary": canary_model_id,
            "percentage": canary_percentage,
            "started_at": datetime.utcnow().isoformat(),
            "status": "active"
        }

        self._deployments.append(deployment)

        # Update model stages
        if stable_model_id in self._models:
            self._models[stable_model_id]["stage"] = "production"
        if canary_model_id in self._models:
            self._models[canary_model_id]["stage"] = "canary"

        return deployment["id"]

    def promote_canary(self, deployment_id: str) -> None:
        """Promote canary to 100% traffic"""
        deployment = next((d for d in self._deployments if d["id"] == deployment_id), None)
        if not deployment:
            return

        # Canary → production
        canary_id = deployment["canary"]
        stable_id = deployment["stable"]

        if canary_id in self._models:
            self._models[canary_id]["stage"] = "production"
        if stable_id in self._models:
            self._models[stable_id]["stage"] = "archived"

        deployment["status"] = "completed"

    def start_ab_test(
        self,
        model_a_id: str,
        model_b_id: str,
        split_percentage: int = 50
    ) -> str:
        """Start A/B test: compare models on real traffic"""
        self._experiment = {
            "id": f"exp-{datetime.utcnow().timestamp()}",
            "model_a": model_a_id,
            "model_b": model_b_id,
            "split": split_percentage,
            "started_at": datetime.utcnow().isoformat(),
            "metrics_a": {"predictions": 0, "avg_latency": 0},
            "metrics_b": {"predictions": 0, "avg_latency": 0}
        }

        return self._experiment["id"]

    def select_model(self, request_id: str) -> str:
        """Select model for inference (A/B test or canary)"""
        # Hash-based selection for reproducibility
        hash_val = hash(request_id) % 100

        if self._experiment:
            split = self._experiment["split"]
            if hash_val < split:
                return self._experiment["model_a"]
            else:
                return self._experiment["model_b"]

        # Fallback: canary deployment
        deployment = next((d for d in self._deployments if d["status"] == "active"), None)
        if deployment:
            canary_pct = deployment["percentage"]
            if hash_val < canary_pct:
                return deployment["canary"]
            else:
                return deployment["stable"]

        # Fallback: production model
        for model in self._models.values():
            if model["stage"] == "production":
                return model["id"]

        return None

    def predict(self, request_id: str, features: Dict) -> Dict:
        """Make prediction using selected model"""
        model_id = self.select_model(request_id)

        if not model_id or model_id not in self._models:
            return {"error": "No model available"}

        model = self._models[model_id]
        model["prediction_count"] += 1

        prediction = {
            "request_id": request_id,
            "model_id": model_id,
            "model_version": model["version"],
            "features": features,
            "prediction": 0.95,  # Dummy prediction
            "latency_ms": 10,
            "timestamp": datetime.utcnow().isoformat()
        }

        self._predictions.append(prediction)
        return prediction

    def batch_predict(self, requests: List[Tuple[str, Dict]]) -> List[Dict]:
        """Predict on multiple requests in one call"""
        predictions = []

        for request_id, features in requests:
            pred = self.predict(request_id, features)
            predictions.append(pred)

        return predictions

    def end_ab_test(self) -> Dict:
        """End A/B test, declare winner"""
        if not self._experiment:
            return None

        # Analyze metrics
        metrics_a = self._experiment["metrics_a"]
        metrics_b = self._experiment["metrics_b"]

        winner = "model_a" if metrics_a["predictions"] > metrics_b["predictions"] else "model_b"

        result = {
            "experiment_id": self._experiment["id"],
            "model_a": self._experiment["model_a"],
            "model_b": self._experiment["model_b"],
            "winner": winner,
            "metrics_a": metrics_a,
            "metrics_b": metrics_b
        }

        self._experiment = None
        return result

    def get_model_status(self, model_id: str) -> Optional[Dict]:
        """Get model serving status"""
        return self._models.get(model_id)
'''

    return serving


def generate_serving_system() -> dict:
    """Generate complete ML model serving system."""

    imports = '''from typing import Dict, List, Optional, Tuple
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 ML Model Serving: A/B Testing & Canary Deployment

Serve ML models with A/B testing, canary deployment, and inference batching.

A/B TESTING:

Goal: Compare two models on real production traffic

Current state:
- Model A (v1): accuracy 92%
- Model B (v2): accuracy 94% (lab)
- But: will it work on real data?

A/B test:
- Split traffic 50/50
- Model A: 50% of requests
- Model B: 50% of requests
- Measure: business metrics (conversion, revenue, latency)

Results:
- Model A: 5% conversion rate, 2% error rate, 10ms latency
- Model B: 5% conversion rate, 2% error rate, 12ms latency
- Verdict: no winner (B is slower, no conversion improvement)
- Decision: keep A, don't deploy B

Alternative scenario:
- Model B: 6% conversion rate, 2% error rate, 12ms latency
- Verdict: B is winner (1% conversion improvement)
- Decision: promote B to 100%

CANARY DEPLOYMENT:

Goal: Roll out new model safely

Process:
1. Week 1: Model A (v1) → 100% production
2. Week 2: Model B (v2) → 10% canary, 90% Model A
   - Monitor: error rate, latency, business metrics
   - If good: proceed
   - If bad: rollback to 0%

3. Week 3: Model B → 25% canary, 75% Model A
   - Monitor again
   - If stable: proceed

4. Week 4: Model B → 50% canary, 50% Model A

5. Week 5: Model B → 100% production
   - Model A archived

INFERENCE BATCHING:

Problem: Single prediction = overhead
- Request comes in with features
- Load model, run inference, return
- Overhead per request: latency, resource usage

Solution: Batch multiple predictions
- Client: batch 10 requests together
- Server: run inference on batch (more efficient)
- Return: 10 predictions

Efficiency:
- Single predictions: 10 * 10ms = 100ms
- Batched predictions: 1 * 15ms = 15ms (GPU/SIMD parallel)
- Speedup: 6.7x faster

MONITORING METRICS:

Prediction latency:
- p50 (median): 10ms
- p95: 20ms
- p99: 50ms

Error rate:
- Prediction errors (NaN, timeout)
- Track by model version

Model performance:
- Accuracy, precision, recall
- Compare to training metrics
- Alert if drops > 5%

Data drift:
- Are input features changing?
- Feature distribution in prod ≠ training
- Retraining trigger

EXAMPLE: Churn Prediction A/B Test

Model A (baseline): Predicts customer churn
Model B (new): Improved features, better performance

Experiment:
- Customer C001: hash("C001") % 100 = 47 → Model A
- Customer C002: hash("C002") % 100 = 72 → Model B
- Each customer always gets same model (consistent experience)

Track:
- Model A: accuracy 85%, precision 92%, recall 78%
- Model B: accuracy 87%, precision 94%, recall 79%
- Winner: B (higher accuracy and precision)
- Decision: promote B to 100%

Deployment:
- Week 1: B gets 10% traffic
- Week 2: B gets 25% traffic
- Week 3: B gets 50% traffic
- Week 4: B gets 100% traffic (A archived)
"""
'''

    serving = generate_ml_model_serving()

    complete_code = imports + module_doc + "\n" + serving

    return {
        "code": complete_code,
        "pattern": "ML Model Serving",
        "module": "phase5_ml_model_serving.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate ML model serving")
    args = parser.parse_args()
    result = generate_serving_system()
    print(result["code"])


if __name__ == "__main__":
    main()
