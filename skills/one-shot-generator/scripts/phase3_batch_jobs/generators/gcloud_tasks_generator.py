"""
Google Cloud Tasks Queue Generator - Cloud-native job queue for Python and Node.js

Generates Cloud Tasks infrastructure:
- Cloud Tasks queue configuration
- Python client SDK integration
- Node.js client SDK integration
- Cloud Tasks HTTP target handlers
- IAM and authentication setup
"""

from typing import Dict


def generate_gcloud_tasks_python_config() -> Dict[str, str]:
    """Generate Python Google Cloud Tasks configuration"""
    return {
        "gcloud_tasks_config.py": '''"""
Google Cloud Tasks Configuration - Cloud-native job queue

Requires:
- google-cloud-tasks>=2.0.0
- google-auth>=2.0.0
"""

import os
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
import json
from datetime import datetime, timedelta


class GoogleCloudTasksQueue:
    """Google Cloud Tasks queue client"""

    def __init__(
        self,
        project_id: str = None,
        queue_name: str = "default",
        location: str = "us-central1"
    ):
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.queue_name = queue_name
        self.location = location
        self.client = tasks_v2.CloudTasksClient()
        self.parent = self.client.queue_path(self.project_id, self.location, queue_name)

    def enqueue_http_task(
        self,
        http_method: str,
        url: str,
        headers: dict = None,
        body: dict = None,
        schedule_time: datetime = None,
        task_name: str = None
    ) -> str:
        """
        Enqueue an HTTP task to Cloud Tasks

        Args:
            http_method: GET, POST, PUT, DELETE
            url: Target HTTP endpoint (must be public or have proper auth)
            headers: HTTP headers to send
            body: Request body (will be JSON-serialized)
            schedule_time: When to execute (default: immediately)
            task_name: Optional custom task name

        Returns: Task name
        """
        task = {
            "http_request": {
                "http_method": http_method,
                "url": url,
            }
        }

        if headers:
            task["http_request"]["headers"] = headers

        if body:
            task["http_request"]["headers"] = task["http_request"].get("headers", {})
            task["http_request"]["headers"]["Content-Type"] = "application/json"
            task["http_request"]["body"] = json.dumps(body).encode()

        if schedule_time:
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(schedule_time)
            task["schedule_time"] = timestamp

        if task_name:
            task["name"] = self.client.task_path(
                self.project_id, self.location, self.queue_name, task_name
            )

        response = self.client.create_task(request={"parent": self.parent, "task": task})
        return response.name

    def enqueue_scheduled_task(
        self,
        http_method: str,
        url: str,
        headers: dict = None,
        body: dict = None,
        delay_seconds: int = 60
    ) -> str:
        """Schedule a task for later execution"""
        schedule_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
        return self.enqueue_http_task(
            http_method=http_method,
            url=url,
            headers=headers,
            body=body,
            schedule_time=schedule_time
        )

    def get_task(self, task_name: str) -> dict:
        """Get task details"""
        return self.client.get_task(request={"name": task_name})

    def delete_task(self, task_name: str) -> None:
        """Delete a task"""
        self.client.delete_task(request={"name": task_name})

    def list_tasks(self) -> list:
        """List all tasks in queue"""
        tasks = self.client.list_tasks(request={"parent": self.parent})
        return list(tasks)


# Queue factory
def create_queue(project_id: str = None, queue_name: str = "default") -> GoogleCloudTasksQueue:
    """Create a Cloud Tasks queue client"""
    return GoogleCloudTasksQueue(project_id=project_id, queue_name=queue_name)
''',
        "requirements_gcloud.txt": '''google-cloud-tasks>=2.0.0
google-auth>=2.0.0
google-auth-httplib2>=0.1.0
google-auth-oauthlib>=0.4.0
''',
        "gcloud_tasks_handler.py": '''"""
Google Cloud Tasks HTTP Task Handler

Flask/FastAPI handler for receiving Cloud Tasks HTTP push requests
"""

from functools import wraps
from typing import Callable
import json
import logging


logger = logging.getLogger(__name__)


class CloudTasksHandler:
    """Handler for Google Cloud Tasks HTTP push requests"""

    def __init__(self, oidc_token: str = None):
        self.oidc_token = oidc_token

    def verify_task_request(self, request) -> bool:
        """
        Verify that the request came from Cloud Tasks
        In production, verify the OIDC token or Cloud Tasks header
        """
        # Check for Cloud Tasks header
        return "X-CloudTasks-TaskName" in request.headers or "X-CloudTasks-QueueName" in request.headers

    def handle_task(self, request) -> dict:
        """Handle incoming Cloud Tasks HTTP push"""
        if not self.verify_task_request(request):
            return {"error": "Invalid request"}, 400

        task_name = request.headers.get("X-CloudTasks-TaskName", "unknown")
        queue_name = request.headers.get("X-CloudTasks-QueueName", "unknown")

        try:
            # Parse task payload
            payload = request.get_json() if request.is_json else {}
            logger.info(f"Executing task: {task_name} from queue: {queue_name}")

            # Execute task logic here
            result = self.execute_task(payload)

            logger.info(f"Task {task_name} completed successfully")
            return {"success": True, "result": result}, 200

        except Exception as e:
            logger.error(f"Task {task_name} failed: {str(e)}")
            # Return 500 to trigger Cloud Tasks retry
            return {"error": str(e)}, 500

    def execute_task(self, payload: dict) -> dict:
        """Override this method to implement task logic"""
        raise NotImplementedError("Subclasses must implement execute_task()")


# Flask integration
def handle_cloud_task(handler: CloudTasksHandler) -> Callable:
    """Flask decorator for Cloud Tasks routes"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Delegate to handler
            return handler.handle_task(*args, **kwargs)
        return decorated_function
    return decorator
''',
    }


