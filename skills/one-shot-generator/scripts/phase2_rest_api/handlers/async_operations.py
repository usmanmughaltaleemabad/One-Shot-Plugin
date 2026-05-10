"""
Async Operations - Asynchronous endpoint generation

Generates:
- Async/await endpoints
- Background tasks
- Celery task integration
- WebSocket support
"""

from typing import Dict, Any, List, Optional


class AsyncOperationsHandler:
    """Generate async operation code"""

    def __init__(self, framework: str, resource_name: str):
        self.framework = framework
        self.resource_name = resource_name

    def generate_django_async(self) -> str:
        """Generate Django async endpoints"""
        return f"""
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from rest_framework.decorators import api_view
from rest_framework.response import Response
from celery import shared_task
import asyncio

# Async view using async_view decorator
@sync_to_async
def get_{self.resource_name}_from_db(id):
    '''Synchronous DB query wrapped for async'''
    from ..models import {self.resource_name.capitalize()}
    return {self.resource_name.capitalize()}.objects.get(pk=id)

async def retrieve_{self.resource_name}_async(request, id):
    '''Async endpoint for retrieving {self.resource_name}'''
    try:
        obj = await get_{self.resource_name}_from_db(id)
        return Response({{'id': obj.id, 'name': obj.name}})
    except Exception as e:
        return Response({{'error': str(e)}}, status=400)

# Celery background tasks
@shared_task
def process_{self.resource_name}_async(id):
    '''Background task to process {self.resource_name}'''
    from ..models import {self.resource_name.capitalize()}
    try:
        obj = {self.resource_name.capitalize()}.objects.get(pk=id)
        # Long-running operation
        return {{'status': 'processed', 'id': id}}
    except Exception as e:
        return {{'error': str(e)}}

@shared_task
def bulk_process_{self.resource_plural}_async(ids):
    '''Background task to process multiple {self.resource_plural}'''
    results = []
    for id in ids:
        result = process_{self.resource_name}_async.delay(id)
        results.append(result.id)
    return {{'tasks': results}}

# Async signal handlers
from django.db.models.signals import post_save
from asgiref.sync import async_to_sync

@async_to_sync
async def on_{self.resource_name}_created(sender, instance, **kwargs):
    '''Handle {self.resource_name} creation asynchronously'''
    await sync_to_async(lambda: print(f'{{instance.name}} created'))()

post_save.connect(on_{self.resource_name}_created, sender=__name__)

# Task queue monitoring
class TaskStatusMonitor:
    @staticmethod
    def get_task_status(task_id):
        from celery.result import AsyncResult
        result = AsyncResult(task_id)
        return {{
            'task_id': task_id,
            'status': result.status,
            'result': result.result if result.ready() else None
        }}

    @staticmethod
    def cancel_task(task_id):
        from celery.result import AsyncResult
        result = AsyncResult(task_id)
        result.revoke(terminate=True)
        return {{'cancelled': True}}
"""

    def generate_fastapi_async(self) -> str:
        """Generate FastAPI async endpoints"""
        return f"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import asyncio
from typing import Optional

router = APIRouter()

class TaskResult(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None

class AsyncTaskManager:
    '''Manage async tasks'''

    _tasks = {{}}

    @classmethod
    async def create_task(cls, task_id: str, coroutine):
        '''Create and track async task'''
        task = asyncio.create_task(coroutine)
        cls._tasks[task_id] = task
        return task

    @classmethod
    def get_task_status(cls, task_id: str):
        '''Get task status'''
        if task_id not in cls._tasks:
            return {{'status': 'not_found'}}

        task = cls._tasks[task_id]
        if task.done():
            try:
                result = task.result()
                return {{'status': 'completed', 'result': result}}
            except Exception as e:
                return {{'status': 'failed', 'error': str(e)}}
        else:
            return {{'status': 'pending'}}

# Async endpoint for creating {self.resource_name}
@router.post('/{{id}}/process-async')
async def process_{self.resource_name}_async(
    id: int,
    background_tasks: BackgroundTasks
):
    '''Process {self.resource_name} asynchronously'''

    async def long_running_task(resource_id: int):
        await asyncio.sleep(5)  # Simulate long operation
        return {{'processed': resource_id}}

    # Option 1: Return immediately with background task
    background_tasks.add_task(asyncio.create_task, long_running_task(id))

    return {{'status': 'processing', 'resource_id': id}}

@router.post('/bulk-process-async')
async def bulk_process_async(
    ids: list,
    background_tasks: BackgroundTasks
):
    '''Bulk process {self.resource_plural} asynchronously'''

    async def process_all(ids: list):
        tasks = [process_{self.resource_name}_internal(id) for id in ids]
        return await asyncio.gather(*tasks)

    background_tasks.add_task(asyncio.create_task, process_all(ids))

    return {{'status': 'processing', 'count': len(ids)}}

async def process_{self.resource_name}_internal(id: int):
    '''Internal async processing function'''
    await asyncio.sleep(2)
    return {{'id': id, 'status': 'processed'}}

# Task status monitoring
@router.get('/tasks/{{task_id}}/status')
async def get_task_status(task_id: str):
    '''Get async task status'''
    return AsyncTaskManager.get_task_status(task_id)

# Stream responses
@router.get('/stream')
async def stream_{self.resource_plural}():
    '''Stream {self.resource_plural} asynchronously'''

    async def generate():
        for i in range(10):
            yield f'{{'id': {{i}}}}\n'
            await asyncio.sleep(1)

    return generate()
"""


def generate_async_operations(
    framework: str,
    resource_name: str
) -> Dict[str, str]:
    """
    Generate async operations code.

    Args:
        framework: django or fastapi
        resource_name: e.g., "user"

    Returns: dict of {filename: code_content}
    """
    handler = AsyncOperationsHandler(framework, resource_name)
    output = {}

    if framework == "django":
        output["async_operations.py"] = handler.generate_django_async()
    elif framework == "fastapi":
        output["async_operations.py"] = handler.generate_fastapi_async()

    return output
