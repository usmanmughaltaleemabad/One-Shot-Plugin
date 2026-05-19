#!/usr/bin/env python3
"""
Phase 5 ML Training Pipeline: Feature Engineering & Orchestration

ML Pipeline: Extract features → train model → evaluate → deploy.

Problem: Manual ML workflows
- Data scientist: runs notebook locally
- Features: hardcoded transformations
- Training: manual, one-off
- Evaluation: unclear if model improved
- Deployment: "copy model file to production"

ML Pipeline (solution):
- Feature engineering: automated transformations
- Training: scheduled, reproducible
- Evaluation: automated metrics, comparison to baseline
- Deployment: automated A/B test, rollback if needed
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Feature:
    name: str
    input_field: str
    transform: str


def generate_ml_training_pipeline() -> str:
    """Generate ML training pipeline."""

    pipeline = '''
class MLTrainingPipeline:
    """
    End-to-end ML training orchestration.

    Stages:
    1. Feature engineering: transform raw data
    2. Training: fit model on features
    3. Evaluation: compute metrics
    4. Registry: version and store model
    """

    def __init__(self):
        self._features = []  # Feature definitions
        self._models = {}  # model_id → {version, metrics, features}
        self._training_jobs = []  # Job history
        self._baseline = None  # Baseline model metrics

    def define_feature(
        self,
        name: str,
        input_field: str,
        transform: str  # "normalize", "one_hot", "log"
    ) -> None:
        """Define feature engineering step"""
        self._features.append({
            "name": name,
            "input_field": input_field,
            "transform": transform,
            "order": len(self._features)
        })

    def compute_features(self, raw_data: Dict) -> Dict:
        """Apply feature transformations"""
        features = {}

        for feature in self._features:
            value = raw_data.get(feature["input_field"])

            if feature["transform"] == "normalize":
                features[feature["name"]] = (value - 50) / 50  # dummy normalization

            elif feature["transform"] == "one_hot":
                features[f"{feature['name']}_true"] = 1 if value else 0

            elif feature["transform"] == "log":
                features[feature["name"]] = __import__("math").log(max(value, 0.001))

        return features

    def train_model(
        self,
        training_data: List[Dict],
        model_type: str = "linear_regression"
    ) -> str:
        """Train model on featured data"""
        job_id = f"train-{datetime.utcnow().timestamp()}"

        # Extract features for all training data
        featured_data = [self.compute_features(row) for row in training_data]

        model = {
            "id": f"model-{len(self._models)}",
            "job_id": job_id,
            "type": model_type,
            "version": len(self._models) + 1,
            "features_used": len(self._features),
            "training_samples": len(featured_data),
            "trained_at": datetime.utcnow().isoformat(),
            "metrics": {
                "accuracy": 0.92,  # Simplified
                "precision": 0.91,
                "recall": 0.89,
                "f1": 0.90
            },
            "status": "ready"
        }

        model_id = model["id"]
        self._models[model_id] = model
        self._training_jobs.append({
            "job_id": job_id,
            "model_id": model_id,
            "status": "completed"
        })

        return model_id

    def evaluate_model(self, model_id: str) -> Dict:
        """Evaluate model against baseline"""
        model = self._models.get(model_id)
        if not model:
            return None

        if not self._baseline:
            self._baseline = model["metrics"]
            comparison = "BASELINE (first model)"
        else:
            improvement = (model["metrics"]["f1"] - self._baseline["f1"]) / self._baseline["f1"]
            comparison = f"IMPROVED {improvement*100:.1f}%" if improvement > 0 else f"DEGRADED {abs(improvement)*100:.1f}%"

        return {
            "model_id": model_id,
            "metrics": model["metrics"],
            "comparison": comparison,
            "ready_for_deployment": improvement > 0 if improvement else True
        }

    def register_model(
        self,
        model_id: str,
        stage: str = "dev"  # dev, staging, production
    ) -> None:
        """Register model for deployment"""
        if model_id in self._models:
            self._models[model_id]["stage"] = stage

    def get_production_model(self) -> Optional[Dict]:
        """Get current production model"""
        for model in self._models.values():
            if model.get("stage") == "production":
                return model

        return None

    def rollback_model(self, previous_model_id: str) -> None:
        """Rollback to previous model"""
        for model in self._models.values():
            if model.get("stage") == "production":
                model["stage"] = "dev"

        if previous_model_id in self._models:
            self._models[previous_model_id]["stage"] = "production"

    def get_training_history(self) -> List[Dict]:
        """Get training job history"""
        return self._training_jobs
'''

    return pipeline


def generate_training_system() -> dict:
    """Generate complete ML training pipeline system."""

    imports = '''from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass


'''

    module_doc = '''"""
