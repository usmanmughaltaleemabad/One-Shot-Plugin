"""
AWS SQS Queue Generator - Managed message queue for Python and Node.js

Generates SQS infrastructure:
- SQS queue configuration
- Python client SDK integration
- Node.js client SDK integration
- SQS message producers and consumers
- IAM and authentication setup
"""

from typing import Dict


def generate_aws_sqs_python_config() -> Dict[str, str]:
    """Generate Python AWS SQS configuration"""
    return {
        "aws_sqs_config.py": '''"""
AWS SQS Configuration - Managed message queue

Requires:
- boto3>=1.26.0
- botocore>=1.29.0
"""

import os
import json
import boto3
from typing import Dict, List, Optional
from datetime import datetime


class AWSQueue:
    """AWS SQS queue client"""

    def __init__(
        self,
        queue_name: str = "default",
        region: str = None,
        aws_access_key: str = None,
        aws_secret_key: str = None
    ):
        self.queue_name = queue_name
        self.region = region or os.getenv("AWS_REGION", "us-east-1")

        # Initialize SQS client
        session_kwargs = {"region_name": self.region}
        if aws_access_key and aws_secret_key:
            session_kwargs["aws_access_key_id"] = aws_access_key
            session_kwargs["aws_secret_access_key"] = aws_secret_key

        self.sqs = boto3.client("sqs", **session_kwargs)
        self.queue_url = self._get_queue_url()

    def _get_queue_url(self) -> str:
        """Get queue URL from queue name"""
        response = self.sqs.get_queue_url(QueueName=self.queue_name)
        return response["QueueUrl"]

    def send_message(
        self,
        message_body: Dict = None,
        message_attributes: Dict = None,
        delay_seconds: int = 0,
        deduplication_id: str = None,
        group_id: str = None
    ) -> str:
        """
        Send a message to SQS queue

        Args:
            message_body: Message content (will be JSON-serialized)
            message_attributes: Message attributes (metadata)
            delay_seconds: Delay delivery (0-900 seconds)
            deduplication_id: For FIFO queues (deduplication)
            group_id: For FIFO queues (message group)

        Returns: Message ID
        """
        if message_body is None:
            message_body = {}

        # Prepare request
        request = {
            "QueueUrl": self.queue_url,
            "MessageBody": json.dumps(message_body),
        }

        if message_attributes:
            request["MessageAttributes"] = message_attributes

        if delay_seconds > 0:
            request["DelaySeconds"] = min(delay_seconds, 900)

        if deduplication_id:
            request["MessageDeduplicationId"] = deduplication_id

        if group_id:
            request["MessageGroupId"] = group_id

        response = self.sqs.send_message(**request)
        return response["MessageId"]

    def send_batch(self, messages: List[Dict]) -> Dict:
        """
        Send multiple messages in a batch

        Args:
            messages: List of {body, attributes, delay_seconds, dedup_id, group_id}

        Returns: Response with successful and failed messages
        """
        entries = []
        for idx, msg in enumerate(messages):
            entry = {
                "Id": str(idx),
                "MessageBody": json.dumps(msg.get("body", {}))
            }

            if msg.get("delay_seconds"):
                entry["DelaySeconds"] = msg["delay_seconds"]
            if msg.get("dedup_id"):
                entry["MessageDeduplicationId"] = msg["dedup_id"]
            if msg.get("group_id"):
                entry["MessageGroupId"] = msg["group_id"]
            if msg.get("attributes"):
                entry["MessageAttributes"] = msg["attributes"]

            entries.append(entry)

        response = self.sqs.send_message_batch(
            QueueUrl=self.queue_url,
            Entries=entries
        )
        return response

    def receive_messages(
        self,
        max_messages: int = 1,
        wait_seconds: int = 0,
        visibility_timeout: int = 30
    ) -> List[Dict]:
        """
        Receive messages from queue

        Args:
            max_messages: Max messages to receive (1-10)
            wait_seconds: Long polling duration (0-20)
            visibility_timeout: Message visibility timeout (seconds)

        Returns: List of messages with metadata
        """
        response = self.sqs.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=min(max_messages, 10),
            WaitTimeSeconds=min(wait_seconds, 20),
            VisibilityTimeout=visibility_timeout,
            MessageAttributeNames=["All"]
        )

        messages = []
        for msg in response.get("Messages", []):
            messages.append({
                "id": msg["MessageId"],
                "receipt_handle": msg["ReceiptHandle"],
                "body": json.loads(msg["MessageBody"]),
                "attributes": msg.get("Attributes", {}),
                "message_attributes": msg.get("MessageAttributes", {})
            })

        return messages

    def delete_message(self, receipt_handle: str) -> None:
        """Delete a message from queue"""
        self.sqs.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=receipt_handle
        )

    def delete_messages(self, receipt_handles: List[str]) -> Dict:
        """Delete multiple messages"""
        entries = [
            {"Id": str(idx), "ReceiptHandle": handle}
            for idx, handle in enumerate(receipt_handles)
        ]

        response = self.sqs.delete_message_batch(
            QueueUrl=self.queue_url,
            Entries=entries
        )
        return response

    def change_message_visibility(
        self,
        receipt_handle: str,
        visibility_timeout: int
    ) -> None:
        """Change message visibility timeout"""
        self.sqs.change_message_visibility(
            QueueUrl=self.queue_url,
            ReceiptHandle=receipt_handle,
            VisibilityTimeout=visibility_timeout
        )

    def get_queue_attributes(self) -> Dict:
        """Get queue attributes"""
        response = self.sqs.get_queue_attributes(
            QueueUrl=self.queue_url,
            AttributeNames=["All"]
        )
        return response["Attributes"]

    def purge_queue(self) -> None:
        """Purge all messages from queue"""
        self.sqs.purge_queue(QueueUrl=self.queue_url)

    def delete_queue(self) -> None:
        """Delete the queue"""
        self.sqs.delete_queue(QueueUrl=self.queue_url)


def create_queue(queue_name: str = "default", region: str = None) -> AWSQueue:
    """Create an SQS queue client"""
    return AWSQueue(queue_name=queue_name, region=region)
''',
        "requirements_aws.txt": '''boto3>=1.26.0
botocore>=1.29.0
''',
        "aws_sqs_consumer.py": '''"""
AWS SQS Consumer - Worker for processing SQS messages
"""

import json
import logging
import time
from typing import Callable, Dict
from aws_sqs_config import AWSQueue


logger = logging.getLogger(__name__)


class SQSConsumer:
    """Consume and process messages from SQS queue"""

    def __init__(
        self,
        queue_name: str = "default",
        region: str = None,
        handler: Callable = None,
        max_messages: int = 10,
        wait_seconds: int = 20,
        visibility_timeout: int = 300
    ):
        self.queue = AWSQueue(queue_name=queue_name, region=region)
        self.handler = handler
        self.max_messages = max_messages
        self.wait_seconds = wait_seconds
        self.visibility_timeout = visibility_timeout
        self.running = False

    def process_message(self, message: Dict) -> bool:
        """Process a single message"""
        try:
            if self.handler:
                result = self.handler(message["body"])
                logger.info(f"Processed message {message['id']}: {result}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error processing message {message['id']}: {str(e)}")
            # Increase visibility timeout on error for retry
            self.queue.change_message_visibility(
                message["receipt_handle"],
                self.visibility_timeout * 2
            )
            return False

    def run(self, max_iterations: int = None):
        """Run consumer loop"""
        self.running = True
        iteration = 0

        while self.running:
            iteration += 1
            if max_iterations and iteration > max_iterations:
                break

            try:
                messages = self.queue.receive_messages(
                    max_messages=self.max_messages,
                    wait_seconds=self.wait_seconds,
                    visibility_timeout=self.visibility_timeout
                )

                if not messages:
                    logger.debug("No messages received, waiting...")
                    continue

                # Process messages
                to_delete = []
                for message in messages:
                    if self.process_message(message):
                        to_delete.append(message["receipt_handle"])

                # Delete successfully processed messages
                if to_delete:
                    self.queue.delete_messages(to_delete)
                    logger.info(f"Deleted {len(to_delete)} processed messages")

            except KeyboardInterrupt:
                logger.info("Consumer interrupted by user")
                self.running = False
            except Exception as e:
                logger.error(f"Consumer error: {str(e)}")
                time.sleep(5)  # Backoff on error

    def stop(self):
        """Stop the consumer"""
        self.running = False
        logger.info("Consumer stopped")


def create_consumer(
    queue_name: str = "default",
    handler: Callable = None,
    region: str = None
) -> SQSConsumer:
    """Create an SQS consumer"""
    return SQSConsumer(
        queue_name=queue_name,
        handler=handler,
        region=region
    )
''',
    }


