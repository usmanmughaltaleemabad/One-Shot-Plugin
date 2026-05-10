"""
Versioning Handler - API versioning strategies

Generates:
- URL-based versioning (e.g., /v1/, /v2/)
- Header-based versioning (Accept: application/json; version=2)
- Query parameter versioning
- Version negotiation
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class APIVersion:
    """API version definition"""
    major: int
    minor: int
    patch: int
    deprecated: bool = False
    sunset_date: Optional[str] = None

    def __str__(self):
        return f"v{self.major}.{self.minor}.{self.patch}"


class VersioningHandler:
    """Generate API versioning code"""

    def __init__(self, framework: str):
        self.framework = framework

    def generate_django_versioning(self) -> str:
        """Generate Django REST Framework versioning"""
        return """
from rest_framework.versioning import (
    URLPathVersioning,
    AcceptHeaderVersioning,
    NamespaceVersioning
)
from rest_framework.response import Response
from rest_framework.decorators import api_view, versioning_classes

# URL Path Versioning (e.g., /api/v1/users/)
class CustomURLPathVersioning(URLPathVersioning):
    invalid_version_message = 'Invalid API version'

    def determine_version(self, request, *args, **kwargs):
        version, scheme = super().determine_version(request, *args, **kwargs)
        if version not in ['v1', 'v2', 'v3']:
            self.invalid_version_message = f'Version {version} is not supported'
        return version

# Accept Header Versioning (e.g., Accept: application/json; version=2)
class CustomAcceptHeaderVersioning(AcceptHeaderVersioning):
    invalid_version_message = 'Invalid API version in Accept header'

# Query Parameter Versioning (e.g., ?api_version=2)
class CustomQueryParameterVersioning(QueryParameterVersioning):
    valid_version = ['1.0', '2.0', '2.1']
    example_media_type = 'application/json; version=2.0'

REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1', 'v2', 'v3']
}

class APIVersionManager:
    @staticmethod
    def get_version(request):
        return request.version

    @staticmethod
    def is_deprecated(version: str) -> bool:
        deprecated_versions = ['v1']
        return version in deprecated_versions

    @staticmethod
    def get_sunset_date(version: str) -> str:
        sunset_dates = {
            'v1': '2027-01-01',
            'v2': '2028-01-01',
        }
        return sunset_dates.get(version)

@api_view(['GET'])
@versioning_classes([CustomURLPathVersioning])
def versioned_endpoint(request):
    version = request.version
    return Response({'version': version, 'data': []})

# Deprecation headers middleware
class DeprecationHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        version = request.version
        if APIVersionManager.is_deprecated(version):
            sunset_date = APIVersionManager.get_sunset_date(version)
            response['Sunset'] = sunset_date
            response['Deprecation'] = 'true'
            response['Warning'] = f'299 - "API {version} is deprecated, will be removed on {sunset_date}"'

        return response
"""

    def generate_fastapi_versioning(self) -> str:
        """Generate FastAPI versioning"""
        return """
from fastapi import APIRouter, Header, HTTPException, status
from typing import Optional
from pydantic import BaseModel

# URL Path Versioning
v1_router = APIRouter(prefix='/api/v1', tags=['v1'])
v2_router = APIRouter(prefix='/api/v2', tags=['v2'])

@v1_router.get('/users/')
async def list_users_v1():
    return {'version': '1.0', 'data': []}

@v2_router.get('/users/')
async def list_users_v2():
    return {'version': '2.0', 'data': [], 'metadata': {}}

# Header-based versioning
async def get_api_version(accept_version: Optional[str] = Header(None)) -> str:
    '''Extract API version from Accept header'''
    if not accept_version:
        return '1.0'

    valid_versions = ['1.0', '2.0', '2.1']
    if accept_version not in valid_versions:
        raise HTTPException(status_code=406, detail=f'Version {accept_version} not supported')

    return accept_version

# Query parameter versioning
@v1_router.get('/data/')
async def get_data(api_version: str = '1.0'):
    if api_version not in ['1.0', '2.0', '2.1']:
        raise HTTPException(status_code=400, detail='Invalid api_version')

    return {'version': api_version, 'data': []}

class APIVersionConfig:
    CURRENT_VERSION = '2.1'
    SUPPORTED_VERSIONS = ['1.0', '2.0', '2.1']
    DEPRECATED_VERSIONS = ['1.0']

    @staticmethod
    def is_supported(version: str) -> bool:
        return version in APIVersionConfig.SUPPORTED_VERSIONS

    @staticmethod
    def is_deprecated(version: str) -> bool:
        return version in APIVersionConfig.DEPRECATED_VERSIONS

    @staticmethod
    def get_sunset_date(version: str) -> str:
        sunset_dates = {
            '1.0': '2027-01-01',
            '2.0': '2028-01-01',
        }
        return sunset_dates.get(version)

class VersionedResponse(BaseModel):
    version: str
    data: dict
    deprecation_notice: Optional[str] = None

async def add_deprecation_headers(response, version: str):
    '''Add deprecation headers to response'''
    if APIVersionConfig.is_deprecated(version):
        sunset = APIVersionConfig.get_sunset_date(version)
        response.headers['Deprecation'] = 'true'
        response.headers['Sunset'] = sunset
        response.headers['Warning'] = f'299 - "API {version} is deprecated"'
    return response
"""


def generate_versioning(framework: str) -> Dict[str, str]:
    """
    Generate versioning code.

    Args:
        framework: django or fastapi

    Returns: dict of {filename: code_content}
    """
    handler = VersioningHandler(framework)
    output = {}

    if framework == "django":
        output["versioning.py"] = handler.generate_django_versioning()
    elif framework == "fastapi":
        output["versioning.py"] = handler.generate_fastapi_versioning()

    return output
