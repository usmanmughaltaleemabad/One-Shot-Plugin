#!/usr/bin/env python3
"""
Phase 5 Real-time: WebSocket Communication

Real-time bidirectional communication.

Problem: HTTP is request-response
- Client waits for server
- Not suitable for real-time (chat, notifications, live updates)
- Poll every second? Wasteful

Solution: WebSocket
- Persistent connection
- Both directions: client→server, server→client
- Low latency: messages arrive instantly
- Efficient: no polling, no overhead per message

Use cases:
- Chat: messages appear instantly
- Live updates: order status changes, notifications
- Collaboration: shared whiteboard, live editing
- Gaming: player positions, actions

Implementation:
- Establish connection (HTTP upgrade)
- Server maintains persistent connection
- Messages flow both directions
- Close connection when done

Usage:
    python phase5_realtime_websockets.py --feature chat

Input: Real-time feature
Output: WebSocket server and client with messaging
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


def generate_websocket_server() -> str:
    """Generate WebSocket server."""

    server = '''
class WebSocketServer:
    """
    WebSocket server for real-time communication.

    Responsibilities:
    - Accept WebSocket connections
    - Manage connection lifetime
    - Route messages
    - Broadcast to interested clients
    """

    def __init__(self):
        self._connections = {}  # client_id → connection
        self._subscriptions = {}  # topic → [client_ids]

    def accept_connection(self, client_id: str, connection: Any) -> None:
        """Accept new WebSocket connection"""
        self._connections[client_id] = connection

    def send_message(self, client_id: str, message: Dict) -> None:
        """Send message to specific client"""
        if client_id in self._connections:
            self._connections[client_id].send(json.dumps(message))

    def broadcast(self, topic: str, message: Dict) -> None:
        """Broadcast message to all subscribers"""
        if topic in self._subscriptions:
            for client_id in self._subscriptions[topic]:
                self.send_message(client_id, message)

    def subscribe(self, client_id: str, topic: str) -> None:
        """Subscribe client to topic"""
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
        self._subscriptions[topic].append(client_id)

    def unsubscribe(self, client_id: str, topic: str) -> None:
        """Unsubscribe client from topic"""
        if topic in self._subscriptions:
            self._subscriptions[topic] = [
                c for c in self._subscriptions[topic]
                if c != client_id
            ]

    def close_connection(self, client_id: str) -> None:
        """Close connection"""
        if client_id in self._connections:
            del self._connections[client_id]

            # Remove from all subscriptions
            for topic in self._subscriptions:
                self.unsubscribe(client_id, topic)

    def get_connected_count(self) -> int:
        """Get number of connected clients"""
        return len(self._connections)
'''

    return server


def generate_message_router() -> str:
    """Generate message routing."""

    router = '''
class MessageRouter:
    """Route incoming messages to handlers"""

    def __init__(self):
        self._handlers = {}  # message_type → handler_fn

    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register handler for message type"""
        self._handlers[message_type] = handler

    def route_message(
        self,
        client_id: str,
        message: Dict,
        server: WebSocketServer
    ) -> None:
        """Route message to appropriate handler"""
        message_type = message.get("type")

        if message_type not in self._handlers:
            # Unknown message type
            server.send_message(client_id, {
                "type": "error",
                "error": f"Unknown message type: {message_type}"
            })
            return

        handler = self._handlers[message_type]
        handler(client_id, message, server)
'''

    return router


def generate_chat_example() -> str:
    """Generate chat example."""

    example = '''
# Real-time Chat Example

class ChatMessage:
    """Chat message handler"""

    @staticmethod
    def handle_send_message(
        client_id: str,
        message: Dict,
        server: WebSocketServer
    ) -> None:
        """Handle user sending message"""
        chat_message = {
            "type": "message",
            "from": client_id,
            "text": message.get("text"),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Broadcast to all subscribers
        server.broadcast("chat-room", chat_message)


class PresenceHandler:
    """User presence (typing, online status)"""

    @staticmethod
    def handle_typing(
        client_id: str,
        message: Dict,
        server: WebSocketServer
    ) -> None:
        """Handle user typing"""
        server.broadcast("chat-room", {
            "type": "user-typing",
            "user": client_id
        })

    @staticmethod
    def handle_stopped_typing(
        client_id: str,
        message: Dict,
        server: WebSocketServer
    ) -> None:
        """Handle user stopped typing"""
        server.broadcast("chat-room", {
            "type": "user-stopped-typing",
            "user": client_id
        })


# Setup
server = WebSocketServer()
router = MessageRouter()

router.register_handler("send-message", ChatMessage.handle_send_message)
router.register_handler("typing", PresenceHandler.handle_typing)
router.register_handler("stopped-typing", PresenceHandler.handle_stopped_typing)

# Client connects
server.accept_connection("alice", websocket_connection)
server.subscribe("alice", "chat-room")

# Alice sends message
router.route_message("alice", {
    "type": "send-message",
    "text": "Hello Bob!"
}, server)

# Bob receives via broadcast
# Message: {"type": "message", "from": "alice", "text": "Hello Bob!", "timestamp": "..."}
'''

    return example


def generate_websocket_system() -> dict:
    """Generate complete WebSocket system."""

    imports = '''import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Real-time: WebSocket Communication

Bidirectional real-time communication.

HTTP (traditional):
- Client sends request
- Server responds
- Connection closes
- For updates: poll every N seconds (wasteful)

WebSocket:
- Client initiates upgrade (HTTP → WebSocket)
- Persistent bidirectional connection
- Server can push data anytime
- Low latency, efficient

Use cases:
1. Chat: messages appear instantly
2. Notifications: real-time alerts
3. Live updates: order status, stock prices
4. Collaboration: shared editing, whiteboard
5. Gaming: position updates, actions
6. Monitoring: real-time dashboards

Message flow:

Chat example:
1. Alice connects: ws://localhost:8000/chat
2. Bob connects: ws://localhost:8000/chat
3. Alice sends: {"type": "send-message", "text": "Hi Bob!"}
4. Server routes to ChatMessageHandler
5. Handler broadcasts to "chat-room" subscribers
6. Bob receives: {"type": "message", "from": "alice", "text": "Hi Bob!", "timestamp": "..."}

Advantages over HTTP polling:
- HTTP polling: 10 requests/second = 10 connections, latency up to 100ms
- WebSocket: 1 connection, latency < 10ms
- 10x less bandwidth, 10x lower latency

Scale considerations:
- Each connection uses memory (keep alive)
- Large deployments: use message queues for pubsub
- Load balance WebSocket servers (sticky sessions)
- Redis or RabbitMQ for cross-server broadcasting
"""
'''

    server = generate_websocket_server()
    router = generate_message_router()
    example = generate_chat_example()

    complete_code = imports + module_doc + "\n" + server + "\n" + router + "\n" + example

    return {
        "code": complete_code,
        "pattern": "Real-time WebSockets",
        "module": "phase5_realtime_websockets.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate WebSocket module")
    parser.add_argument("--feature", help="Real-time feature")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_websocket_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
