#!/usr/bin/env python3
"""
Tests for Phase 3.1 Cloud Backend Generators (Google Cloud Tasks, AWS SQS)

Tests:
1. Google Cloud Tasks generator creates correct Python output
2. Google Cloud Tasks generator creates correct Node.js output
3. AWS SQS generator creates correct Python output
4. AWS SQS generator creates correct Node.js output
5. Cloud backend routing in orchestrator
6. Queue type detection and selection
7. Cloud backend configuration validation
8. Setup script generation
9. Documentation generation
10. Integration with phase3_runner
"""

import pytest
import sys
import json
from pathlib import Path
from typing import Dict

# Add generators to path
sys.path.insert(0, str(Path(__file__).parent / "generators"))
sys.path.insert(0, str(Path(__file__).parent))

from gcloud_tasks_generator import generate_gcloud_tasks
from aws_sqs_generator import generate_aws_sqs
from orchestrator_phase3 import Phase3Orchestrator, orchestrate_phase3


class TestGoogleCloudTasks:
    """Test Google Cloud Tasks generator"""

    def test_python_config_generation(self):
        """Test Python Google Cloud Tasks config generation"""
        output = generate_gcloud_tasks("django", "python", "test_job")
        assert isinstance(output, dict)
        assert "gcloud_tasks_config.py" in output
        assert "gcloud_tasks_handler.py" in output
        assert "requirements_gcloud.txt" in output
        assert "setup_gcloud_tasks.sh" in output
        assert "GCLOUD_TASKS_SETUP.md" in output

    def test_python_config_content(self):
        """Test Python config contains required classes"""
        output = generate_gcloud_tasks("django", "python", "test_job")
        config_code = output["gcloud_tasks_config.py"]
        assert "class GoogleCloudTasksQueue" in config_code
        assert "def enqueue_http_task" in config_code
        assert "def enqueue_scheduled_task" in config_code
        assert "def get_task" in config_code
        assert "def delete_task" in config_code
        assert "def list_tasks" in config_code

    def test_python_handler_content(self):
        """Test Python handler contains required classes"""
        output = generate_gcloud_tasks("django", "python", "test_job")
        handler_code = output["gcloud_tasks_handler.py"]
        assert "class CloudTasksHandler" in handler_code
        assert "def verify_task_request" in handler_code
        assert "def handle_task" in handler_code
        assert "def execute_task" in handler_code

    def test_nodejs_config_generation(self):
        """Test Node.js Google Cloud Tasks config generation"""
        output = generate_gcloud_tasks("nestjs", "javascript", "test_job")
        assert isinstance(output, dict)
        assert "gcloud-tasks-config.js" in output
        assert "package-gcloud.json" in output
        assert "setup-gcloud-tasks.sh" in output
        assert "GCLOUD_TASKS_SETUP.md" in output

    def test_nodejs_config_content(self):
        """Test Node.js config contains required classes"""
        output = generate_gcloud_tasks("nestjs", "javascript", "test_job")
        config_code = output["gcloud-tasks-config.js"]
        assert "class GoogleCloudTasksQueue" in config_code
        assert "enqueueHttpTask" in config_code
        assert "enqueueScheduledTask" in config_code
        assert "getTask" in config_code
        assert "deleteTask" in config_code

    def test_setup_script(self):
        """Test setup script generation"""
        output = generate_gcloud_tasks("django", "python", "test_queue")
        setup = output["setup_gcloud_tasks.sh"]
        assert "gcloud tasks queues create test_queue" in setup
        assert "GCP_PROJECT_ID" in setup
        assert "pip install google-cloud-tasks" in setup

    def test_documentation(self):
        """Test documentation generation"""
        output = generate_gcloud_tasks("django", "python", "test_job")
        docs = output["GCLOUD_TASKS_SETUP.md"]
        assert "Google Cloud Tasks Queue Setup" in docs
        assert "Prerequisites" in docs
        assert "Quick Start" in docs
        assert "Configuration" in docs
        assert "Pricing" in docs


class TestAWSSQS:
    """Test AWS SQS generator"""

    def test_python_config_generation(self):
        """Test Python AWS SQS config generation"""
        output = generate_aws_sqs("django", "python", "test_queue")
        assert isinstance(output, dict)
        assert "aws_sqs_config.py" in output
        assert "aws_sqs_consumer.py" in output
        assert "requirements_aws.txt" in output
        assert "setup_aws_sqs.sh" in output
        assert "AWS_SQS_SETUP.md" in output

    def test_python_config_content(self):
        """Test Python config contains required classes"""
        output = generate_aws_sqs("django", "python", "test_queue")
        config_code = output["aws_sqs_config.py"]
        assert "class AWSQueue" in config_code
        assert "def send_message" in config_code
        assert "def send_batch" in config_code
        assert "def receive_messages" in config_code
        assert "def delete_message" in config_code
        assert "def delete_messages" in config_code

    def test_python_consumer_content(self):
        """Test Python consumer contains required classes"""
        output = generate_aws_sqs("django", "python", "test_queue")
        consumer_code = output["aws_sqs_consumer.py"]
        assert "class SQSConsumer" in consumer_code
        assert "def process_message" in consumer_code
        assert "def run" in consumer_code
        assert "def stop" in consumer_code

    def test_nodejs_config_generation(self):
        """Test Node.js AWS SQS config generation"""
        output = generate_aws_sqs("nestjs", "javascript", "test_queue")
        assert isinstance(output, dict)
        assert "aws-sqs-config.js" in output
        assert "package-aws.json" in output
        assert "setup-aws-sqs.sh" in output
        assert "AWS_SQS_SETUP.md" in output

    def test_nodejs_config_content(self):
        """Test Node.js config contains required classes"""
        output = generate_aws_sqs("nestjs", "javascript", "test_queue")
        config_code = output["aws-sqs-config.js"]
        assert "class AWSQueue" in config_code
        assert "async sendMessage" in config_code
        assert "async receiveMessages" in config_code
        assert "async deleteMessage" in config_code

    def test_setup_script(self):
        """Test setup script generation"""
        output = generate_aws_sqs("django", "python", "test_queue")
        setup = output["setup_aws_sqs.sh"]
        assert "aws sqs create-queue" in setup
        assert "test_queue" in setup
        assert "AWS_REGION" in setup
        assert "pip install boto3" in setup

    def test_documentation(self):
        """Test documentation generation"""
        output = generate_aws_sqs("django", "python", "test_job")
        docs = output["AWS_SQS_SETUP.md"]
        assert "AWS SQS Queue Setup" in docs
        assert "Prerequisites" in docs
        assert "Quick Start" in docs
        assert "Configuration" in docs
        assert "Pricing" in docs


