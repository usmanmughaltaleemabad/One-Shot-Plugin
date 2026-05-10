"""
Queue Selector - Auto-detect and configure job queues

Detects:
- Celery (Django/FastAPI)
- RQ (Redis Queue)
- Bull (Node.js)
- Google Cloud Tasks
- AWS SQS
"""

from typing import Dict, Any, Optional


class QueueDetector:
    """Detect and select appropriate job queue"""

    QUEUE_INDICATORS = {
        "celery": ["celery", "beat", "celery_config"],
        "rq": ["rq", "redis", "RQ_"],
        "bull": ["bull", "ioredis", "package.json"],
        "gcloud_tasks": ["google.cloud.tasks", "gcloud"],
        "sqs": ["boto3", "botocore", "AWS_"],
    }

    @staticmethod
    def detect_from_codebase(project_path: str) -> str:
        """Detect queue system from codebase"""
        # Check for celery
        indicators = {
            "celery": 0,
            "rq": 0,
            "bull": 0,
            "gcloud_tasks": 0,
            "sqs": 0,
        }

        # In real implementation, scan project files
        # For now, return most likely based on framework

        return "celery"  # Default

    @staticmethod
    def get_queue_config(queue_type: str, framework: str) -> Dict[str, Any]:
        """Get queue configuration"""
        configs = {
            "celery": {
                "broker_url": "redis://localhost:6379/0",
                "result_backend": "redis://localhost:6379/0",
                "task_serializer": "json",
                "timezone": "UTC",
            },
            "rq": {
                "redis_host": "localhost",
                "redis_port": 6379,
                "redis_db": 0,
                "default_result_ttl": 500,
            },
            "bull": {
                "redis_host": "localhost",
                "redis_port": 6379,
                "defaultJobOptions": {
                    "attempts": 3,
                    "backoff": {"type": "exponential", "delay": 2000},
                },
            },
        }

        return configs.get(queue_type, {})


def generate_queue_selector(framework: str, language: str) -> Dict[str, str]:
    """
    Generate queue selector code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript, go

    Returns: dict of {filename: code_content}
    """
    output = {}

    if language == "python":
        output["queue_selector.py"] = """
from queue_detector import QueueDetector

# Auto-detect queue
detected_queue = QueueDetector.detect_from_codebase('.')
print(f'Detected queue: {detected_queue}')

# Get configuration
config = QueueDetector.get_queue_config(detected_queue, 'django')
print(f'Queue config: {config}')
"""
    elif language == "javascript":
        output["queue_selector.js"] = """
import { QueueDetector } from './queue_detector.js';

// Auto-detect queue
const detectedQueue = QueueDetector.detectFromCodebase('.');
console.log(`Detected queue: ${detectedQueue}`);

// Get configuration
const config = QueueDetector.getQueueConfig(detectedQueue, 'fastapi');
console.log(`Queue config: ${JSON.stringify(config)}`);
"""

    return output
