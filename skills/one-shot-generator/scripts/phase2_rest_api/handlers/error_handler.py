"""
Error Handler - Framework-specific error response generation

Generates error handling for:
- HTTP error responses
- Error serialization
- Error message formatting
- Error metadata
- Stack trace handling
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ErrorSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorResponse:
    """Standard error response"""
    status_code: int
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    path: Optional[str] = None
    severity: ErrorSeverity = ErrorSeverity.ERROR


class ErrorHandler:
    """Generate error handling code"""

    def __init__(self, framework: str):
        self.framework = framework

    def generate_django(self) -> str:
        """Generate Django error handling"""
        return """
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from django.http import JsonResponse
from django.views import View
from datetime import datetime
import traceback
import logging

logger = logging.getLogger(__name__)

class ErrorResponse:
    def __init__(self, status_code: int, error_code: str, message: str, details=None):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            'error': {
                'code': self.error_code,
                'message': self.message,
                'status': self.status_code,
                'details': self.details,
                'timestamp': self.timestamp
            }
        }

class APIErrorException(APIException):
    default_detail = 'An error occurred'
    default_code = 'error'

    def __init__(self, detail=None, code=None, status_code=400, error_code=None):
        self.status_code = status_code
        self.error_code = error_code or code or self.default_code
        super().__init__(detail, code)

class GlobalExceptionHandler:
    @staticmethod
    def handle_validation_error(exc):
        return Response(
            {
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Validation failed',
                    'details': exc.detail if hasattr(exc, 'detail') else str(exc),
                    'status': 400
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    @staticmethod
    def handle_not_found(exc):
        return Response(
            {
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Resource not found',
                    'status': 404
                }
            },
            status=status.HTTP_404_NOT_FOUND
        )

    @staticmethod
    def handle_permission_denied(exc):
        return Response(
            {
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': 'You do not have permission',
                    'status': 403
                }
            },
            status=status.HTTP_403_FORBIDDEN
        )

    @staticmethod
    def handle_authentication_failed(exc):
        return Response(
            {
                'error': {
                    'code': 'AUTHENTICATION_FAILED',
                    'message': 'Authentication failed',
                    'status': 401
                }
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    @staticmethod
    def handle_server_error(exc):
        logger.error(f'Server error: {str(exc)}', exc_info=True)
        return Response(
            {
                'error': {
                    'code': 'SERVER_ERROR',
                    'message': 'Internal server error',
                    'status': 500
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def error_response(status_code: int, error_code: str, message: str, details=None):
    return Response(
        {
            'error': {
                'code': error_code,
                'message': message,
                'status': status_code,
                'details': details or {}
            }
        },
        status=status_code
    )

def get_error_response(exception: Exception, status_code: int = 500):
    return error_response(
        status_code,
        exception.__class__.__name__,
        str(exception)
    )
"""

    def generate_fastapi(self) -> str:
        """Generate FastAPI error handling"""
        return """
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
import traceback
import logging

logger = logging.getLogger(__name__)

class ErrorDetail(BaseModel):
    code: str
    message: str
    status: int
    details: Optional[Dict[str, Any]] = None
    timestamp: str = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

class ErrorResponse(BaseModel):
    error: ErrorDetail

class HTTPException(Exception):
    def __init__(self, status_code: int, error_code: str, message: str, details: Optional[Dict] = None):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}

def error_response(status_code: int, error_code: str, message: str, details: Optional[Dict] = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            'error': {
                'code': error_code,
                'message': message,
                'status': status_code,
                'details': details or {},
                'timestamp': datetime.utcnow().isoformat()
            }
        }
    )

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return error_response(exc.status_code, exc.error_code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return error_response(
            400,
            'VALIDATION_ERROR',
            'Validation failed',
            {'errors': exc.errors()}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f'Unhandled exception: {str(exc)}', exc_info=True)
        return error_response(
            500,
            'SERVER_ERROR',
            'Internal server error'
        )

class ErrorHandler:
    @staticmethod
    def not_found(resource: str) -> JSONResponse:
        return error_response(404, 'NOT_FOUND', f'{resource} not found')

    @staticmethod
    def permission_denied(message: str = 'Permission denied') -> JSONResponse:
        return error_response(403, 'PERMISSION_DENIED', message)

    @staticmethod
    def authentication_failed(message: str = 'Authentication failed') -> JSONResponse:
        return error_response(401, 'AUTHENTICATION_FAILED', message)

    @staticmethod
    def validation_error(message: str, details: Dict = None) -> JSONResponse:
        return error_response(400, 'VALIDATION_ERROR', message, details)

    @staticmethod
    def server_error(message: str = 'Internal server error') -> JSONResponse:
        return error_response(500, 'SERVER_ERROR', message)

    @staticmethod
    def conflict(message: str = 'Resource conflict') -> JSONResponse:
        return error_response(409, 'CONFLICT', message)

    @staticmethod
    def rate_limit_exceeded() -> JSONResponse:
        return error_response(429, 'RATE_LIMIT_EXCEEDED', 'Too many requests')

    @staticmethod
    def bad_request(message: str, details: Dict = None) -> JSONResponse:
        return error_response(400, 'BAD_REQUEST', message, details)
"""


def generate_error_handlers(framework: str) -> Dict[str, str]:
    """
    Generate error handling code.

    Args:
        framework: django or fastapi

    Returns: dict of {filename: code_content}
    """
    generator = ErrorHandler(framework)
    output = {}

    if framework == "django":
        output["error_handler.py"] = generator.generate_django()
    elif framework == "fastapi":
        output["error_handler.py"] = generator.generate_fastapi()

    return output
