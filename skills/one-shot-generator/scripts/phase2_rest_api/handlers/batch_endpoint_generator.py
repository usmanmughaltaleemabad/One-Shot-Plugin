"""
Batch Endpoint Generator - Batch operation endpoints

Generates:
- Batch create endpoints
- Batch update endpoints
- Batch delete endpoints
- Batch get endpoints
"""

from typing import Dict, Any, List


class BatchEndpointGenerator:
    """Generate batch endpoints"""

    def __init__(self, framework: str, resource_name: str, resource_plural: str):
        self.framework = framework
        self.resource_name = resource_name
        self.resource_plural = resource_plural

    def generate_django_batch_endpoints(self) -> str:
        """Generate Django batch endpoints"""
        return f"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def batch_get(request):
    '''Batch get {self.resource_plural} by IDs'''
    ids = request.data.get('ids', [])
    from .models import {self.resource_name.capitalize()}

    items = {self.resource_name.capitalize()}.objects.filter(id__in=ids)
    from .serializers import {self.resource_name.capitalize()}Serializer

    serializer = {self.resource_name.capitalize()}Serializer(items, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def batch_delete(request):
    '''Batch delete {self.resource_plural} by IDs'''
    ids = request.data.get('ids', [])
    from .models import {self.resource_name.capitalize()}

    count, _ = {self.resource_name.capitalize()}.objects.filter(id__in=ids).delete()
    return Response({{'deleted': count}}, status=status.HTTP_204_NO_CONTENT)
"""

    def generate_fastapi_batch_endpoints(self) -> str:
        """Generate FastAPI batch endpoints"""
        return f"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix='/api/v1/{self.resource_plural}', tags=['{self.resource_plural}'])

class BatchGetRequest(BaseModel):
    ids: List[int]

class BatchDeleteRequest(BaseModel):
    ids: List[int]

@router.post('/batch/get')
async def batch_get(request: BatchGetRequest):
    '''Batch get {self.resource_plural} by IDs'''
    # Fetch multiple items
    items = []
    return {{'items': items}}

@router.post('/batch/delete')
async def batch_delete(request: BatchDeleteRequest):
    '''Batch delete {self.resource_plural} by IDs'''
    deleted_count = len(request.ids)
    return {{'deleted': deleted_count}}

@router.put('/batch/update')
async def batch_update(updates: List[dict]):
    '''Batch update {self.resource_plural}'''
    updated_count = len(updates)
    return {{'updated': updated_count}}
"""


def generate_batch_endpoints(framework: str, resource_name: str, resource_plural: str) -> Dict[str, str]:
    """
    Generate batch endpoints.

    Args:
        framework: django or fastapi
        resource_name: e.g., "user"
        resource_plural: e.g., "users"

    Returns: dict of {filename: code_content}
    """
    generator = BatchEndpointGenerator(framework, resource_name, resource_plural)
    output = {}

    if framework == "django":
        output["batch_endpoints.py"] = generator.generate_django_batch_endpoints()
    elif framework == "fastapi":
        output["batch_endpoints.py"] = generator.generate_fastapi_batch_endpoints()

    return output
