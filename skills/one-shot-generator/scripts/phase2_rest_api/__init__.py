"""
Phase 2 REST API Specialist Module

Generates complete REST API implementations with:
- CRUD endpoints (GET, POST, PUT, DELETE)
- Request/response validation
- Pagination, filtering, sorting
- OpenAPI/Swagger documentation
- Authentication & authorization
- Error handling
- Comprehensive test suite

Supported frameworks: Django, FastAPI, Spring Boot, Go, NestJS
Supported languages: Python, Java, Go, TypeScript

Usage:
    from orchestrator_phase2 import orchestrate_phase2

    config = {
        "framework": "fastapi",
        "language": "python",
        "api_name": "User Service",
        "api_version": "v1",
        "base_path": "/api/v1",
        "resources": [
            {
                "name": "user",
                "plural": "users",
                "schema": {"type": "object", "properties": {...}}
            }
        ]
    }

    result = orchestrate_phase2(config)
    # result["code"] contains generated API code
    # result["tests"] contains test suite
    # result["docs"] contains OpenAPI spec and docs
"""

__version__ = "2.0.0"
__author__ = "One-Shot Prompting Team"

from .orchestrator_phase2 import Phase2Orchestrator, orchestrate_phase2
from .core.crud_generator import CRUDGenerator
from .validators.api_validator import APIValidator
from .generators.openapi_generator import OpenAPIGenerator
from .handlers.pagination_handler import (
    PaginationGenerator,
    FilteringGenerator,
    SortingGenerator
)
from .handlers.request_validator import RequestValidatorGenerator

__all__ = [
    "Phase2Orchestrator",
    "orchestrate_phase2",
    "CRUDGenerator",
    "APIValidator",
    "OpenAPIGenerator",
    "PaginationGenerator",
    "FilteringGenerator",
    "SortingGenerator",
    "RequestValidatorGenerator"
]
