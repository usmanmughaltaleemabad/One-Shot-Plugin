#!/usr/bin/env python3
"""
Phase 5 Real-time/Async: Message Queue

Message Queue: Asynchronous communication between services.

Problem: Synchronous calls = blocking
- OrderService calls PaymentService
- Waits for response (blocks)
- If PaymentService slow: OrderService slow
- If PaymentService down: OrderService fails

Message Queue (solution):
- OrderService sends message: "please process payment"
- Continues immediately (doesn't wait)
- PaymentService processes message asynchronously
- OrderService finds out result later (via callback/polling)

Benefits:
- Loose coupling (services don't need to know each other)
- Resilience (PaymentService can be down, message waits)
- Performance (no blocking)
- Scalability (multiple consumers can process messages)
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime
from collections import deque


def generate_message_queue() -> str:
    """Generate message queue."""

    queue = '''
class MessageQueue:
    """
    Message Queue: Store messages, process asynchronously.

    Producers: Send messages (OrderService)
    Consumers: Receive & process messages (PaymentService)
    Queue: Stores messages until processed
    """

    def __init__(self):
        self._queues = {}  # topic → messages
        self._consumers = {}  # topic → handler functions
        self._processed_messages = []

    def create_topic(self, topic_name: str) -> None:
        """Create message topic"""
        if topic_name not in self._queues:
            self._queues[topic_name] = deque()

    def publish(self, topic: str, message: Dict) -> str:
        """Publish message to topic"""
        if topic not in self._queues:
            self.create_topic(topic)

        message_id = f"msg-{datetime.utcnow().timestamp()}"
        message_obj = {
            "id": message_id,
            "topic": topic,
            "data": message,
            "published_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }

        self._queues[topic].append(message_obj)
        return message_id

    def subscribe(self, topic: str, handler: Callable) -> None:
        """Subscribe to topic (register consumer)"""
        if topic not in self._consumers:
            self._consumers[topic] = []

        self._consumers[topic].append(handler)

    def process_messages(self, topic: str, batch_size: int = 10) -> int:
        """Process pending messages (pull model)"""
        if topic not in self._queues:
            return 0

        processed = 0
        handlers = self._consumers.get(topic, [])

        if not handlers:
            return 0

        while processed < batch_size and self._queues[topic]:
            message = self._queues[topic].popleft()

            # Call all handlers for this topic
            for handler in handlers:
                try:
                    handler(message["data"])
                    message["status"] = "processed"
                except Exception as e:
                    message["status"] = "failed"
                    message["error"] = str(e)

            message["processed_at"] = datetime.utcnow().isoformat()
            self._processed_messages.append(message)
            processed += 1

        return processed

    def get_pending_count(self, topic: str) -> int:
        """Get count of pending messages"""
        return len(self._queues.get(topic, []))

    def get_processed_messages(self) -> List[Dict]:
        """Get processed messages (audit trail)"""
        return self._processed_messages.copy()
'''

    return queue


def generate_message_patterns() -> str:
    """Generate message queue patterns."""

    patterns = '''
class MessagePatterns:
    """
    Common message queue patterns.

    1. REQUEST-REPLY
       Producer sends request, waits for response
       Use: order creation (need order ID back)

    2. PUBLISH-SUBSCRIBE
       Producer publishes event, multiple consumers react
       Use: user created → send welcome email, create profile, etc.

    3. WORK QUEUE
       Multiple consumers, each message processed once
       Use: send 1M emails, distribute across workers
    """

    def __init__(self, queue: 'MessageQueue'):
        self.queue = queue

    def request_reply(self, topic: str, request: Dict, timeout_ms: int = 5000) -> Optional[Dict]:
        """Request-reply pattern: wait for response"""
        request_id = f"req-{datetime.utcnow().timestamp()}"

        request["request_id"] = request_id
        request["reply_to"] = f"reply-{request_id}"

        # Publish request
        self.queue.publish(topic, request)

        # Wait for reply (simplified, in production use real queue)
        start = datetime.utcnow()
        reply_topic = f"reply-{request_id}"

        while True:
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000
            if elapsed > timeout_ms:
                return None

            # Check if reply arrived
            if self.queue.get_pending_count(reply_topic) > 0:
                # In production: actually consume message
                return {"status": "success"}

    def publish_subscribe(self, topic: str, event: Dict) -> None:
        """Publish-subscribe: fire-and-forget, multiple subscribers"""
        self.queue.publish(topic, event)
        # All subscribers will be notified automatically

    def work_queue(self, topic: str, work_item: Dict) -> str:
        """Work queue: distribute work across workers"""
        message_id = self.queue.publish(topic, work_item)
        # Any available worker will pick it up
        return message_id
'''

    return patterns


def generate_message_system() -> dict:
    """Generate complete message queue system."""

    imports = '''from typing import Dict, List, Optional, Callable
from datetime import datetime
from collections import deque


'''

    module_doc = '''"""
Phase 5 Message Queue: Asynchronous Communication

Decouple services with event-driven architecture (RabbitMQ, Kafka, SQS).

SYNCHRONOUS (WITHOUT QUEUE):
OrderService → (waits) → PaymentService
OrderService → (waits) → ShippingService
OrderService → (waits) → NotificationService
- If any service slow/down: entire request fails
- Latency: OrderService waits for all 3

ASYNCHRONOUS (WITH QUEUE):
OrderService publishes "order.created" event
- PaymentService subscribes: processes payment
- ShippingService subscribes: creates shipment
- NotificationService subscribes: sends email
- OrderService continues immediately
- Services process independently

PATTERNS:

1. REQUEST-REPLY (sync-like)
   - OrderService: "Create order" → OrderService queue
   - Wait for reply
   - Get: {order_id, status}

2. PUBLISH-SUBSCRIBE (async, multiple)
   - OrderService: publishes "order.created"
   - PaymentService: subscribed, processes payment
   - ShippingService: subscribed, arranges shipment
   - NotificationService: subscribed, sends email
   - All happen in parallel

3. WORK QUEUE (async, distributed)
   - EmailService: 1M emails to send
   - Publish to "send-email" queue
   - 10 workers pick up messages in parallel
   - Each sends one email
   - Done 10x faster

BENEFITS:
✓ Loose coupling: services don't call each other
✓ Resilience: PaymentService down? Messages wait in queue
✓ Scalability: Add more workers to handle more load
✓ Reliability: Don't lose messages (persisted to disk/DB)
✓ Flexibility: New services can subscribe to events
"""
'''

    queue = generate_message_queue()
    patterns = generate_message_patterns()

    complete_code = imports + module_doc + "\n" + queue + "\n" + patterns

    return {
        "code": complete_code,
        "pattern": "Message Queue",
        "module": "phase5_message_queue.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate message queue")
    args = parser.parse_args()
    result = generate_message_system()
    print(result["code"])


if __name__ == "__main__":
    main()
