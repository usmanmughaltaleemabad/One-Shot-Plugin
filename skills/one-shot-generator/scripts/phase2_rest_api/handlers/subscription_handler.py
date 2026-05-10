"""
Subscription Handler - WebSocket subscriptions and real-time updates

Generates:
- WebSocket connection handling
- Subscription management
- Real-time data push
- Client broadcast
"""

from typing import Dict, Any


class SubscriptionHandler:
    """Generate subscription code"""

    def __init__(self, framework: str, resource_name: str):
        self.framework = framework
        self.resource_name = resource_name

    def generate_django_subscriptions(self) -> str:
        """Generate Django Channels subscriptions"""
        return f"""
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class {self.resource_name.capitalize()}Consumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.{self.resource_name}_id = self.scope['url_route']['kwargs'].get('{self.resource_name}_id')
        self.{self.resource_name}_group_name = f'{self.resource_name}_{{self.{self.resource_name}_id}}'

        await self.channel_layer.group_add(
            self.{self.resource_name}_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.{self.resource_name}_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data['type'] == 'subscribe':
            await self.channel_layer.group_send(
                self.{self.resource_name}_group_name,
                {{'type': '{self.resource_name}.update', 'data': data}}
            )

    async def {self.resource_name}_update(self, event):
        await self.send(text_data=json.dumps(event['data']))

def broadcast_{self.resource_name}_update(channel_layer, {self.resource_name}_id, data):
    '''Broadcast {self.resource_name} update to all subscribers'''
    import asyncio
    asyncio.run(channel_layer.group_send(
        f'{self.resource_name}_{{{{self.resource_name}_id}}}}',
        {{'type': '{self.resource_name}.update', 'data': data}}
    ))
"""

    def generate_fastapi_subscriptions(self) -> str:
        """Generate FastAPI WebSocket subscriptions"""
        return f"""
from fastapi import WebSocket, WebSocketDisconnect
import json

class {self.resource_name.capitalize()}SubscriptionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = {self.resource_name.capitalize()}SubscriptionManager()

@app.websocket('/ws/{self.resource_plural}/{{item_id}}')
async def websocket_endpoint(websocket: WebSocket, item_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Process subscription
            if message.get('action') == 'subscribe':
                await manager.broadcast({{
                    'type': '{self.resource_name}.update',
                    'item_id': item_id,
                    'data': message.get('data')
                }})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def broadcast_{self.resource_name}_update(item_id: int, data: dict):
    '''Broadcast update to all {self.resource_name} subscribers'''
    await manager.broadcast({{
        'type': '{self.resource_name}.update',
        'item_id': item_id,
        'data': data
    }})
"""


def generate_subscriptions(framework: str, resource_name: str, resource_plural: str) -> Dict[str, str]:
    """
    Generate subscription code.

    Args:
        framework: django or fastapi
        resource_name: e.g., "user"
        resource_plural: e.g., "users"

    Returns: dict of {filename: code_content}
    """
    generator = SubscriptionHandler(framework, resource_name)
    output = {}

    if framework == "django":
        output["subscriptions.py"] = generator.generate_django_subscriptions()
    elif framework == "fastapi":
        output["subscriptions.py"] = generator.generate_fastapi_subscriptions()

    return output
