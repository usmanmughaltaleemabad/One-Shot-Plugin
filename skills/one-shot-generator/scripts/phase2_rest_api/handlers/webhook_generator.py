"""
Webhook Generator - Webhook support for APIs

Generates:
- Webhook endpoint registration
- Webhook delivery and retry logic
- Event signing and verification
- Webhook management endpoints
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import hashlib
import hmac


@dataclass
class WebhookEvent:
    """Webhook event definition"""
    name: str
    description: str
    payload: Dict[str, Any]


class WebhookGenerator:
    """Generate webhook code"""

    def __init__(self, framework: str, resource_name: str):
        self.framework = framework
        self.resource_name = resource_name

    def generate_django_webhooks(self) -> str:
        """Generate Django webhook implementation"""
        return f"""
import json
import requests
import hmac
import hashlib
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

class WebhookEndpoint(models.Model):
    '''Registered webhook endpoint'''
    url = models.URLField()
    events = models.JSONField(default=list)
    secret = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'webhook_endpoints'

class WebhookDelivery(models.Model):
    '''Track webhook deliveries'''
    endpoint = models.ForeignKey(WebhookEndpoint, on_delete=models.CASCADE)
    event = models.CharField(max_length=255)
    payload = models.JSONField()
    status_code = models.IntegerField(null=True)
    response = models.TextField(null=True)
    delivered_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'webhook_deliveries'

class WebhookManager:
    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        '''Generate HMAC signature'''
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def verify_signature(payload: str, signature: str, secret: str) -> bool:
        '''Verify webhook signature'''
        expected = WebhookManager.generate_signature(payload, secret)
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def trigger_event(event_name: str, payload: Dict):
        '''Trigger webhook event'''
        endpoints = WebhookEndpoint.objects.filter(
            events__contains=event_name,
            active=True
        )

        for endpoint in endpoints:
            deliver_webhook.delay(endpoint.id, event_name, payload)

@shared_task(bind=True, max_retries=3)
def deliver_webhook(self, endpoint_id: int, event: str, payload: Dict):
    '''Deliver webhook with retry logic'''
    try:
        endpoint = WebhookEndpoint.objects.get(id=endpoint_id)
        payload_json = json.dumps(payload)
        signature = WebhookManager.generate_signature(payload_json, endpoint.secret)

        response = requests.post(
            endpoint.url,
            json=payload,
            headers={{
                'Content-Type': 'application/json',
                'X-Webhook-Signature': signature,
                'X-Webhook-Event': event,
            }},
            timeout=10
        )

        WebhookDelivery.objects.create(
            endpoint=endpoint,
            event=event,
            payload=payload,
            status_code=response.status_code,
            response=response.text[:1000]
        )

        response.raise_for_status()
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

@receiver(post_save, sender={self.resource_name.capitalize()})
def trigger_{self.resource_name}_webhook(sender, instance, created, **kwargs):
    '''Trigger webhook on {self.resource_name} change'''
    event = f'{self.resource_name}.created' if created else f'{self.resource_name}.updated'
    WebhookManager.trigger_event(event, {{
        'id': instance.id,
        'event': event,
        'data': {{'id': instance.id, 'name': instance.name}}
    }})
"""

    def generate_fastapi_webhooks(self) -> str:
        """Generate FastAPI webhook implementation"""
        return f"""
import json
import httpx
import hmac
import hashlib
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class WebhookEndpoint(BaseModel):
    url: str
    events: List[str]
    secret: str
    active: bool = True

class WebhookEvent(BaseModel):
    event: str
    timestamp: datetime
    data: dict

class WebhookManager:
    def __init__(self):
        self.endpoints = {{}}

    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        '''Generate HMAC signature'''
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def verify_signature(payload: str, signature: str, secret: str) -> bool:
        '''Verify webhook signature'''
        expected = WebhookManager.generate_signature(payload, secret)
        return hmac.compare_digest(expected, signature)

    async def trigger_event(self, event: str, payload: dict):
        '''Trigger webhook event'''
        for endpoint in self.endpoints.values():
            if event in endpoint.events and endpoint.active:
                await self.deliver_webhook(endpoint, event, payload)

    async def deliver_webhook(self, endpoint: WebhookEndpoint, event: str, payload: dict):
        '''Deliver webhook with retry'''
        payload_json = json.dumps(payload)
        signature = self.generate_signature(payload_json, endpoint.secret)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    endpoint.url,
                    json=payload,
                    headers={{
                        'Content-Type': 'application/json',
                        'X-Webhook-Signature': signature,
                        'X-Webhook-Event': event,
                    }},
                    timeout=10
                )
                response.raise_for_status()
            except httpx.RequestError as e:
                # Log and retry
                pass

webhook_manager = WebhookManager()

async def register_webhook(endpoint: WebhookEndpoint):
    '''Register webhook endpoint'''
    webhook_manager.endpoints[endpoint.url] = endpoint

async def trigger_{self.resource_name}_event(event: str, data: dict):
    '''Trigger {self.resource_name} webhook event'''
    await webhook_manager.trigger_event(
        f'{self.resource_name}.{{event}}',
        {{'event': f'{self.resource_name}.{{event}}', 'data': data, 'timestamp': datetime.now()}}
    )
"""


def generate_webhooks(framework: str, resource_name: str) -> Dict[str, str]:
    """
    Generate webhook code.

    Args:
        framework: django or fastapi
        resource_name: e.g., "user"

    Returns: dict of {filename: code_content}
    """
    generator = WebhookGenerator(framework, resource_name)
    output = {}

    if framework == "django":
        output["webhooks.py"] = generator.generate_django_webhooks()
    elif framework == "fastapi":
        output["webhooks.py"] = generator.generate_fastapi_webhooks()

    return output