def generate_gcloud_tasks_nodejs_config() -> Dict[str, str]:
    """Generate Node.js Google Cloud Tasks configuration"""
    return {
        "gcloud-tasks-config.js": '''"""
Google Cloud Tasks Configuration - Node.js Client

Requires:
- @google-cloud/tasks
- google-auth-library
"""

const cloudTasks = require("@google-cloud/tasks");
const { v2 } = require("@google-cloud/tasks");

class GoogleCloudTasksQueue {
    constructor(projectId, queueName = "default", location = "us-central1") {
        this.projectId = projectId || process.env.GCP_PROJECT_ID;
        this.queueName = queueName;
        this.location = location;
        this.client = new v2.CloudTasksClient();
        this.parent = this.client.queuePath(this.projectId, this.location, queueName);
    }

    async enqueueHttpTask(method, url, headers = {}, body = null) {
        const task = {
            httpRequest: {
                httpMethod: method,
                url: url,
                headers: headers,
            },
        };

        if (body) {
            task.httpRequest.headers["Content-Type"] = "application/json";
            task.httpRequest.body = Buffer.from(JSON.stringify(body)).toString("base64");
        }

        const request = {
            parent: this.parent,
            task: task,
        };

        const [response] = await this.client.createTask(request);
        return response.name;
    }

    async enqueueScheduledTask(method, url, headers = {}, body = null, delaySeconds = 60) {
        const scheduleTime = new Date();
        scheduleTime.setSeconds(scheduleTime.getSeconds() + delaySeconds);

        const task = {
            httpRequest: {
                httpMethod: method,
                url: url,
                headers: headers,
            },
            scheduleTime: scheduleTime,
        };

        if (body) {
            task.httpRequest.headers["Content-Type"] = "application/json";
            task.httpRequest.body = Buffer.from(JSON.stringify(body)).toString("base64");
        }

        const request = {
            parent: this.parent,
            task: task,
        };

        const [response] = await this.client.createTask(request);
        return response.name;
    }

    async getTask(taskName) {
        const [task] = await this.client.getTask({ name: taskName });
        return task;
    }

    async deleteTask(taskName) {
        await this.client.deleteTask({ name: taskName });
    }

    async listTasks() {
        const [tasks] = await this.client.listTasks({ parent: this.parent });
        return tasks || [];
    }
}

module.exports = { GoogleCloudTasksQueue };
''',
        "package-gcloud.json": '''{
  "name": "gcloud-tasks-integration",
  "version": "1.0.0",
  "dependencies": {
    "@google-cloud/tasks": "^3.0.0",
    "google-auth-library": "^8.0.0"
  }
}
''',
    }


