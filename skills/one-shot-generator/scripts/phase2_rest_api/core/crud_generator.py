"""
CRUD REST API Generator - Phase 2

Generates complete CRUD endpoint implementations for REST APIs.
Supports: Django, FastAPI, Spring Boot, Go, NestJS.

One-shot generation of:
  - GET endpoints (list with pagination/filtering)
  - GET by ID
  - POST (create)
  - PUT/PATCH (update)
  - DELETE

Framework-aware: generates idiomatic code per framework.
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class CRUDConfig:
    """Configuration for CRUD endpoint generation"""
    framework: str  # django, fastapi, spring, go, nestjs
    language: str   # python, java, go, typescript
    resource_name: str  # e.g., "user", "product"
    resource_plural: str  # e.g., "users", "products"
    has_authentication: bool = True
    supports_soft_delete: bool = False
    include_timestamps: bool = True
    pagination_style: str = "offset"  # offset, cursor, keyset
    api_version: str = "v1"


class CRUDGenerator:
    """Generate CRUD REST API endpoints"""

    def __init__(self, config: CRUDConfig):
        self.config = config
        self.framework_handlers = {
            "django": self._generate_django_crud,
            "fastapi": self._generate_fastapi_crud,
            "spring": self._generate_spring_crud,
            "go": self._generate_go_crud,
            "nestjs": self._generate_nestjs_crud,
        }

    def generate(self) -> Dict[str, str]:
        """
        Generate all CRUD endpoints for the configured resource.

        Returns: dict of {filename: code_content}
        """
        handler = self.framework_handlers.get(self.config.framework)
        if not handler:
            raise ValueError(f"Unsupported framework: {self.config.framework}")

        return handler()

    def _generate_django_crud(self) -> Dict[str, str]:
        """Generate Django REST Framework CRUD endpoints"""

        resource = self.config.resource_name
        plural = self.config.resource_plural
        model_name = resource.capitalize()

        # Model
        model_code = f"""
from django.db import models
from django.contrib.auth.models import User

class {model_name}(models.Model):
    \"\"\"{{resource}} model\"\"\"
    # Replace with actual fields
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='{plural}')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return self.name


class {model_name}Serializer(serializers.ModelSerializer):
    \"\"\"Serializer for {{resource}}\"\"\"
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = {model_name}
        fields = ['id', 'name', 'description', 'user_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_id']


class {model_name}CreateSerializer(serializers.ModelSerializer):
    \"\"\"Serializer for creating {{resource}}\"\"\"

    class Meta:
        model = {model_name}
        fields = ['name', 'description']

    def validate_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters")
        return value


class {model_name}UpdateSerializer(serializers.ModelSerializer):
    \"\"\"Serializer for updating {{resource}}\"\"\"

    class Meta:
        model = {model_name}
        fields = ['name', 'description']
"""

        # ViewSet
        viewset_code = f"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import {model_name}
from .serializers import {model_name}Serializer, {model_name}CreateSerializer, {model_name}UpdateSerializer


class {model_name}Pagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class {model_name}ViewSet(viewsets.ModelViewSet):
    \"\"\"
    CRUD endpoints for {resource}.

    list:   GET /{plural}
    create: POST /{plural}
    retrieve: GET /{plural}/{{id}}
    update: PUT /{plural}/{{id}}
    partial_update: PATCH /{plural}/{{id}}
    destroy: DELETE /{plural}/{{id}}
    \"\"\"

    queryset = {model_name}.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = {model_name}Pagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['user']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        \"\"\"Filter {plural} by current user\"\"\"
        return {model_name}.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return {model_name}CreateSerializer
        elif self.action in ['update', 'partial_update']:
            return {model_name}UpdateSerializer
        return {model_name}Serializer

    def perform_create(self, serializer):
        \"\"\"Set user when creating{{resource}}\"\"\"
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        \"\"\"Clone a {{resource}}\"\"\"
        obj = self.get_object()
        obj.pk = None
        obj.save()
        serializer = self.get_serializer(obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# URLs
from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'{plural}', {model_name}ViewSet, basename='{resource}')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
"""

        # Tests
        test_code = f"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import {model_name}


