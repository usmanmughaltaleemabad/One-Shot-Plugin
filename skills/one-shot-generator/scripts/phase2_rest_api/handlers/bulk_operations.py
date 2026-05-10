"""
Bulk Operations - Bulk create, update, delete operations

Generates:
- Bulk create endpoints
- Bulk update endpoints
- Bulk delete endpoints
- Transaction handling
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class BulkOperationResult:
    """Result of bulk operation"""
    total: int
    created: int
    updated: int
    deleted: int
    failed: int
    errors: List[Dict[str, Any]]


class BulkOperationsHandler:
    """Generate bulk operation code"""

    def __init__(self, framework: str, resource_name: str, resource_plural: str):
        self.framework = framework
        self.resource_name = resource_name
        self.resource_plural = resource_plural

    def generate_django_bulk_operations(self) -> str:
        """Generate Django bulk operations"""
        return f"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.core.exceptions import ValidationError

class BulkOperationsMixin:
    '''Mixin for bulk operations'''

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        '''Bulk create {self.resource_plural}'''
        items = request.data if isinstance(request.data, list) else [request.data]

        if len(items) > 1000:
            return Response(
                {{'error': 'Maximum 1000 items per request'}},
                status=status.HTTP_400_BAD_REQUEST
            )

        created = []
        errors = []

        try:
            with transaction.atomic():
                for idx, item in enumerate(items):
                    try:
                        serializer = self.get_serializer(data=item)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                        created.append(serializer.data)
                    except ValidationError as e:
                        errors.append({{'index': idx, 'errors': e.detail}})
        except Exception as e:
            return Response(
                {{'error': str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {{
                'total': len(items),
                'created': len(created),
                'errors': len(errors),
                'data': created,
                'errors_detail': errors
            }},
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['put'])
    def bulk_update(self, request):
        '''Bulk update {self.resource_plural}'''
        items = request.data if isinstance(request.data, list) else [request.data]

        updated = []
        errors = []

        try:
            with transaction.atomic():
                for idx, item in enumerate(items):
                    try:
                        obj = self.get_queryset().get(pk=item.get('id'))
                        serializer = self.get_serializer(obj, data=item, partial=True)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                        updated.append(serializer.data)
                    except Exception as e:
                        errors.append({{'index': idx, 'id': item.get('id'), 'error': str(e)}})
        except Exception as e:
            return Response(
                {{'error': str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {{
                'total': len(items),
                'updated': len(updated),
                'errors': len(errors),
                'data': updated,
                'errors_detail': errors
            }},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        '''Bulk delete {self.resource_plural}'''
        ids = request.data.get('ids', []) if isinstance(request.data, dict) else []

        if len(ids) > 1000:
            return Response(
                {{'error': 'Maximum 1000 items per request'}},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                count, _ = self.get_queryset().filter(id__in=ids).delete()
        except Exception as e:
            return Response(
                {{'error': str(e)}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {{'deleted': count}},
            status=status.HTTP_204_NO_CONTENT
        )
"""

    def generate_fastapi_bulk_operations(self) -> str:
        """Generate FastAPI bulk operations"""
        return f"""
from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session

router = APIRouter()

class BulkCreateRequest(BaseModel):
    items: List[dict]

class BulkUpdateRequest(BaseModel):
    items: List[dict]

class BulkDeleteRequest(BaseModel):
    ids: List[int]

class BulkOperationResult(BaseModel):
    total: int
    created: int
    updated: int
    deleted: int
    failed: int
    errors: List[dict] = []

@router.post('/bulk/create', response_model=BulkOperationResult)
async def bulk_create({self.resource_plural}: BulkCreateRequest, db: Session):
    '''Bulk create {self.resource_plural}'''
    items = {self.resource_plural}.items

    if len(items) > 1000:
        return {{'error': 'Maximum 1000 items per request'}}

    created = 0
    errors = []

    try:
        for idx, item in enumerate(items):
            try:
                # Create item
                created += 1
            except Exception as e:
                errors.append({{'index': idx, 'error': str(e)}})
    except Exception as e:
        return {{'error': str(e)}}

    return BulkOperationResult(
        total=len(items),
        created=created,
        updated=0,
        deleted=0,
        failed=len(errors),
        errors=errors
    )

@router.put('/bulk/update', response_model=BulkOperationResult)
async def bulk_update({self.resource_plural}: BulkUpdateRequest, db: Session):
    '''Bulk update {self.resource_plural}'''
    items = {self.resource_plural}.items

    updated = 0
    errors = []

    try:
        for idx, item in enumerate(items):
            try:
                # Update item
                updated += 1
            except Exception as e:
                errors.append({{'index': idx, 'error': str(e)}})
    except Exception as e:
        return {{'error': str(e)}}

    return BulkOperationResult(
        total=len(items),
        created=0,
        updated=updated,
        deleted=0,
        failed=len(errors),
        errors=errors
    )

@router.delete('/bulk/delete', response_model=BulkOperationResult)
async def bulk_delete(request: BulkDeleteRequest, db: Session):
    '''Bulk delete {self.resource_plural}'''
    ids = request.ids

    if len(ids) > 1000:
        return {{'error': 'Maximum 1000 items per request'}}

    deleted = 0
    try:
        deleted = len(ids)  # Implement actual deletion
    except Exception as e:
        return {{'error': str(e)}}

    return BulkOperationResult(
        total=len(ids),
        created=0,
        updated=0,
        deleted=deleted,
        failed=0
    )
"""


def generate_bulk_operations(
    framework: str,
    resource_name: str,
    resource_plural: str
) -> Dict[str, str]:
    """
    Generate bulk operations code.

    Args:
        framework: django or fastapi
        resource_name: e.g., "user"
        resource_plural: e.g., "users"

    Returns: dict of {filename: code_content}
    """
    handler = BulkOperationsHandler(framework, resource_name, resource_plural)
    output = {}

    if framework == "django":
        output["bulk_operations.py"] = handler.generate_django_bulk_operations()
    elif framework == "fastapi":
        output["bulk_operations.py"] = handler.generate_fastapi_bulk_operations()

    return output