def generate_gcloud_tasks(framework: str, language: str, job_name: str = None) -> Dict[str, str]:
    """Generate complete Google Cloud Tasks infrastructure"""
    output = {}
    job_name = job_name or "default_job"

    if language == "python":
        output.update(generate_gcloud_tasks_python_config())
        output["setup_gcloud_tasks.sh"] = '''#!/bin/bash
# Setup Google Cloud Tasks

# Set up your GCP project
export GCP_PROJECT_ID="your-project-id"

# Create a Cloud Tasks queue
gcloud tasks queues create {queue_name} \\
  --location=us-central1 \\
  --project=$GCP_PROJECT_ID

# Set up authentication
gcloud auth application-default login

# Install Python client
pip install google-cloud-tasks google-auth
'''.format(queue_name=job_name)

    else:
        output.update(generate_gcloud_tasks_nodejs_config())
        output["setup-gcloud-tasks.sh"] = '''#!/bin/bash
# Setup Google Cloud Tasks

# Set up your GCP project
export GCP_PROJECT_ID="your-project-id"

# Create a Cloud Tasks queue
gcloud tasks queues create {queue_name} \\
  --location=us-central1 \\
  --project=$GCP_PROJECT_ID

# Set up authentication
gcloud auth application-default login

# Install Node.js client
npm install @google-cloud/tasks
'''.format(queue_name=job_name)

    output["GCLOUD_TASKS_SETUP.md"] = '''# Google Cloud Tasks Queue Setup

## Prerequisites

1. Google Cloud Platform account
2. Project with Cloud Tasks API enabled
3. Appropriate IAM roles (Cloud Tasks Admin, Cloud Tasks Enqueuer)

## Quick Start

### 1. Enable Cloud Tasks API
```bash
gcloud services enable cloudtasks.googleapis.com
```

### 2. Create a Queue
```bash
gcloud tasks queues create {queue_name} \\
  --location=us-central1 \\
  --max-tasks-per-second=100
```

### 3. Deploy HTTP Handler
Your HTTP handler must be accessible from Google Cloud.
Set the handler URL in your enqueue_http_task() call.

### 4. Set Up Authentication

**Option A: Application Default Credentials (Development)**
```bash
gcloud auth application-default login
```

**Option B: Service Account (Production)**
```bash
gcloud iam service-accounts create cloud-tasks-service \\
  --display-name="Cloud Tasks Service"

gcloud projects add-iam-policy-binding PROJECT_ID \\
  --member=serviceAccount:cloud-tasks-service@PROJECT_ID.iam.gserviceaccount.com \\
  --role=roles/cloudtasks.enqueuer

gcloud iam service-accounts keys create key.json \\
  --iam-account=cloud-tasks-service@PROJECT_ID.iam.gserviceaccount.com

export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/key.json"
```

## Configuration

### Queue Options
- **Max tasks per second:** Rate at which tasks are dispatched
- **Retry:** Automatic retry with exponential backoff
- **Dead letter queue:** Route failed tasks (after retries)

### Task Lifecycle

1. **Enqueued** — Added to queue
2. **Dispatched** — Sent to HTTP endpoint
3. **Completed** — Handler returned 200-299 status
4. **Failed** — Handler returned non-2xx status
5. **Retried** — Automatic retry based on policy
6. **Dead lettered** — After max retries

## Pricing

Cloud Tasks pricing:
- **Task operations:** $0.40 per million operations
- **Additional API calls:** $0.10 per million operations

## Advantages over Self-Hosted

✅ Fully managed (no infrastructure to maintain)
✅ Auto-scaling (handles traffic spikes)
✅ Built-in retries & dead letter queues
✅ Integrated with Google Cloud ecosystem
✅ HIPAA, SOC 2, PCI-DSS compliant

## Disadvantages

❌ No local testing without emulator (use emulator image)
❌ Vendor lock-in to GCP
❌ Network latency to invoke external HTTP handlers
'''

    return output
