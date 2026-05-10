"""
Webhook Handler - Job event webhooks and callbacks

Generates:
- Webhook registration endpoints
- Job event callbacks
- Webhook delivery with retry
- Webhook signature verification
- Event payload formatting
"""

from typing import Dict, Any


class WebhookHandler:
    """Generate webhook handling code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_django_webhooks(self) -> str:
        """Generate Django webhook handlers"""
        return """
from django.db import models
from django.http import JsonResponse
from rest_framework.decorators import api_view
import json
import hashlib
import hmac
import requests
import logging

logger = logging.getLogger(__name__)

class JobWebhook(models.Model):
    '''Store registered webhooks for job events'''
    url = models.URLField()
    events = models.JSONField(default=list)  # job.submitted, job.completed, job.failed
    secret = models.CharField(max_length=256)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'job_webhooks'

class WebhookManager:
    def __init__(self):
        self.max_retries = 3
        self.timeout = 5

    def register_webhook(self, url: str, events: list, secret: str):
        '''Register a webhook'''
        webhook = JobWebhook.objects.create(
            url=url,
            events=events,
            secret=secret
        )
        logger.info(f'Webhook registered: {webhook.id}')
        return webhook

    def trigger_webhook(self, job_id: str, event: str, data: dict):
        '''Trigger webhook for job event'''
        webhooks = JobWebhook.objects.filter(
            events__contains=event,
            active=True
        )

        for webhook in webhooks:
            self._deliver_webhook(webhook, job_id, event, data)

    def _deliver_webhook(self, webhook: JobWebhook, job_id: str, event: str, data: dict):
        '''Deliver webhook with retry logic'''
        payload = {
            'job_id': job_id,
            'event': event,
            'data': data,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }

        headers = self._generate_headers(webhook, payload)

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    logger.info(f'Webhook delivered: {webhook.id}')
                    return
            except Exception as e:
                logger.warning(f'Webhook delivery attempt {attempt + 1} failed: {e}')

        logger.error(f'Webhook delivery failed after {self.max_retries} attempts: {webhook.id}')

    def _generate_headers(self, webhook: JobWebhook, payload: dict) -> dict:
        '''Generate webhook signature headers'''
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            webhook.secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        return {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature,
            'X-Webhook-Timestamp': __import__('time').time()
        }

@api_view(['POST'])
def register_webhook(request):
    '''Register a new webhook'''
    url = request.data.get('url')
    events = request.data.get('events', [])
    secret = request.data.get('secret')

    if not all([url, events, secret]):
        return JsonResponse({'error': 'url, events, secret required'}, status=400)

    manager = WebhookManager()
    webhook = manager.register_webhook(url, events, secret)

    return JsonResponse({
        'webhook_id': webhook.id,
        'url': webhook.url,
        'events': webhook.events
    }, status=201)

@api_view(['GET'])
def list_webhooks(request):
    '''List registered webhooks'''
    webhooks = JobWebhook.objects.all()
    return JsonResponse({
        'webhooks': [{
            'id': w.id,
            'url': w.url,
            'events': w.events,
            'active': w.active
        } for w in webhooks]
    })

@api_view(['POST'])
def delete_webhook(request):
    '''Delete a webhook'''
    webhook_id = request.data.get('webhook_id')
    try:
        webhook = JobWebhook.objects.get(id=webhook_id)
        webhook.delete()
        return JsonResponse({'status': 'deleted'})
    except JobWebhook.DoesNotExist:
        return JsonResponse({'error': 'Webhook not found'}, status=404)

webhook_manager = WebhookManager()
"""

    def generate_fastapi_webhooks(self) -> str:
        """Generate FastAPI webhook handlers"""
        return """
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import json
import hashlib
import hmac
import httpx
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/webhooks', tags=['webhooks'])

class WebhookRequest(BaseModel):
    url: str
    events: List[str]
    secret: str

class Webhook(BaseModel):
    id: str
    url: str
    events: List[str]
    active: bool

class WebhookManager:
    def __init__(self):
        self.webhooks = {}
        self.max_retries = 3
        self.timeout = 5

    def register(self, url: str, events: list, secret: str) -> dict:
        '''Register webhook'''
        import uuid
        webhook_id = str(uuid.uuid4())
        self.webhooks[webhook_id] = {
            'url': url,
            'events': events,
            'secret': secret,
            'active': True
        }
        logger.info(f'Webhook registered: {webhook_id}')
        return {'id': webhook_id, 'url': url, 'events': events}

    async def trigger(self, job_id: str, event: str, data: dict):
        '''Trigger webhooks for event'''
        for webhook_id, webhook in self.webhooks.items():
            if event in webhook['events'] and webhook['active']:
                await self._deliver(webhook, job_id, event, data)

    async def _deliver(self, webhook: dict, job_id: str, event: str, data: dict):
        '''Deliver webhook with retry'''
        payload = {
            'job_id': job_id,
            'event': event,
            'data': data,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }

        headers = self._generate_headers(webhook, payload)

        async with httpx.AsyncClient() as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(
                        webhook['url'],
                        json=payload,
                        headers=headers,
                        timeout=self.timeout
                    )
                    if response.status_code == 200:
                        logger.info(f'Webhook delivered')
                        return
                except Exception as e:
                    logger.warning(f'Attempt {attempt + 1} failed: {e}')

        logger.error(f'Webhook delivery failed after {self.max_retries} attempts')

    def _generate_headers(self, webhook: dict, payload: dict) -> dict:
        '''Generate signature headers'''
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            webhook['secret'].encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        return {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature,
            'X-Webhook-Timestamp': str(__import__('time').time())
        }

