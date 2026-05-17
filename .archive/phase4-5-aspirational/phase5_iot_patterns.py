#!/usr/bin/env python3
"""Phase 5 IoT Patterns: MQTT Broker, Device Registry, Telemetry"""

from typing import Dict, List, Optional
from datetime import datetime


def generate_iot_patterns() -> str:
    return '''
class MQTTBroker:
    """IoT message broker with device registry."""

    def __init__(self):
        self._devices = {}  # device_id → device
        self._subscriptions = {}  # topic → [device_ids]
        self._messages = []  # Message history

    def register_device(self, device_id: str, device_type: str) -> str:
        """Register IoT device"""
        self._devices[device_id] = {
            "id": device_id,
            "type": device_type,
            "status": "online",
            "registered_at": datetime.utcnow().isoformat()
        }
        return device_id

    def publish(self, topic: str, message: Dict, from_device: str) -> None:
        """Publish message to topic"""
        self._messages.append({
            "topic": topic,
            "message": message,
            "from": from_device,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Route to subscribers
        if topic in self._subscriptions:
            for device_id in self._subscriptions[topic]:
                pass  # Send to device

    def subscribe(self, device_id: str, topic: str) -> None:
        """Subscribe device to topic"""
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
        self._subscriptions[topic].append(device_id)

    def telemetry_collect(self, device_id: str, metrics: Dict) -> None:
        """Collect device telemetry"""
        if device_id in self._devices:
            self._devices[device_id]["last_telemetry"] = metrics
            self._devices[device_id]["last_seen"] = datetime.utcnow().isoformat()
'''
    return generate_iot_patterns()


if __name__ == "__main__":
    print(generate_iot_patterns())