class {model_name}APITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.url = '/api/v1/{plural}/'

    def test_list_{plural}(self):
        \"\"\"Test listing {{plural}}\"\"\"
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_create_{resource}(self):
        \"\"\"Test creating {{resource}}\"\"\"
        data = {{'name': 'Test {{resource}}', 'description': 'Test'}}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual({model_name}.objects.count(), 1)

    def test_retrieve_{resource}(self):
        \"\"\"Test retrieving single {{resource}}\"\"\"
        obj = {model_name}.objects.create(name='Test', user=self.user)
        response = self.client.get(f'{{self.url}}{{obj.id}}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_{resource}(self):
        \"\"\"Test updating {{resource}}\"\"\"
        obj = {model_name}.objects.create(name='Test', user=self.user)
        data = {{'name': 'Updated'}}
        response = self.client.patch(f'{{self.url}}{{obj.id}}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_{resource}(self):
        \"\"\"Test deleting {{resource}}\"\"\"
        obj = {model_name}.objects.create(name='Test', user=self.user)
        response = self.client.delete(f'{{self.url}}{{obj.id}}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual({model_name}.objects.count(), 0)

    def test_pagination(self):
        \"\"\"Test pagination\"\"\"
        for i in range(25):
            {model_name}.objects.create(name=f'Test {{i}}', user=self.user)
        response = self.client.get(self.url)
        self.assertIn('next', response.data)
        self.assertEqual(len(response.data['results']), 20)

    def test_filtering(self):
        \"\"\"Test filtering\"\"\"
        other_user = User.objects.create_user(username='other', password='pass')
        {model_name}.objects.create(name='User1', user=self.user)
        {model_name}.objects.create(name='User2', user=other_user)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data['results']), 1)
"""

        return {
            f"{resource}/models.py": model_code,
            f"{resource}/viewsets.py": viewset_code,
            f"{resource}/tests.py": test_code,
        }

    def _generate_fastapi_crud(self) -> Dict[str, str]:
        """Generate FastAPI CRUD endpoints"""
        resource = self.config.resource_name
        plural = self.config.resource_plural

        router_code = f"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from database import get_db
from models import {resource.capitalize()}

router = APIRouter(prefix="/api/v1/{plural}", tags=["{resource}"])

class {resource.capitalize()}Schema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class {resource.capitalize()}CreateSchema(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None

@router.get("/", response_model=List[{resource.capitalize()}Schema])
async def list_{plural}(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    \"\"\"List all {{plural}} with pagination and filtering\"\"\"
    query = db.query({resource.capitalize()})
    if search:
        query = query.filter({resource.capitalize()}.name.ilike(f"%{{search}}%"))
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model={resource.capitalize()}Schema, status_code=201)
async def create_{resource}(
    data: {resource.capitalize()}CreateSchema,
    db: Session = Depends(get_db)
):
    \"\"\"Create new {{resource}}\"\"\"
    obj = {resource.capitalize()}(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/{{id}}", response_model={resource.capitalize()}Schema)
async def retrieve_{resource}(id: int, db: Session = Depends(get_db)):
    \"\"\"Retrieve single {{resource}}\"\"\"
    obj = db.query({resource.capitalize()}).filter({resource.capitalize()}.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return obj

@router.put("/{{id}}", response_model={resource.capitalize()}Schema)
async def update_{resource}(
    id: int,
    data: {resource.capitalize()}CreateSchema,
    db: Session = Depends(get_db)
):
    \"\"\"Update {{resource}}\"\"\"
    obj = db.query({resource.capitalize()}).filter({resource.capitalize()}.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    for key, value in data.dict().items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/{{id}}", status_code=204)
async def delete_{resource}(id: int, db: Session = Depends(get_db)):
    \"\"\"Delete {{resource}}\"\"\"
    obj = db.query({resource.capitalize()}).filter({resource.capitalize()}.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(obj)
    db.commit()
"""

        return {
            f"{resource}/router.py": router_code,
        }

    def _generate_spring_crud(self) -> Dict[str, str]:
        """Generate Spring Boot CRUD endpoints"""
        # Placeholder - will be implemented
        return {"spring_rest_api.java": "// Spring CRUD implementation (coming soon)"}

    def _generate_go_crud(self) -> Dict[str, str]:
        """Generate Go REST API endpoints"""
        # Placeholder - will be implemented
        return {"go_rest_api.go": "// Go CRUD implementation (coming soon)"}

    def _generate_nestjs_crud(self) -> Dict[str, str]:
        """Generate NestJS CRUD endpoints"""
        # Placeholder - will be implemented
        return {"nestjs_rest_api.ts": "// NestJS CRUD implementation (coming soon)"}


def generate_crud_endpoints(
    framework: str,
    language: str,
    resource_name: str,
    **kwargs
) -> Dict[str, str]:
    """
    Generate CRUD endpoints.

    Args:
        framework: django, fastapi, spring, go, nestjs
        language: python, java, go, typescript
        resource_name: e.g., "user", "product"
        **kwargs: additional config options

    Returns: dict of {filename: code_content}
    """
    resource_plural = kwargs.get('resource_plural', f"{resource_name}s")

    config = CRUDConfig(
        framework=framework,
        language=language,
        resource_name=resource_name,
        resource_plural=resource_plural,
        **{k: v for k, v in kwargs.items() if k != 'resource_plural'}
    )

    generator = CRUDGenerator(config)
    return generator.generate()
