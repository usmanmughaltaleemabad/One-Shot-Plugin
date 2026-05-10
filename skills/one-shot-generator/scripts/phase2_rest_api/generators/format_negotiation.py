"""
Format Negotiation - Content negotiation (JSON, XML, CSV, etc.)

Generates:
- Content-type negotiation
- Multiple output format support
- Format conversion
- Accept header parsing
"""

from typing import Dict, Any, List, Optional
import json
import csv
from io import StringIO


class FormatNegotiationGenerator:
    """Generate content negotiation code"""

    def __init__(self, framework: str):
        self.framework = framework

    def generate_django_format_negotiation(self) -> str:
        """Generate Django format negotiation"""
        return """
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework_xml.renderers import XMLRenderer
import csv
from io import StringIO
from django.http import HttpResponse

class CSVRenderer:
    '''Render response as CSV'''
    media_type = 'text/csv'
    format_suffix = 'csv'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if not isinstance(data, list):
            data = [data]

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys() if data else [])
        writer.writeheader()
        writer.writerows(data)

        return output.getvalue().encode()

class FormatNegotiationMixin:
    '''Mixin for format negotiation'''

    renderer_classes = [
        JSONRenderer,
        XMLRenderer,
        CSVRenderer,
        BrowsableAPIRenderer,
    ]

    def get_renderer_context(self):
        context = super().get_renderer_context()
        # Add custom format logic
        return context

class ContentNegotiationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        accept_header = request.META.get('HTTP_ACCEPT', 'application/json')

        response = self.get_response(request)

        # Set content-type based on accept header
        if 'application/xml' in accept_header:
            response['Content-Type'] = 'application/xml'
        elif 'text/csv' in accept_header:
            response['Content-Type'] = 'text/csv'
        else:
            response['Content-Type'] = 'application/json'

        return response

def get_format_from_request(request):
    '''Get preferred format from Accept header'''
    accept = request.META.get('HTTP_ACCEPT', 'application/json')

    if 'application/xml' in accept:
        return 'xml'
    elif 'text/csv' in accept:
        return 'csv'
    elif 'text/html' in accept:
        return 'html'
    else:
        return 'json'
"""

    def generate_fastapi_format_negotiation(self) -> str:
        """Generate FastAPI format negotiation"""
        return """
from fastapi import Header, Response
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
import json
import csv
from io import StringIO

async def get_format_from_accept(accept: Optional[str] = Header(None)):
    '''Get preferred format from Accept header'''
    if not accept:
        return 'json'

    if 'application/xml' in accept:
        return 'xml'
    elif 'text/csv' in accept:
        return 'csv'
    elif 'text/html' in accept:
        return 'html'
    else:
        return 'json'

class FormatNegotiator:
    @staticmethod
    def to_json(data: dict) -> str:
        '''Convert to JSON'''
        return json.dumps(data)

    @staticmethod
    def to_xml(data: dict) -> str:
        '''Convert to XML'''
        xml = '<?xml version="1.0"?>\\n<root>\\n'
        for key, value in data.items():
            xml += f'  <{key}>{value}</{key}>\\n'
        xml += '</root>'
        return xml

    @staticmethod
    def to_csv(data: list) -> str:
        '''Convert to CSV'''
        if not data:
            return ''

        output = StringIO()
        if isinstance(data, dict):
            data = [data]

        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

        return output.getvalue()

async def negotiate_response(
    data: dict,
    accept: Optional[str] = Header(None)
):
    '''Negotiate response format'''
    format_type = 'json'

    if accept:
        if 'application/xml' in accept:
            format_type = 'xml'
        elif 'text/csv' in accept:
            format_type = 'csv'

    if format_type == 'xml':
        return Response(
            content=FormatNegotiator.to_xml(data),
            media_type='application/xml'
        )
    elif format_type == 'csv':
        return Response(
            content=FormatNegotiator.to_csv([data]),
            media_type='text/csv'
        )
    else:
        return JSONResponse(content=data)
"""


def generate_format_negotiation(framework: str) -> Dict[str, str]:
    """
    Generate format negotiation code.

    Args:
        framework: django or fastapi

    Returns: dict of {filename: code_content}
    """
    generator = FormatNegotiationGenerator(framework)
    output = {}

    if framework == "django":
        output["format_negotiation.py"] = generator.generate_django_format_negotiation()
    elif framework == "fastapi":
        output["format_negotiation.py"] = generator.generate_fastapi_format_negotiation()

    return output
