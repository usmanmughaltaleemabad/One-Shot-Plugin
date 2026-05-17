#!/usr/bin/env python3
"""
Phase 5 Event Streaming: Kafka-Like Broker & Consumer Groups

Event Streaming: Unbounded stream of immutable events.

Problem: Point-to-point messaging bottleneck
- Service A publishes: Service B, C, D must subscribe
- Add Service E: update Service A code
- Coupling: A depends on B,C,D,E existing

Event Streaming (solution):
- Event broker (Kafka): decouples publishers/subscribers
- Partitioning: distribute load
- Consumer groups: parallel processing
- Replayability: re-consume events
"""

from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict


def generate_event_streaming() -> str:
    """Generate event streaming system."""

    streaming = '''
class EventBroker:
    """
    Kafka-like event streaming broker.

    Concepts:
    - Topic: named event stream
    - Partition: shard of topic (parallel)
    - Consumer: reads events
    - Offset: position in stream
    """

    def __init__(self):
        self._topics = {}  # topic_name → {partitions: []}
        self._events = defaultdict(list)  # topic → list of events
        self._offsets = defaultdict(lambda: defaultdict(int))  # topic,consumer → offset
        self._consumer_groups = {}  # group_id → {consumers, assignments}

    def create_topic(self, name: str, num_partitions: int = 3) -> None:
        """Create topic with partitions"""
        self._topics[name] = {
            "name": name,
            "partitions": num_partitions,
            "created_at": datetime.utcnow().isoformat(),
            "messages_total": 0
        }

    def publish(self, topic: str, event: Dict, key: str = None) -> None:
        """Publish event to topic"""
        if topic not in self._topics:
            return

        message = {
            "id": f"{topic}-{len(self._events[topic])}",
            "topic": topic,
            "data": event,
            "key": key,
            "timestamp": datetime.utcnow().isoformat(),
            "partition": hash(key or str(event)) % self._topics[topic]["partitions"]
        }

        self._events[topic].append(message)
        self._topics[topic]["messages_total"] += 1

    def create_consumer_group(self, group_id: str, topic: str, num_consumers: int) -> None:
        """Create consumer group for topic"""
        self._consumer_groups[group_id] = {
            "id": group_id,
            "topic": topic,
            "consumers": [f"{group_id}-c{i}" for i in range(num_consumers)],
            "created_at": datetime.utcnow().isoformat()
        }

    def consume(
        self,
        topic: str,
        consumer_id: str,
        max_messages: int = 10
    ) -> List[Dict]:
        """Consume messages"""
        if topic not in self._events:
            return []

        offset = self._offsets[topic][consumer_id]
        messages = self._events[topic][offset:offset + max_messages]

        # Update offset
        self._offsets[topic][consumer_id] += len(messages)

        return messages

    def get_offset(self, topic: str, consumer_id: str) -> int:
        """Get current offset"""
        return self._offsets[topic][consumer_id]

    def reset_offset(self, topic: str, consumer_id: str, offset: int) -> None:
        """Reset offset (replay events)"""
        self._offsets[topic][consumer_id] = offset

    def get_topic_stats(self, topic: str) -> Dict:
        """Get topic statistics"""
        if topic not in self._topics:
            return None

        return {
            "name": topic,
            "partitions": self._topics[topic]["partitions"],
            "total_messages": self._topics[topic]["messages_total"],
            "consumers": len(self._offsets[topic])
        }

    def get_lag(self, topic: str, consumer_id: str) -> int:
        """Get consumer lag (how far behind)"""
        if topic not in self._events:
            return 0

        total_messages = len(self._events[topic])
        offset = self._offsets[topic][consumer_id]
        return total_messages - offset
'''

    return streaming


