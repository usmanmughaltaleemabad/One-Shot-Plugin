"""
Response Formatter - Response envelope and formatting

Generates:
- Consistent response envelopes
- Meta information (pagination, timestamps)
- Error response formatting
- Success response formatting
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ResponseEnvelope:
    """Standard response envelope"""
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict] = None
    meta: Optional[Dict] = None
    timestamp: Optional[str] = None

    def to_dict(self):
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'meta': self.meta,
            'timestamp': self.timestamp or datetime.utcnow().isoformat()
        }


class ResponseFormatter:
    """Format API responses"""

    def __init__(self, framework: str):
        self.framework = framework

    def generate_django_formatter(self) -> str:
        """Generate Django response formatter"""
        return """
from rest_framework.response import Response
from datetime import datetime
from typing import Dict, Any, Optional

class FormattedResponse:
    '''Format responses consistently'''

    @staticmethod
    def success(data: Any, status_code: int = 200, meta: Dict = None):
        '''Success response'''
        response = {
            'success': True,
            'data': data,
            'meta': meta or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        return Response(response, status=status_code)

    @staticmethod
    def error(message: str, code: str, status_code: int = 400, details: Dict = None):
        '''Error response'''
        response = {
            'success': False,
            'error': {
                'message': message,
                'code': code,
                'details': details or {}
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        return Response(response, status=status_code)

    @staticmethod
    def paginated(data: list, total: int, page: int, page_size: int):
        '''Paginated response'''
        total_pages = (total + page_size - 1) // page_size
        response = {
            'success': True,
            'data': data,
            'meta': {
                'pagination': {
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_previous': page > 1
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        return Response(response)

    @staticmethod
    def list_response(items: list, total: int = None, offset: int = 0, limit: int = 20):
        '''List response with metadata'''
        response = {
            'success': True,
            'data': items,
            'meta': {
                'count': len(items),
                'total': total or len(items),
                'offset': offset,
                'limit': limit,
                'has_more': (offset + limit) < (total or len(items))
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        return Response(response)

class ResponseFormatterMiddleware:
    '''Middleware to format all responses consistently'''

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only format API responses
        if request.path.startswith('/api/'):
            if response.status_code >= 400:
                # Error response - ensure proper format
                if not isinstance(response.data, dict) or 'error' not in response.data:
                    response.data = {
                        'success': False,
                        'error': {
                            'message': 'An error occurred',
                            'code': 'ERROR'
                        },
                        'timestamp': datetime.utcnow().isoformat()
                    }

        return response

def format_response_for_serializer(serializer):
    '''Format serializer output'''
    return {
        'success': True,
        'data': serializer.data,
        'timestamp': datetime.utcnow().isoformat()
    }
"""

    def generate_fastapi_formatter(self) -> str:
        """Generate FastAPI response formatter"""
        return """
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')

class Meta(BaseModel):
    '''Response metadata'''
    timestamp: str = None
    pagination: Optional[Dict] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

class SuccessResponse(BaseModel, Generic[T]):
    '''Success response envelope'''
    success: bool = True
    data: T
    meta: Optional[Meta] = None

class ErrorDetail(BaseModel):
    '''Error detail'''
    message: str
    code: str
    details: Optional[Dict] = None

class ErrorResponse(BaseModel):
    '''Error response envelope'''
    success: bool = False
    error: ErrorDetail
    timestamp: str = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

class PaginationMeta(BaseModel):
    '''Pagination metadata'''
    total: int
    count: int
    offset: int
    limit: int
    has_more: bool

class ResponseFormatter:
    '''Format responses'''

    @staticmethod
    def success(data: Any, meta: Dict = None) -> JSONResponse:
        '''Success response'''
        response = {
            'success': True,
            'data': data,
            'meta': meta or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        return JSONResponse(content=response, status_code=200)

    @staticmethod
    def error(message: str, code: str, status_code: int = 400, details: Dict = None) -> JSONResponse:
        '''Error response'''
        response = {
            'success': False,
            'error': {
                'message': message,
                'code': code,
                'details': details or {}
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        return JSONResponse(content=response, status_code=status_code)

    @staticmethod
    def paginated(
        data: list,
        total: int,
        offset: int = 0,
        limit: int = 20
    ) -> JSONResponse:
        '''Paginated response'''
        response = {
            'success': True,
            'data': data,
            'meta': {
                'pagination': {
                    'total': total,
                    'count': len(data),
                    'offset': offset,
                    'limit': limit,
                    'has_more': (offset + limit) < total
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        return JSONResponse(content=response)

    @staticmethod
    def list_response(
        items: list,
        total: int = None,
        offset: int = 0,
        limit: int = 20
    ) -> Dict:
        '''List response'''
        return {
            'success': True,
            'data': items,
            'meta': {
                'pagination': {
                    'total': total or len(items),
                    'count': len(items),
                    'offset': offset,
                    'limit': limit,
                    'has_more': (offset + limit) < (total or len(items))
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        }

class ResponseFormatterMiddleware:
    '''Middleware to format responses'''

    async def __call__(self, request, call_next):
        response = await call_next(request)

        # Add timestamp if not present
        if 'timestamp' not in response.headers:
            response.headers['X-Timestamp'] = datetime.utcnow().isoformat()

        return response
"""


def generate_response_formatter(framework: str) -> Dict[str, str]:
    """
    Generate response formatter code.

    Args:
        framework: django or fastapi

    Returns: dict of {filename: code_content}
    """
    formatter = ResponseFormatter(framework)
    output = {}

    if framework == "django":
        output["response_formatter.py"] = formatter.generate_django_formatter()
    elif framework == "fastapi":
        output["response_formatter.py"] = formatter.generate_fastapi_formatter()

    return output
