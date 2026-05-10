"""
ETag Generator - HTTP ETag and conditional request support

Generates:
- ETag computation
- If-None-Match handling
- If-Modified-Since support
- Cache validation
"""

from typing import Dict, Any, Optional
import hashlib


class ETagGenerator:
    """Generate ETag support code"""

    def __init__(self, framework: str):
        self.framework = framework

    def generate_django_etags(self) -> str:
        """Generate Django ETag support"""
        return """
import hashlib
from django.views.decorators.http import condition
from django.http import HttpResponse
from django.utils.http import parse_etags
from rest_framework.decorators import api_view
from rest_framework.response import Response

def compute_etag(data: dict) -> str:
    '''Compute ETag from data'''
    data_str = str(data)
    return hashlib.md5(data_str.encode()).hexdigest()

def get_last_modified(obj):
    '''Get last modified timestamp'''
    return obj.updated_at if hasattr(obj, 'updated_at') else None

class ETagMixin:
    '''Mixin to add ETag support to views'''

    def get_etag(self, request, *args, **kwargs):
        '''Compute ETag for response'''
        response = super().get(request, *args, **kwargs)
        if response.status_code == 200:
            etag = compute_etag(response.data)
            response['ETag'] = f'"{etag}"'
        return response

    def head(self, request, *args, **kwargs):
        '''HEAD request with ETag'''
        response = self.get(request, *args, **kwargs)
        response.content = b''
        return response

def etag_conditional(view_func):
    '''Decorator for ETag conditional requests'''
    def wrapper(request, *args, **kwargs):
        # Get response
        response = view_func(request, *args, **kwargs)

        if request.method == 'GET' and response.status_code == 200:
            # Compute ETag
            etag = compute_etag(response.data)
            response['ETag'] = f'"{etag}"'

            # Check If-None-Match
            if_none_match = request.META.get('HTTP_IF_NONE_MATCH')
            if if_none_match:
                client_etags = parse_etags(if_none_match)
                if etag in client_etags or '*' in client_etags:
                    return HttpResponse(status=304)  # Not Modified

        return response
    return wrapper

class ConditionalGetMixin:
    '''Support for conditional GET requests'''

    def get(self, request, *args, **kwargs):
        '''GET with conditional support'''
        response = super().get(request, *args, **kwargs)

        if response.status_code == 200:
            # Add ETag
            etag = compute_etag(response.data)
            response['ETag'] = f'"{etag}"'

            # Add Cache-Control
            response['Cache-Control'] = 'public, max-age=3600'

        return response
"""

    def generate_fastapi_etags(self) -> str:
        """Generate FastAPI ETag support"""
        return """
import hashlib
from fastapi import Header, Response, status
from typing import Optional

def compute_etag(data: dict) -> str:
    '''Compute ETag from data'''
    data_str = str(data)
    return hashlib.md5(data_str.encode()).hexdigest()

async def get_with_etag(
    data: dict,
    if_none_match: Optional[str] = Header(None),
    response: Response = None
) -> dict:
    '''Get with ETag support'''
    etag = compute_etag(data)

    # Check If-None-Match
    if if_none_match:
        if if_none_match.strip('\"') == etag or if_none_match == '*':
            response.status_code = status.HTTP_304_NOT_MODIFIED
            return None

    # Set ETag header
    response.headers['ETag'] = f'"{etag}"'
    response.headers['Cache-Control'] = 'public, max-age=3600'

    return data

class ETagManager:
    @staticmethod
    def generate_etag(data: dict) -> str:
        '''Generate ETag'''
        return compute_etag(data)

    @staticmethod
    def is_match(etag: str, if_match: str) -> bool:
        '''Check if ETag matches'''
        return if_match.strip('\"') == etag

    @staticmethod
    def is_not_match(etag: str, if_none_match: str) -> bool:
        '''Check if ETag does not match'''
        return if_none_match.strip('\"') != etag

def add_etag_headers(response: Response, data: dict):
    '''Add ETag headers to response'''
    etag = compute_etag(data)
    response.headers['ETag'] = f'"{etag}"'
    response.headers['Cache-Control'] = 'public, max-age=3600'
    return response
"""


def generate_etags(framework: str) -> Dict[str, str]:
    """
    Generate ETag code.

    Args:
        framework: django or fastapi

    Returns: dict of {filename: code_content}
    """
    generator = ETagGenerator(framework)
    output = {}

    if framework == "django":
        output["etags.py"] = generator.generate_django_etags()
    elif framework == "fastapi":
        output["etags.py"] = generator.generate_fastapi_etags()

    return output