def generate_streaming_system() -> dict:
    """Generate complete event streaming system."""

    imports = '''from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict


'''

    module_doc = '''"""
Phase 5 Event Streaming: Kafka-Like Broker & Consumer Groups

Publish-subscribe at scale with topics and partitions (Apache Kafka pattern).

ARCHITECTURE:

Topics (event streams):
- orders: {user_id, product_id, amount} events
- payments: {user_id, amount, status} events
- shipments: {order_id, tracking_number} events

Producers (publishers):
- Order Service: publishes to orders topic
- Payment Service: publishes to payments topic

Consumers (subscribers):
- Notification Service: consumes orders, payments, shipments
- Analytics Service: consumes all events
- Fraud Detection: consumes payments

Broker (event store):
- Persists all events
- Indexes by offset
- Replicates for durability

EXAMPLE: Order Processing

Publisher: Order Service
- User places order
- Publish event: {orderId: 123, userId: 456, amount: $99}
- To topic: orders

Subscribers (consumers):
1. Payment Service
   - Consumes event
   - Charges credit card
   - Publishes: payment_completed {orderId: 123, status: success}

2. Inventory Service
   - Consumes event
   - Reserves items
   - Publishes: inventory_reserved {orderId: 123}

3. Shipment Service
   - Consumes: inventory_reserved
   - Creates shipment
   - Publishes: shipment_created {orderId: 123, tracking: xyz}

4. Notification Service
   - Consumes: payment_completed, shipment_created
   - Sends email: "Order confirmed", "Shipped!"

5. Analytics Service
   - Consumes: orders, payments, shipments
   - Aggregates: orders per hour, revenue per region
   - Runs batch analytics

All subscribers are decoupled:
- Order Service doesn't know who reads orders
- New subscriber? Just subscribe, no code change
- Scaling: add more consumers in same group

PARTITIONING:

Topic: orders (3 partitions)

Partition 0: orders with key hash % 3 == 0
- Event 1: {orderId: 123, key: user_456}
- Event 4: {orderId: 789, key: user_123}
- Event 7: {orderId: 456, key: user_789}

Partition 1: orders with key hash % 3 == 1
- Event 2: {orderId: 234, key: user_567}
- Event 5: {orderId: 901, key: user_234}

Partition 2: orders with key hash % 3 == 2
- Event 3: {orderId: 567, key: user_890}
- Event 6: {orderId: 012, key: user_567}

Benefits:
- Parallel: consumer can read all 3 partitions simultaneously
- Ordering: events with same key go to same partition (ordered)
- Scaling: add partitions for more throughput

CONSUMER GROUPS:

Topic: orders (3 partitions)

Consumer Group A (3 consumers):
- Consumer A1: reads partition 0
- Consumer A2: reads partition 1
- Consumer A3: reads partition 2
- Parallelism: 3x throughput

Consumer Group B (1 consumer):
- Consumer B1: reads all partitions (0,1,2)
- Parallelism: same as serial
- But different group, independent offset

Same events, multiple consumers:
- Group A: first reader (e.g. shipment service)
- Group B: second reader (e.g. analytics)
- Each consumer group: independent offset
- Replay: reset offset, re-read from start

OFFSET (position tracking):

Consumer offset: position in stream
- Offset 0: start of stream
- Offset 100: read events 0-99
- Offset 500: read events 0-499
- Committed: persist offset after processing

Scenario: Consumer crashes
- Consumer was at offset 500
- Crashes while processing event 501
- Restart: resume from offset 500
- Re-read: events 500-501 (might reprocess)
- Idempotency: consumer should handle duplicates

Scenario: Replay
- Consumer wants to reprocess all events
- Reset offset to 0
- Re-read: all events from beginning
- Use: bug fix, data correction, testing

LAG (behind by how much):

Total events in topic: 1000
Consumer offset: 800
Consumer lag: 200

Lag = 0: consumer caught up (real-time)
Lag > 0: consumer behind (processing slower than publish)

Alert if lag > 1000: consumer struggling

HIGH THROUGHPUT PATTERN:

Topic: raw_events (100 partitions)
- 1M events/sec published

Consumer Group 1: streaming processors (Kafka Streams)
- 100 consumers (one per partition)
- Read, enrich, write to another topic
- Throughput: 1M events/sec

Consumer Group 2: batch analytics (Spark)
- 1 consumer (batches events)
- Batch size: 10k events
- Frequency: every minute
- Throughput: aggregated results

Same source, different consumers, different speeds

ORDERING GUARANTEES:

Key-based partitioning ensures ordering:
- Events with key=user_123 always go to partition 1
- Partition 1 is read serially
- Events processed in order
- Result: user_123's orders processed in order

Cross-partition:
- Events from different keys: no ordering guarantee
- Event A (key=user_123) and Event B (key=user_456)
- Might process out of order
- Usually OK (different users don't interfere)

BENEFITS:

✓ Decoupled: publishers don't know subscribers
✓ Scalable: partition by key/throughput
✓ Durable: events persisted
✓ Replayable: re-consume any event
✓ Ordered: by key (within partition)
✓ Parallel: multiple consumers per group
"""
'''

    streaming = generate_event_streaming()

    complete_code = imports + module_doc + "\n" + streaming

    return {
        "code": complete_code,
        "pattern": "Event Streaming",
        "module": "phase5_event_streaming.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate event streaming")
    args = parser.parse_args()
    result = generate_streaming_system()
    print(result["code"])


if __name__ == "__main__":
    main()
