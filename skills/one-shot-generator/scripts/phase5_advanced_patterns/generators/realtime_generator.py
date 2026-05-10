"""
Phase 5.2: Real-Time Features Generator

Generates real-time communication infrastructure:
- WebSocket servers and clients
- Server-Sent Events (SSE)
- Pub/Sub patterns (Redis, Kafka)
- Real-time data synchronization
- Presence tracking and user sessions
"""

from typing import Dict


def generate_websocket_python() -> Dict[str, str]:
    """Generate Python WebSocket infrastructure"""
    return {
        "websocket_server.py": '''"""WebSocket real-time server"""
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import Set, Dict, List
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

class WebSocketManager:
    """Manage WebSocket connections and broadcasting"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.user_rooms: Dict[str, Set[WebSocket]] = {}
        self.presence: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, user_id: str = None):
        """Accept connection and track user"""
        await websocket.accept()
        self.active_connections.add(websocket)

        if user_id:
            if user_id not in self.user_rooms:
                self.user_rooms[user_id] = set()
            self.user_rooms[user_id].add(websocket)

            # Track presence
            self.presence[user_id] = {
                "user_id": user_id,
                "connected_at": asyncio.get_event_loop().time()
            }

            # Broadcast presence update
            await self.broadcast({
                "type": "presence",
                "action": "join",
                "user_id": user_id,
                "presence": list(self.presence.keys())
            })

        logger.info(f"Client {user_id or 'anonymous'} connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, user_id: str = None):
        """Remove connection and update presence"""
        self.active_connections.discard(websocket)

        if user_id:
            if user_id in self.user_rooms:
                self.user_rooms[user_id].discard(websocket)
                if not self.user_rooms[user_id]:
                    del self.user_rooms[user_id]
                    del self.presence[user_id]

        logger.info(f"Client {user_id or 'anonymous'} disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return

        # Send to all connections
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected
        self.active_connections -= disconnected

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user"""
        if user_id not in self.user_rooms:
            return

        disconnected = set()
        for connection in self.user_rooms[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                disconnected.add(connection)

        self.user_rooms[user_id] -= disconnected

    async def send_to_room(self, room_id: str, message: dict):
        """Send message to room (group of users)"""
        # Implementation depends on room management
        await self.broadcast(message)

    def get_presence(self) -> List[Dict]:
        """Get current presence info"""
        return list(self.presence.values())

manager = WebSocketManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: str = None):
    """Main WebSocket endpoint"""
    await manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
                continue

            # Route message types
            if message.get("type") == "broadcast":
                await manager.broadcast({
                    "type": "message",
                    "user_id": user_id,
                    "content": message.get("content"),
                    "timestamp": asyncio.get_event_loop().time()
                })

            elif message.get("type") == "direct":
                await manager.send_to_user(message.get("to_user_id"), {
                    "type": "direct_message",
                    "from_user_id": user_id,
                    "content": message.get("content"),
                    "timestamp": asyncio.get_event_loop().time()
                })

            elif message.get("type") == "presence_request":
                await websocket.send_json({
                    "type": "presence",
                    "users": manager.get_presence()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

@app.get("/")
async def get():
    """HTML client for testing WebSocket"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
    </head>
    <body>
        <h1>WebSocket Real-Time Chat</h1>
        <input id="userId" type="text" placeholder="User ID">
        <input id="messageInput" type="text" placeholder="Message">
        <button onclick="sendMessage()">Send</button>
        <ul id="messages"></ul>

        <script>
            let ws;

            function connect() {
                const userId = document.getElementById('userId').value;
                ws = new WebSocket(`ws://localhost:8000/ws?user_id=${userId}`);

                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    const li = document.createElement('li');
                    li.innerText = `${data.user_id || 'System'}: ${JSON.stringify(data)}`;
                    document.getElementById('messages').appendChild(li);
                };

                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            }

            function sendMessage() {
                const input = document.getElementById('messageInput');
                ws.send(JSON.stringify({
                    "type": "broadcast",
                    "content": input.value
                }));
                input.value = '';
            }

            window.onload = connect;
        </script>
    </body>
    </html>
    """)
''',
        "websocket_client.py": '''"""WebSocket client for real-time communication"""
import asyncio
import json
import websockets
from typing import Callable, Dict, Any

class WebSocketClient:
    """WebSocket client for real-time communication"""

    def __init__(self, url: str, user_id: str = None):
        self.url = url
        self.user_id = user_id
        self.websocket = None
        self.handlers: Dict[str, Callable] = {}

    async def connect(self):
        """Connect to WebSocket server"""
        uri = f"{self.url}?user_id={self.user_id}" if self.user_id else self.url
        self.websocket = await websockets.connect(uri)
        print(f"Connected to {uri}")

    async def disconnect(self):
        """Disconnect from server"""
        if self.websocket:
            await self.websocket.close()

    async def send(self, message: Dict[str, Any]):
        """Send message to server"""
        if self.websocket:
            await self.websocket.send(json.dumps(message))

    async def receive(self):
        """Receive message from server"""
        if self.websocket:
            return await self.websocket.recv()

    async def listen(self):
        """Listen for incoming messages"""
        try:
            while True:
                message = await self.receive()
                data = json.loads(message)

                # Call registered handler
                msg_type = data.get("type")
                if msg_type in self.handlers:
                    await self.handlers[msg_type](data)
                else:
                    print(f"Received: {data}")

        except Exception as e:
            print(f"Error: {e}")

        finally:
            await self.disconnect()

    def on(self, message_type: str, handler: Callable):
        """Register message handler"""
        self.handlers[message_type] = handler

# Example usage
async def main():
    client = WebSocketClient("ws://localhost:8000/ws", user_id="user1")

    @client.on("message")
    async def handle_message(data):
        print(f"Message: {data}")

    await client.connect()
    await client.listen()

if __name__ == "__main__":
    asyncio.run(main())
''',
    }