def generate_aws_sqs_nodejs_config() -> Dict[str, str]:
    """Generate Node.js AWS SQS configuration"""
    return {
        "aws-sqs-config.js": '''"""
AWS SQS Configuration - Node.js Client

Requires:
- @aws-sdk/client-sqs
- @aws-sdk/credential-providers
"""

const { SQSClient, SendMessageCommand, ReceiveMessageCommand, DeleteMessageCommand } = require("@aws-sdk/client-sqs");

class AWSQueue {
    constructor(queueName = "default", region = null) {
        this.queueName = queueName;
        this.region = region || process.env.AWS_REGION || "us-east-1";

        this.client = new SQSClient({ region: this.region });
        this.queueUrl = null;
    }

    async init() {
        // In production, resolve queue URL via GetQueueUrl API
        // For now, construct from account ID and region
        const accountId = process.env.AWS_ACCOUNT_ID || "123456789012";
        this.queueUrl = `https://sqs.${this.region}.amazonaws.com/${accountId}/${this.queueName}`;
        return this.queueUrl;
    }

    async sendMessage(messageBody = {}, options = {}) {
        const command = new SendMessageCommand({
            QueueUrl: this.queueUrl,
            MessageBody: JSON.stringify(messageBody),
            DelaySeconds: options.delaySeconds || 0,
            MessageAttributes: options.messageAttributes || {},
            ...(options.deduplicationId && { MessageDeduplicationId: options.deduplicationId }),
            ...(options.groupId && { MessageGroupId: options.groupId }),
        });

        try {
            const response = await this.client.send(command);
            return response.MessageId;
        } catch (error) {
            console.error("Error sending message:", error);
            throw error;
        }
    }

    async sendBatch(messages = []) {
        // Use batch endpoint for multiple messages
        const entries = messages.map((msg, idx) => ({
            Id: String(idx),
            MessageBody: JSON.stringify(msg.body || {}),
            DelaySeconds: msg.delaySeconds || 0,
            ...(msg.deduplicationId && { MessageDeduplicationId: msg.deduplicationId }),
            ...(msg.groupId && { MessageGroupId: msg.groupId }),
            MessageAttributes: msg.attributes || {},
        }));

        // Note: Use SendMessageBatch command
        // This is a simplified example
        const results = [];
        for (const entry of entries) {
            const command = new SendMessageCommand({
                QueueUrl: this.queueUrl,
                ...entry
            });
            const response = await this.client.send(command);
            results.push(response.MessageId);
        }
        return results;
    }

    async receiveMessages(options = {}) {
        const command = new ReceiveMessageCommand({
            QueueUrl: this.queueUrl,
            MaxNumberOfMessages: Math.min(options.maxMessages || 1, 10),
            WaitTimeSeconds: Math.min(options.waitSeconds || 0, 20),
            VisibilityTimeout: options.visibilityTimeout || 30,
            MessageAttributeNames: ["All"],
        });

        try {
            const response = await this.client.send(command);
            return (response.Messages || []).map(msg => ({
                id: msg.MessageId,
                receiptHandle: msg.ReceiptHandle,
                body: JSON.parse(msg.Body),
                attributes: msg.Attributes || {},
                messageAttributes: msg.MessageAttributes || {},
            }));
        } catch (error) {
            console.error("Error receiving messages:", error);
            throw error;
        }
    }

    async deleteMessage(receiptHandle) {
        const command = new DeleteMessageCommand({
            QueueUrl: this.queueUrl,
            ReceiptHandle: receiptHandle,
        });

        try {
            await this.client.send(command);
        } catch (error) {
            console.error("Error deleting message:", error);
            throw error;
        }
    }

    async deleteMessages(receiptHandles = []) {
        // Batch delete
        const entries = receiptHandles.map((handle, idx) => ({
            Id: String(idx),
            ReceiptHandle: handle,
        }));

        // Use DeleteMessageBatch command
        // Simplified: delete one by one
        for (const handle of receiptHandles) {
            await this.deleteMessage(handle);
        }
        return { Successful: receiptHandles.length, Failed: 0 };
    }

    async changeMessageVisibility(receiptHandle, visibilityTimeout) {
        // Implementation using ChangeMessageVisibility API
        console.log(`Changing visibility for ${receiptHandle} to ${visibilityTimeout}s`);
    }

    async purgeQueue() {
        console.log("Purging queue not implemented - would delete all messages");
    }

    async deleteQueue() {
        console.log("Deleting queue not implemented - would delete the queue");
    }
}

async function createQueue(queueName = "default", region = null) {
    const queue = new AWSQueue(queueName, region);
    await queue.init();
    return queue;
}

module.exports = { AWSQueue, createQueue };
''',
        "package-aws.json": '''{
  "name": "aws-sqs-integration",
  "version": "1.0.0",
  "dependencies": {
    "@aws-sdk/client-sqs": "^3.0.0",
    "@aws-sdk/credential-providers": "^3.0.0"
  }
}
''',
    }


