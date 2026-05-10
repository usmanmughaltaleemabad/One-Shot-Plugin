"""
Logging Handler - Structured logging for APIs

Generates:
- Structured logging configuration
- Request/response logging
- Performance logging
- Error logging with context
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class LogConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "json"  # json, text
    include_request_body: bool = True
    include_response_body: bool = True
    exclude_paths: List[str] = None

    def __post_init__(self):
        if self.exclude_paths is None:
            self.exclude_paths = ['/health', '/metrics']


class LoggingHandler:
    """Generate logging configuration"""

    def __init__(self, framework: str):
        self.framework = framework

    def generate_django_logging(self) -> str:
        """Generate Django logging configuration"""
        return """
import logging
import json
import time
from django.utils.deprecation import MiddlewareNotUsed
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logger = logging.getLogger(__name__)

class JSONFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(JSONFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = record.created
        log_record['level'] = record.levelname
        log_record['logger'] = record.name

# Django logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': JSONFormatter,
            'fmt': '%(timestamp)s %(level)s %(name)s %(message)s'
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
            'level': 'INFO',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/api.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
            'level': 'INFO',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'api': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

class RequestLoggingMiddleware:
    '''Log all API requests and responses'''

    EXCLUDE_PATHS = {'/health', '/metrics', '/static', '/media'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in self.EXCLUDE_PATHS:
            return self.get_response(request)

        # Log request
        start_time = time.time()
        logger.info(f'Request: {request.method} {request.path}', extra={
            'method': request.method,
            'path': request.path,
            'query_string': request.META.get('QUERY_STRING', ''),
            'client_ip': self.get_client_ip(request),
        })

        response = self.get_response(request)

        # Log response
        duration = time.time() - start_time
        logger.info(f'Response: {request.method} {request.path} {response.status_code}', extra={
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration_ms': duration * 1000,
        })

        return response

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

def log_performance(view_func):
    '''Decorator to log performance metrics'''
    def wrapper(*args, **kwargs):
        start = time.time()
        result = view_func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f'Performance: {view_func.__name__} took {duration:.2f}s')
        return result
    return wrapper

def log_error(exc, context=''):
    '''Log error with context'''
    logger.error(f'Error: {str(exc)}', extra={
        'error': str(exc),
        'type': type(exc).__name__,
        'context': context,
    }, exc_info=True)
"""

    def generate_fastapi_logging(self) -> str:
        """Generate FastAPI logging configuration"""
        return """
import logging
import time
import json
from fastapi import Request
from pythonjsonlogger import jsonlogger

logger = logging.getLogger(__name__)

# Configure JSON logging
class JSONFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = record.created
        log_record['level'] = record.levelname

# Setup logging handlers
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter('%(timestamp)s %(level)s %(name)s %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

async def logging_middleware(request: Request, call_next):
    '''Log all requests and responses'''
    start_time = time.time()

    # Log request
    logger.info(f'Request: {request.method} {request.url.path}', extra={
        'method': request.method,
        'path': request.url.path,
        'client_ip': request.client.host if request.client else 'unknown',
    })

    response = await call_next(request)

    # Log response
    duration = time.time() - start_time
    logger.info(f'Response: {request.method} {request.url.path} {response.status_code}', extra={
        'method': request.method,
        'path': request.url.path,
        'status_code': response.status_code,
        'duration_ms': duration * 1000,
    })

    return response

import functools

def log_performance(func):
    '''Decorator to log performance metrics'''
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f'Performance: {func.__name__} took {duration:.2f}s')
        return result

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f'Performance: {func.__name__} took {duration:.2f}s')
        return result

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

def log_error(exc: Exception, context: str = ''):
    '''Log error with context'''
    logger.error(f'Error: {str(exc)}', extra={
        'error': str(exc),
        'type': type(exc).__name__,
        'context': context,
    }, exc_info=True)

class LogContext:
    '''Context manager for logging scopes'''
    def __init__(self, name: str, **extra):
        self.name = name
        self.extra = extra

    def __enter__(self):
        logger.debug(f'Entering {self.name}', extra=self.extra)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f'Error in {self.name}: {exc_val}', extra=self.extra, exc_info=True)
        else:
            logger.debug(f'Exiting {self.name}', extra=self.extra)
"""


def generate_logging(framework: str) -> Dict[str, str]:
    """
    Generate logging configuration.

    Args:
        framework: django or fastapi

    Returns: dict of {filename: code_content}
    """
    handler = LoggingHandler(framework)
    output = {}

    if framework == "django":
        output["logging.py"] = handler.generate_django_logging()
    elif framework == "fastapi":
        output["logging.py"] = handler.generate_fastapi_logging()

    return output