class TestOrchestratorCloudBackendRouting:
    """Test orchestrator routing to cloud backends"""

    def test_gcloud_tasks_routing(self):
        """Test orchestrator routes to gcloud_tasks generator"""
        output = orchestrate_phase3(
            "django",
            "python",
            "test_job",
            queue_type="gcloud_tasks"
        )
        assert isinstance(output, dict)
        assert "gcloud_tasks_config.py" in output
        assert "gcloud_tasks_handler.py" in output

    def test_sqs_routing(self):
        """Test orchestrator routes to AWS SQS generator"""
        output = orchestrate_phase3(
            "django",
            "python",
            "test_job",
            queue_type="sqs"
        )
        assert isinstance(output, dict)
        assert "aws_sqs_config.py" in output
        assert "aws_sqs_consumer.py" in output

    def test_default_routing(self):
        """Test orchestrator uses default routing when no queue_type specified"""
        output = orchestrate_phase3(
            "django",
            "python",
            "test_job"
        )
        # Should generate standard batch job infrastructure (not cloud backend specific)
        assert isinstance(output, dict)
        assert len(output) > 0

    def test_phase3_orchestrator_init(self):
        """Test Phase3Orchestrator accepts queue_type"""
        orch = Phase3Orchestrator("django", "python", "test", queue_type="gcloud_tasks")
        assert orch.queue_type == "gcloud_tasks"
        assert orch.framework == "django"
        assert orch.language == "python"

    def test_phase3_orchestrator_default_queue_type(self):
        """Test Phase3Orchestrator defaults to celery"""
        orch = Phase3Orchestrator("django", "python", "test")
        assert orch.queue_type == "celery"


class TestCloudBackendFrameworks:
    """Test cloud backends with different frameworks"""

    def test_gcloud_tasks_with_django(self):
        """Test Google Cloud Tasks with Django"""
        output = generate_gcloud_tasks("django", "python", "django_job")
        assert len(output) == 5
        assert all(isinstance(v, str) for v in output.values())

    def test_gcloud_tasks_with_fastapi(self):
        """Test Google Cloud Tasks with FastAPI"""
        output = generate_gcloud_tasks("fastapi", "python", "api_job")
        assert len(output) == 5
        assert "gcloud_tasks_config.py" in output

    def test_sqs_with_django(self):
        """Test AWS SQS with Django"""
        output = generate_aws_sqs("django", "python", "django_queue")
        assert len(output) == 5
        assert all(isinstance(v, str) for v in output.values())

    def test_sqs_with_nodejs(self):
        """Test AWS SQS with Node.js"""
        output = generate_aws_sqs("nestjs", "javascript", "node_queue")
        assert len(output) == 4
        assert "aws-sqs-config.js" in output


class TestCloudBackendRequirements:
    """Test dependency requirements"""

    def test_gcloud_tasks_python_requirements(self):
        """Test Python gcloud_tasks requirements"""
        output = generate_gcloud_tasks("django", "python", "job")
        reqs = output["requirements_gcloud.txt"]
        assert "google-cloud-tasks" in reqs
        assert "google-auth" in reqs

    def test_sqs_python_requirements(self):
        """Test Python SQS requirements"""
        output = generate_aws_sqs("django", "python", "queue")
        reqs = output["requirements_aws.txt"]
        assert "boto3" in reqs
        assert "botocore" in reqs

    def test_gcloud_tasks_nodejs_requirements(self):
        """Test Node.js gcloud_tasks requirements"""
        output = generate_gcloud_tasks("nestjs", "javascript", "job")
        pkg_json = json.loads(output["package-gcloud.json"])
        assert "@google-cloud/tasks" in pkg_json["dependencies"]

    def test_sqs_nodejs_requirements(self):
        """Test Node.js SQS requirements"""
        output = generate_aws_sqs("nestjs", "javascript", "queue")
        pkg_json = json.loads(output["package-aws.json"])
        assert "@aws-sdk/client-sqs" in pkg_json["dependencies"]


def run_all_tests():
    """Run all tests"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_all_tests()