def generate_aws_sqs(framework: str, language: str, queue_name: str = None) -> Dict[str, str]:
    """Generate complete AWS SQS infrastructure"""
    output = {}
    queue_name = queue_name or "default_queue"

    if language == "python":
        output.update(generate_aws_sqs_python_config())
        output["setup_aws_sqs.sh"] = '''#!/bin/bash
# Setup AWS SQS

# Set up AWS credentials
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID="your-account-id"

# Create SQS queue
aws sqs create-queue \\
  --queue-name {queue_name} \\
  --region $AWS_REGION \\
  --attributes "VisibilityTimeout=300"

# Get queue URL
QUEUE_URL=$(aws sqs get-queue-url \\
  --queue-name {queue_name} \\
  --region $AWS_REGION \\
  --query 'QueueUrl' \\
  --output text)

echo "Queue created: $QUEUE_URL"

# Install Python client
pip install boto3 botocore
'''.format(queue_name=queue_name)

    else:
        output.update(generate_aws_sqs_nodejs_config())
        output["setup-aws-sqs.sh"] = '''#!/bin/bash
# Setup AWS SQS

# Set up AWS credentials
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID="your-account-id"

# Create SQS queue
aws sqs create-queue \\
  --queue-name {queue_name} \\
  --region $AWS_REGION \\
  --attributes "VisibilityTimeout=300"

# Get queue URL
QUEUE_URL=$(aws sqs get-queue-url \\
  --queue-name {queue_name} \\
  --region $AWS_REGION \\
  --query 'QueueUrl' \\
  --output text)

echo "Queue created: $QUEUE_URL"

# Install Node.js client
npm install @aws-sdk/client-sqs @aws-sdk/credential-providers
'''.format(queue_name=queue_name)

    output["AWS_SQS_SETUP.md"] = '''# AWS SQS Queue Setup

## Prerequisites

1. AWS Account with appropriate permissions
2. AWS CLI configured with credentials
3. IAM user with SQS permissions (sqs:CreateQueue, sqs:SendMessage, sqs:ReceiveMessage, sqs:DeleteMessage)

## Quick Start

### 1. Create Queue
```bash
aws sqs create-queue \\
  --queue-name {queue_name} \\
  --region us-east-1 \\
  --attributes "VisibilityTimeout=300,MessageRetentionPeriod=1209600"
```

### 2. Get Queue URL
```bash
QUEUE_URL=$(aws sqs get-queue-url \\
  --queue-name {queue_name} \\
  --region us-east-1 \\
  --query 'QueueUrl' \\
  --output text)
echo $QUEUE_URL
```

### 3. Set Up Credentials

**Option A: Environment Variables (Development)**
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"
```

**Option B: AWS CLI Profile (Development)**
```bash
aws configure --profile myprofile
export AWS_PROFILE=myprofile
```

**Option C: IAM Role (Production)**
- Attach IAM role with SQS permissions to EC2/ECS/Lambda instance
- No credentials needed; boto3 auto-detects role

## Configuration

### Queue Types
- **Standard Queue:** At-least-once delivery, best effort ordering
- **FIFO Queue:** Exactly-once delivery, strict ordering (slower)

### Queue Attributes
- **VisibilityTimeout:** How long messages are hidden after receive (30-900s)
- **MessageRetentionPeriod:** How long messages stay in queue (60s-1209600s)
- **ReceiveMessageWaitTimeSeconds:** Long polling timeout (0-20s)

### Message Lifecycle

1. **Sent** — Added to queue
2. **Received** — Message becomes invisible (visibility timeout)
3. **Processed** — Application handles message
4. **Deleted** — Message removed from queue
5. **DLQ** — Failed after max retries (optional dead letter queue)

## Pricing

AWS SQS pricing:
- **Requests:** $0.40 per million requests
- **Data transfer:** Standard AWS data transfer rates

## Advantages

✅ Fully managed (no infrastructure)
✅ Auto-scaling (handles traffic spikes)
✅ At-least-once delivery guarantee
✅ Long polling (reduces API calls)
✅ FIFO option for ordering
✅ Dead letter queues
✅ Integration with Lambda, SQS, SNS

## Disadvantages

❌ No local testing without LocalStack
❌ Vendor lock-in to AWS
❌ Visibility timeout complexity (re-queue manually on timeout)
❌ No built-in deduplication (Standard queues)
'''

    return output