def generate_sse_python() -> Dict[str, str]:
    """Generate Server-Sent Events (SSE) infrastructure"""
    return {
        "sse_server.py": '''"""Server-Sent Events (SSE) for real-time data streaming"""
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
import asyncio
import json
from typing import AsyncGenerator, Set
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

class SSEManager:
    """Manage Server-Sent Events connections"""

    def __init__(self):
        self.subscribers: Set[asyncio.Queue] = set()

    async def subscribe(self) -> AsyncGenerator[str, None]:
        """Subscribe to SSE stream"""
        queue: asyncio.Queue = asyncio.Queue()
        self.subscribers.add(queue)

        try:
            while True:
                message = await queue.get()
                yield f"data: {json.dumps(message)}\\n\\n"

        except asyncio.CancelledError:
            self.subscribers.discard(queue)
            logger.info(f"SSE subscriber disconnected. Total: {len(self.subscribers)}")

    async def publish(self, message: dict):
        """Publish message to all subscribers"""
        tasks = []
        for queue in self.subscribers:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                logger.warning("SSE queue full, dropping message")

        logger.info(f"Published to {len(self.subscribers)} subscribers")

manager = SSEManager()

@app.get("/subscribe")
async def subscribe():
    """Subscribe to SSE stream"""
    return StreamingResponse(
        manager.subscribe(),
        media_type="text/event-stream"
    )

@app.post("/publish")
async def publish(message: dict):
    """Publish message to all subscribers"""
    await manager.publish(message)
    return {"status": "published"}

# Example: Publish events periodically
@app.on_event("startup")
async def startup_event():
    """Start background task to publish events"""
    async def publish_updates():
        counter = 0
        while True:
            await manager.publish({
                "type": "update",
                "counter": counter,
                "message": f"Update {counter}"
            })
            counter += 1
            await asyncio.sleep(5)

    asyncio.create_task(publish_updates())
''',
        "sse_client.py": '''"""Server-Sent Events client"""

class SSEClient:
    """SSE client for real-time data updates"""

    def __init__(self, url: str):
        self.url = url

    def subscribe(self, callback):
        """Subscribe to SSE stream"""
        import requests

        response = requests.get(self.url, stream=True)

        for line in response.iter_lines():
            if line:
                if line.startswith(b"data: "):
                    data = line[6:].decode()
                    import json
                    message = json.loads(data)
                    callback(message)

# Example usage
if __name__ == "__main__":
    client = SSEClient("http://localhost:8000/subscribe")

    def handle_message(data):
        print(f"Received: {data}")

    client.subscribe(handle_message)
''',
    }