webhook_manager = WebhookManager()

@router.post('/register', status_code=201)
async def register_webhook(request: WebhookRequest):
    '''Register webhook'''
    webhook = webhook_manager.register(request.url, request.events, request.secret)
    return webhook

@router.get('/list')
async def list_webhooks():
    '''List webhooks'''
    return {
        'webhooks': [
            {
                'id': wid,
                'url': w['url'],
                'events': w['events'],
                'active': w['active']
            }
            for wid, w in webhook_manager.webhooks.items()
        ]
    }

@router.post('/delete')
async def delete_webhook(webhook_id: str):
    '''Delete webhook'''
    if webhook_id not in webhook_manager.webhooks:
        raise HTTPException(status_code=404, detail='Webhook not found')

    del webhook_manager.webhooks[webhook_id]
    return {'status': 'deleted'}
"""

    def generate_nestjs_webhooks(self) -> str:
        """Generate NestJS webhook handlers"""
        return """
import {
  Controller,
  Post,
  Get,
  Delete,
  Body,
  Query,
  HttpStatus,
  HttpCode,
} from '@nestjs/common';
import { Injectable } from '@nestjs/core';
import * as crypto from 'crypto';
import axios from 'axios';

interface WebhookDto {
  url: string;
  events: string[];
  secret: string;
}

@Injectable()
export class WebhookService {
  private webhooks: Map<string, any> = new Map();
  private maxRetries = 3;
  private timeout = 5000;

  register(url: string, events: string[], secret: string): any {
    const id = crypto.randomUUID();
    this.webhooks.set(id, { url, events, secret, active: true });
    return { id, url, events };
  }

  async trigger(jobId: string, event: string, data: any): Promise<void> {
    for (const [id, webhook] of this.webhooks.entries()) {
      if (webhook.events.includes(event) && webhook.active) {
        await this.deliver(webhook, jobId, event, data);
      }
    }
  }

  private async deliver(webhook: any, jobId: string, event: string, data: any): Promise<void> {
    const payload = {
      jobId,
      event,
      data,
      timestamp: new Date().toISOString(),
    };

    const headers = this.generateHeaders(webhook, payload);

    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        const response = await axios.post(webhook.url, payload, {
          headers,
          timeout: this.timeout,
        });

        if (response.status === 200) {
          console.log('Webhook delivered');
          return;
        }
      } catch (error) {
        console.warn(`Webhook delivery attempt ${attempt + 1} failed:`, error.message);
      }
    }

    console.error('Webhook delivery failed after max retries');
  }

  private generateHeaders(webhook: any, payload: any): Record<string, string> {
    const payloadStr = JSON.stringify(payload, Object.keys(payload).sort());
    const signature = crypto
      .createHmac('sha256', webhook.secret)
      .update(payloadStr)
      .digest('hex');

    return {
      'Content-Type': 'application/json',
      'X-Webhook-Signature': signature,
      'X-Webhook-Timestamp': String(Date.now() / 1000),
    };
  }

  list(): any[] {
    return Array.from(this.webhooks.entries()).map(([id, webhook]) => ({
      id,
      url: webhook.url,
      events: webhook.events,
      active: webhook.active,
    }));
  }

  delete(webhookId: string): boolean {
    return this.webhooks.delete(webhookId);
  }
}

@Controller('api/webhooks')
export class WebhookController {
  constructor(private readonly webhookService: WebhookService) {}

  @Post('register')
  @HttpCode(HttpStatus.CREATED)
  register(@Body() request: WebhookDto) {
    return this.webhookService.register(request.url, request.events, request.secret);
  }

  @Get('list')
  list() {
    return { webhooks: this.webhookService.list() };
  }

  @Delete('delete')
  delete(@Query('webhookId') webhookId: string) {
    if (!this.webhookService.delete(webhookId)) {
      throw new Error('Webhook not found');
    }
    return { status: 'deleted' };
  }
}
"""


def generate_webhook_handler(framework: str, language: str) -> Dict[str, str]:
    """
    Generate webhook handler code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = WebhookHandler(framework, language)
    output = {}

    if language == "python":
        if framework == "django":
            output["webhooks.py"] = generator.generate_django_webhooks()
        elif framework == "fastapi":
            output["webhooks.py"] = generator.generate_fastapi_webhooks()
    elif language == "javascript":
        output["webhook.service.ts"] = generator.generate_nestjs_webhooks()

    return output