Phase 5 ML Training Pipeline: Feature Engineering & Orchestration

End-to-end ML workflows with feature management and model registry.

PIPELINE STAGES:

1. FEATURE ENGINEERING
   Input: raw data {age: 25, income: 50000, employed: true}

   Define features:
   - age_normalized = (age - mean) / std
   - income_log = log(income)
   - is_employed = 1 if employed else 0

   Output: {age_normalized: 0.5, income_log: 10.8, is_employed: 1}

2. TRAINING
   Input: featured data
   Algorithm: linear regression, decision tree, neural network
   Output: trained model (weights, parameters)

3. EVALUATION
   Input: model, test data
   Metrics: accuracy, precision, recall, F1
   Compare: new model vs baseline
   Result: improved/degraded

4. REGISTRATION
   Status stages:
   - dev: candidate model
   - staging: testing in shadow traffic
   - production: live, serving real requests

5. MONITORING
   Track: prediction latency, error rate, data drift
   Alert: if accuracy drops below threshold
   Action: retrain, rollback, or investigate

WORKFLOW:

Week 1: Data collection
- Gather training data (historical transactions, labels)
- Clean, normalize

Week 2: Feature engineering
- Domain expert: define features
- Data scientist: implement transformations
- Validate: features useful for prediction

Week 3: Training
- Split: 80% train, 20% test
- Train model: fit on training set
- Evaluate: measure on test set (F1 = 0.92)
- Compare baseline: improvement? proceed

Week 4: Staging
- Register model: stage = staging
- Deploy: shadow traffic (10% to new, 90% to baseline)
- Monitor: latency, predictions, errors
- Decision: good? promote to production

Week 5: Production
- Register model: stage = production
- Deploy: blue-green switch
- Monitor: live traffic
- Alert: if F1 < 0.90, possible retrain

HYPERPARAMETER TUNING:

Grid search: try combinations
- Learning rate: [0.001, 0.01, 0.1]
- Batch size: [16, 32, 64]
- Layers: [1, 2, 3]
- Result: 27 models trained, best one selected

COMMON PITFALLS:

❌ Data leakage: test features use data from test set
   → Model seems great (99% accurate) but fails in production
   → Solution: strictly separate train/test, encode features on train only

❌ Class imbalance: 99% negative, 1% positive
   → Model predicts all negative (99% accurate but useless)
   → Solution: stratified split, weighted loss, SMOTE

❌ Concept drift: model trained on 2020 data, deployed 2026
   → World changed, data distribution changed
   → Solution: monitor for drift, retrain on recent data

❌ No baseline: improve by 1%... to what?
   → Solution: always track baseline, measure % improvement

DEPLOYMENT STRATEGIES:

Blue-Green:
- Blue (old model): 100% traffic
- Green (new model): 0% traffic
- Test green in isolation
- Switch: green → 100% traffic
- Fast rollback: switch back to blue

Canary:
- Old model: 95% traffic
- New model: 5% traffic
- Monitor metrics
- If good: 10%, 50%, 100%
- If bad: rollback to 0%

Shadow:
- Old model: 100% traffic, return response
- New model: 100% traffic, discard response
- Compare predictions offline
- Zero risk deployment
"""
'''

    pipeline = generate_ml_training_pipeline()

    complete_code = imports + module_doc + "\n" + pipeline

    return {
        "code": complete_code,
        "pattern": "ML Training Pipeline",
        "module": "phase5_ml_training_pipeline.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate ML training pipeline")
    args = parser.parse_args()
    result = generate_training_system()
    print(result["code"])


if __name__ == "__main__":
    main()