def generate_pubsub_python() -> Dict[str, str]:
    """Generate Pub/Sub infrastructure (Redis)"""
    return {
        "pubsub_redis.py": '''"""Redis Pub/Sub for real-time messaging"""
import redis
import json
import asyncio
from typing import Callable, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RedisPubSub:
    """Redis Pub/Sub wrapper for real-time messaging"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis = redis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()
        self.handlers: Dict[str, Callable] = {}

    def subscribe(self, channel: str, handler: Callable = None):
        """Subscribe to channel"""
        self.pubsub.subscribe(channel)
        if handler:
            self.handlers[channel] = handler
        logger.info(f"Subscribed to channel: {channel}")

    def publish(self, channel: str, message: Dict[str, Any]):
        """Publish message to channel"""
        self.redis.publish(channel, json.dumps(message))
        logger.info(f"Published to {channel}: {message}")

    async def listen(self):
        """Listen for messages on subscribed channels"""
        try:
            for message in self.pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"].decode()
                    data = json.loads(message["data"].decode())

                    # Call registered handler
                    if channel in self.handlers:
                        await self.handlers[channel](data)
                    else:
                        logger.info(f"Message on {channel}: {data}")

        except Exception as e:
            logger.error(f"PubSub error: {e}")

    def close(self):
        """Close connection"""
        self.pubsub.close()

# Example usage
async def main():
    pubsub = RedisPubSub()

    async def handle_notification(data):
        print(f"Notification: {data}")

    pubsub.subscribe("notifications", handle_notification)

    # Publish example
    pubsub.publish("notifications", {"type": "alert", "message": "System update"})

    await pubsub.listen()

if __name__ == "__main__":
    asyncio.run(main())
''',
    }


def generate_websocket_nodejs() -> Dict[str, str]:
    """Generate Node.js WebSocket infrastructure"""
    return {
        "websocket-server.js": '''// WebSocket real-time server
const WebSocket = require('ws');
const http = require('http');
const express = require('express');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

class WebSocketManager {
    constructor() {
        this.connections = new Map();
        this.userRooms = new Map();
        this.presence = new Map();
    }

    addConnection(ws, userId) {
        this.connections.set(ws, { userId, connectedAt: Date.now() });

        if (userId) {
            if (!this.userRooms.has(userId)) {
                this.userRooms.set(userId, new Set());
            }
            this.userRooms.get(userId).add(ws);

            this.presence.set(userId, {
                userId,
                connectedAt: Date.now()
            });

            this.broadcast({
                type: 'presence',
                action: 'join',
                users: Array.from(this.presence.keys())
            });
        }

        console.log(`Client ${userId || 'anonymous'} connected. Total: ${this.connections.size}`);
    }

    removeConnection(ws, userId) {
        this.connections.delete(ws);

        if (userId) {
            const rooms = this.userRooms.get(userId);
            if (rooms) {
                rooms.delete(ws);
                if (rooms.size === 0) {
                    this.userRooms.delete(userId);
                    this.presence.delete(userId);
                }
            }
        }

        console.log(`Client ${userId || 'anonymous'} disconnected. Total: ${this.connections.size}`);
    }

    broadcast(message) {
        this.connections.forEach(({ userId }, ws) => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify(message));
            }
        });
    }

    sendToUser(userId, message) {
        const rooms = this.userRooms.get(userId);
        if (rooms) {
            rooms.forEach(ws => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify(message));
                }
            });
        }
    }

    getPresence() {
        return Array.from(this.presence.values());
    }
}

const manager = new WebSocketManager();

wss.on('connection', (ws) => {
    const url = new URL(ws.url, `http://${ws._socket.remoteAddress}`);
    const userId = url.searchParams.get('userId');

    manager.addConnection(ws, userId);

    ws.on('message', (data) => {
        try {
            const message = JSON.parse(data);

            if (message.type === 'broadcast') {
                manager.broadcast({
                    type: 'message',
                    userId,
                    content: message.content,
                    timestamp: Date.now()
                });
            } else if (message.type === 'direct') {
                manager.sendToUser(message.toUserId, {
                    type: 'direct_message',
                    fromUserId: userId,
                    content: message.content,
                    timestamp: Date.now()
                });
            } else if (message.type === 'presence_request') {
                ws.send(JSON.stringify({
                    type: 'presence',
                    users: manager.getPresence()
                }));
            }
        } catch (e) {
            ws.send(JSON.stringify({ error: 'Invalid JSON' }));
        }
    });

    ws.on('close', () => {
        manager.removeConnection(ws, userId);
    });
});

server.listen(8000, () => {
    console.log('WebSocket server listening on port 8000');
});
''',
        "websocket-client.js": '''// WebSocket client
class WebSocketClient {
    constructor(url, userId) {
        this.url = url;
        this.userId = userId;
        this.ws = null;
        this.handlers = {};
    }

    connect() {
        return new Promise((resolve, reject) => {
            const uri = this.userId
                ? `${this.url}?userId=${this.userId}`
                : this.url;

            this.ws = new WebSocket(uri);

            this.ws.onopen = () => {
                console.log('Connected to WebSocket server');
                resolve();
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                const type = data.type;

                if (this.handlers[type]) {
                    this.handlers[type](data);
                } else {
                    console.log('Received:', data);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };
        });
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    on(type, handler) {
        this.handlers[type] = handler;
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Example usage
const client = new WebSocketClient('ws://localhost:8000', 'user1');

client.on('message', (data) => {
    console.log('Message:', data);
});

client.on('presence', (data) => {
    console.log('Online users:', data.users);
});

(async () => {
    await client.connect();
    client.send({ type: 'presence_request' });
})();
''',
    }


