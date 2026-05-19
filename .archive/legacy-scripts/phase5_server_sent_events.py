#!/usr/bin/env python3
"""
Phase 5 Real-time: Server-Sent Events (SSE)

Real-time server → browser updates without polling.

Problem: Polling = wastes bandwidth
- Browser: "Do you have updates?" (every 1 second)
- Server: "No" (repeated 1000 times/hour)
- Bandwidth wasted on "No" responses

Server-Sent Events (solution):
- Browser: opens connection to server
- Server: keeps connection open
- When server has update: sends to browser
- Browser receives immediately (real-time)
- No polling = less bandwidth

Use cases:
- Stock prices (real-time updates)
- Chat messages (instant notification)
- Notifications (1000+ users, one server connection each)
- Live sports scores
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime


def generate_sse_server() -> str:
    """Generate SSE server."""

    server = '''
class SSEServer:
    """
    Server-Sent Events: Push updates to browser.

    Connection flow:
    1. Browser: new EventSource("http://api.example.com/events")
    2. Server: accepts connection, keeps it open
    3. Server: has update, sends data
    4. Browser: onmessage fires, processes data
    5. Repeat step 3-4
    6. Eventually: connection closes
    """

    def __init__(self):
        self._clients = []  # Connected clients
        self._event_log = []

    def add_client(self, client_id: str, channel: str) -> None:
        """Register SSE client"""
        self._clients.append({
            "id": client_id,
            "channel": channel,
            "connected_at": datetime.utcnow().isoformat(),
            "messages_sent": 0
        })

    def remove_client(self, client_id: str) -> None:
        """Client disconnected"""
        self._clients = [c for c in self._clients if c["id"] != client_id]

    def broadcast(self, channel: str, event: Dict) -> int:
        """Send event to all clients on channel"""
        sent_count = 0

        for client in self._clients:
            if client["channel"] == channel:
                # Send to client (simplified)
                self._send_to_client(client["id"], event)
                client["messages_sent"] += 1
                sent_count += 1

        self._event_log.append({
            "event": event,
            "channel": channel,
            "recipients": sent_count,
            "timestamp": datetime.utcnow().isoformat()
        })

        return sent_count

    def _send_to_client(self, client_id: str, event: Dict) -> None:
        """Send event to specific client"""
        # In production: actually write to HTTP response stream
        # Format: "data: {json}\n\n"
        pass

    def get_connected_clients(self, channel: str = None) -> int:
        """Get count of connected clients"""
        if channel:
            return len([c for c in self._clients if c["channel"] == channel])
        return len(self._clients)

    def get_event_log(self) -> List[Dict]:
        """Get event history"""
        return self._event_log.copy()
'''

    return server


def generate_sse_examples() -> str:
    """Generate SSE usage examples."""

    examples = '''
class SSEExamples:
    """
    Real-world SSE examples.

    Example 1: Stock Price Updates
    - Browser subscribes to "STOCK_AAPL" channel
    - When price changes: server sends update
    - Browser updates price display

    Example 2: Chat Notifications
    - Browser subscribes to "CHAT_USER_123" channel
    - When new message arrives: server sends notification
    - Browser shows in UI without page reload

    Example 3: Live Dashboard
    - Browser subscribes to "DASHBOARD_METRICS" channel
    - Every second: server sends latest metrics
    - Chart updates in real-time
    """

    def __init__(self, sse_server: 'SSEServer'):
        self.sse = sse_server

    def stream_stock_prices(self, symbol: str, prices: List[float]) -> None:
        """Stream stock price updates"""
        for price in prices:
            event = {
                "type": "price",
                "symbol": symbol,
                "price": price,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.sse.broadcast(f"STOCK_{symbol}", event)

    def notify_new_message(self, user_id: str, message: Dict) -> None:
        """Notify user of new message"""
        event = {
            "type": "message",
            "data": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.sse.broadcast(f"CHAT_USER_{user_id}", event)

    def stream_metrics(self, metrics: Dict) -> None:
        """Stream dashboard metrics"""
        event = {
            "type": "metrics",
            "cpu": metrics.get("cpu"),
            "memory": metrics.get("memory"),
            "requests_per_sec": metrics.get("rps"),
            "timestamp": datetime.utcnow().isoformat()
        }
        self.sse.broadcast("DASHBOARD_METRICS", event)
'''

    return examples


def generate_sse_system() -> dict:
    """Generate complete SSE system."""

    imports = '''from typing import Dict, List, Optional, Callable
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Server-Sent Events: Real-time Server-to-Browser Push

One-way push from server to browser (WebSocket alternative for simple cases).

FLOW:
1. Browser creates EventSource
   const evtSource = new EventSource("/api/events")

2. Browser listens for events
   evtSource.addEventListener("price-update", (event) => {
     console.log(event.data)  // {price: 150.50}
   })

3. Server sends event
   send HTTP with Content-Type: text/event-stream
   data: {"price": 150.50}\\n\\n

4. Browser receives, onmessage fires, updates UI

5. Connection stays open until
   - Browser closes tab
   - Server sends reconnect: <milliseconds>
   - Network disconnected

SSE vs WebSocket:

SSE:
- One-way (server → browser)
- Simple HTTP (works everywhere)
- Auto-reconnect (built-in)
- Lightweight
- Use: notifications, live updates, dashboards

WebSocket:
- Two-way (both directions)
- TCP-like connection
- Full-duplex (simultaneous)
- More complex
- Use: chat, multiplayer games, real-time collaboration

BROWSER CODE:
const evtSource = new EventSource("/api/events");

evtSource.addEventListener("open", () => {
  console.log("Connected");
});

evtSource.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  console.log("Update:", data);
});

evtSource.addEventListener("error", () => {
  console.log("Disconnected, will auto-retry");
});

SERVER CODE:
response.headers = {"Content-Type": "text/event-stream"}
response.write("data: {json}\\n\\n")
response.flush()
# Keep connection open
# Send more data when available
"""
'''

    server = generate_sse_server()
    examples = generate_sse_examples()

    complete_code = imports + module_doc + "\n" + server + "\n" + examples

    return {
        "code": complete_code,
        "pattern": "Server-Sent Events",
        "module": "phase5_server_sent_events.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate SSE system")
    args = parser.parse_args()
    result = generate_sse_system()
    print(result["code"])


if __name__ == "__main__":
    main()
