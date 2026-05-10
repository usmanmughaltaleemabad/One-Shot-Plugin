"""
Exception Mapper - Map framework-specific exceptions to HTTP responses

Maps:
- Database exceptions to HTTP errors
- Validation exceptions to 422 responses
- Authentication exceptions to 401 responses
- Authorization exceptions to 403 responses
- Not found exceptions to 404 responses
"""

from typing import Dict, Any, Type, Callable, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ExceptionMapping:
    """Exception to HTTP response mapping"""
    exception_class: Type[Exception]
    status_code: int
    error_code: str
    message: str


class ExceptionMapper:
    """Map framework-specific exceptions"""

    def __init__(self, framework: str):
        self.framework = framework
        self.mappings: Dict[Type, ExceptionMapping] = {}

    def add_mapping(self, exception: Type, status_code: int, error_code: str, message: str):
        self.mappings[exception] = ExceptionMapping(exception, status_code, error_code, message)

    def get_mapping(self, exception: Exception) -> Optional[ExceptionMapping]:
        for exc_type, mapping in self.mappings.items():
            if isinstance(exception, exc_type):
                return mapping
        return None

    def generate_django(self) -> str:
        """Generate Django exception mapper"""
        return """
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.utils import IntegrityError, DatabaseError
from rest_framework.exceptions import APIException, NotFound, ValidationError as DRFValidationError

class ExceptionMapper:
    MAPPINGS = {
        ObjectDoesNotExist: (404, 'NOT_FOUND', 'Resource not found'),
        ValidationError: (422, 'VALIDATION_ERROR', 'Validation failed'),
        IntegrityError: (409, 'CONFLICT', 'Resource conflict'),
        DatabaseError: (500, 'DATABASE_ERROR', 'Database error'),
    }

    @staticmethod
    def map_exception(exc: Exception) -> Tuple[int, str, str]:
        for exc_type, (status_code, error_code, message) in ExceptionMapper.MAPPINGS.items():
            if isinstance(exc, exc_type):
                return status_code, error_code, message

        # Default mapping
        if isinstance(exc, APIException):
            return exc.status_code, exc.default_code, exc.detail
        return 500, 'SERVER_ERROR', 'Internal server error'

    @staticmethod
    def create_error_response(exc: Exception) -> Response:
        status_code, error_code, message = ExceptionMapper.map_exception(exc)
        return Response(
            {
                'error': {
                    'code': error_code,
                    'message': message,
                    'status': status_code
                }
            },
            status=status_code
        )

def map_django_exceptions(view_func):
    def wrapper(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
        except Exception as exc:
            return ExceptionMapper.create_error_response(exc)
    return wrapper

class DjangoExceptionHandler(APIException):
    def __init__(self, exc: Exception):
        status_code, error_code, message = ExceptionMapper.map_exception(exc)
        self.status_code = status_code
        self.detail = {
            'error': {
                'code': error_code,
                'message': message,
                'status': status_code
            }
        }
        super().__init__(self.detail)
"""

    def generate_fastapi(self) -> str:
        """Generate FastAPI exception mapper"""
        return """
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import ValidationError
from typing import Optional, Tuple, Type
from datetime import datetime

class ExceptionMapper:
    MAPPINGS = {
        ValueError: (400, 'BAD_REQUEST', 'Invalid value'),
        KeyError: (400, 'BAD_REQUEST', 'Missing required field'),
        ValidationError: (422, 'VALIDATION_ERROR', 'Validation failed'),
        IntegrityError: (409, 'CONFLICT', 'Resource conflict'),
        SQLAlchemyError: (500, 'DATABASE_ERROR', 'Database error'),
    }

    @staticmethod
    def map_exception(exc: Exception) -> Tuple[int, str, str]:
        for exc_type, (status_code, error_code, message) in ExceptionMapper.MAPPINGS.items():
            if isinstance(exc, exc_type):
                return status_code, error_code, message

        # Default mapping
        return 500, 'SERVER_ERROR', 'Internal server error'

    @staticmethod
    def create_error_response(exc: Exception, status_code: int = None) -> JSONResponse:
        if status_code is None:
            status_code, error_code, message = ExceptionMapper.map_exception(exc)
        else:
            _, error_code, message = ExceptionMapper.map_exception(exc)

        return JSONResponse(
            status_code=status_code,
            content={
                'error': {
                    'code': error_code,
                    'message': message,
                    'status': status_code,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
        )

def setup_exception_mappers(app: FastAPI):
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return ExceptionMapper.create_error_response(exc)

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return ExceptionMapper.create_error_response(exc, 400)

    @app.exception_handler(KeyError)
    async def key_error_handler(request: Request, exc: KeyError):
        return ExceptionMapper.create_error_response(exc, 400)

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return ExceptionMapper.create_error_response(exc, 422)

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        return ExceptionMapper.create_error_response(exc, 409)

    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(request: Request, exc: SQLAlchemyError):
        return ExceptionMapper.create_error_response(exc, 500)

class HTTPExceptionDetail:
    NOT_FOUND = (404, 'NOT_FOUND', 'Resource not found')
    UNAUTHORIZED = (401, 'UNAUTHORIZED', 'Unauthorized')
    FORBIDDEN = (403, 'FORBIDDEN', 'Forbidden')
    CONFLICT = (409, 'CONFLICT', 'Resource conflict')
    VALIDATION_ERROR = (422, 'VALIDATION_ERROR', 'Validation failed')
    SERVER_ERROR = (500, 'SERVER_ERROR', 'Internal server error')

    @staticmethod
    def create_response(detail: Tuple, message: str = None) -> JSONResponse:
        status_code, error_code, default_message = detail
        return JSONResponse(
            status_code=status_code,
            content={
                'error': {
                    'code': error_code,
                    'message': message or default_message,
                    'status': status_code,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
        )
"""


def generate_exception_mapper(framework: str) -> Dict[str, str]:
    """
    Generate exception mapper code.

    Args:
        framework: django or fastapi

    Returns: dict of {filename: code_content}
    """
    mapper = ExceptionMapper(framework)
    output = {}

    if framework == "django":
        output["exception_mapper.py"] = mapper.generate_django()
    elif framework == "fastapi":
        output["exception_mapper.py"] = mapper.generate_fastapi()

    return output