def generate_realtime(framework: str, language: str, app_name: str = None) -> Dict[str, str]:
    """Generate complete real-time features infrastructure"""
    app_name = app_name or "realtime-app"
    output = {}

    if language == "python":
        # WebSocket infrastructure
        output.update(generate_websocket_python())

        # SSE infrastructure
        output.update(generate_sse_python())

        # Pub/Sub infrastructure
        output.update(generate_pubsub_python())

        # Requirements
        output["requirements-realtime.txt"] = '''fastapi>=0.104.0
uvicorn>=0.24.0
websockets>=12.0
redis>=5.0.0
aioredis>=2.0.0
python-socketio>=5.0.0
'''

        # Integrated example
        output["realtime_integration.py"] = '''"""Integrated real-time features"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import asyncio
from websocket_server import manager as ws_manager, app as ws_app
from sse_server import manager as sse_manager, app as sse_app
from pubsub_redis import RedisPubSub

app = FastAPI()

# Mount real-time handlers
app.include_router(ws_app.router)
app.include_router(sse_app.router)

# Initialize Redis Pub/Sub
pubsub = RedisPubSub()

@app.on_event("startup")
async def startup():
    """Start real-time services"""
    asyncio.create_task(pubsub.listen())

@app.get("/dashboard")
async def dashboard():
    """Real-time dashboard"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Real-Time Dashboard</h1>
        <div id="status">Connecting...</div>
        <div id="messages"></div>
        <script>
            const ws = new WebSocket('ws://localhost:8000/ws');
            const sse = new EventSource('/subscribe');

            ws.onopen = () => {
                document.getElementById('status').innerText = 'Connected';
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('WebSocket:', data);
            };

            sse.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('SSE:', data);
            };
        </script>
    </body>
    </html>
    """)
'''

    else:  # JavaScript/Node.js
        output.update(generate_websocket_nodejs())

        output["package-realtime.json"] = '''{
  "name": "realtime-features",
  "version": "1.0.0",
  "dependencies": {
    "ws": "^8.14.0",
    "express": "^4.18.0",
    "redis": "^4.6.0",
    "socket.io": "^4.7.0"
  }
}
'''

        output["sse-server.js"] = '''// Server-Sent Events server
const express = require('express');
const app = express();

const subscribers = new Set();

app.get('/subscribe', (req, res) => {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    subscribers.add(res);

    res.write('data: {"type":"connected"}\\n\\n');

    req.on('close', () => {
        subscribers.delete(res);
    });
});

function publish(message) {
    subscribers.forEach(res => {
        res.write(`data: ${JSON.stringify(message)}\\n\\n`);
    });
}

app.post('/publish', (req, res) => {
    const message = req.body;
    publish(message);
    res.json({ status: 'published' });
});

module.exports = { app, publish };
'''

    # Docker setup
    output["docker-compose-realtime.yaml"] = '''version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
'''

    return output
