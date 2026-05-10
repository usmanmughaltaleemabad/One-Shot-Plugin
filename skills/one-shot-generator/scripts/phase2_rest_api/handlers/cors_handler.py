"""
CORS Handler - Cross-Origin Resource Sharing configuration

Generates CORS configuration for:
- Allowed origins
- Allowed methods
- Allowed headers
- Exposed headers
- Credentials handling
- Max age configuration
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class CORSConfig:
    """CORS configuration"""
    allowed_origins: List[str] = None
    allowed_methods: List[str] = None
    allowed_headers: List[str] = None
    exposed_headers: List[str] = None
    allow_credentials: bool = True
    max_age: int = 3600

    def __post_init__(self):
        if self.allowed_origins is None:
            self.allowed_origins = ["http://localhost:3000", "http://localhost:8000"]
        if self.allowed_methods is None:
            self.allowed_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
        if self.allowed_headers is None:
            self.allowed_headers = ["*"]
        if self.exposed_headers is None:
            self.exposed_headers = ["X-Total-Count", "X-Page-Number"]


class CORSGenerator:
    """Generate CORS configuration"""

    def __init__(self, framework: str, config: CORSConfig):
        self.framework = framework
        self.config = config

    def generate_django(self) -> str:
        """Generate Django CORS configuration"""
        origins = ", ".join([f'"{o}"' for o in self.config.allowed_origins])
        methods = ", ".join([f'"{m}"' for m in self.config.allowed_methods])
        headers = ", ".join([f'"{h}"' for h in self.config.allowed_headers])
        exposed = ", ".join([f'"{h}"' for h in self.config.exposed_headers])

        return f"""
from django.http import HttpResponse
from django.utils.decorators import decorator_from_middleware
from django.utils.decorators import decorator_from_middleware_with_args

CORS_ALLOWED_ORIGINS = [
    {origins}
]

CORS_ALLOWED_METHODS = [
    {methods}
]

CORS_ALLOWED_HEADERS = [
    {headers}
]

CORS_EXPOSE_HEADERS = [
    {exposed}
]

CORS_ALLOW_CREDENTIALS = {str(self.config.allow_credentials).lower()}
CORS_MAX_AGE = {self.config.max_age}

class CORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        origin = request.headers.get('Origin')
        if origin in CORS_ALLOWED_ORIGINS or '*' in CORS_ALLOWED_ORIGINS:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Methods'] = ', '.join(CORS_ALLOWED_METHODS)
            response['Access-Control-Allow-Headers'] = ', '.join(CORS_ALLOWED_HEADERS)
            response['Access-Control-Expose-Headers'] = ', '.join(CORS_EXPOSE_HEADERS)
            response['Access-Control-Max-Age'] = str(CORS_MAX_AGE)

            if CORS_ALLOW_CREDENTIALS:
                response['Access-Control-Allow-Credentials'] = 'true'

        if request.method == 'OPTIONS':
            response.status_code = 200

        return response

def cors_allow_all(view_func):
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)

        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = ', '.join(CORS_ALLOWED_METHODS)
        response['Access-Control-Allow-Headers'] = ', '.join(CORS_ALLOWED_HEADERS)

        return response
    return wrapper

def cors_allow_origin(allowed_origins=None):
    if allowed_origins is None:
        allowed_origins = CORS_ALLOWED_ORIGINS

    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)

            origin = request.headers.get('Origin')
            if origin in allowed_origins or '*' in allowed_origins:
                response['Access-Control-Allow-Origin'] = origin
                response['Access-Control-Allow-Methods'] = ', '.join(CORS_ALLOWED_METHODS)
                response['Access-Control-Allow-Headers'] = ', '.join(CORS_ALLOWED_HEADERS)

            return response
        return wrapper
    return decorator
"""

    def generate_fastapi(self) -> str:
        """Generate FastAPI CORS configuration"""
        origins = [repr(o) for o in self.config.allowed_origins]
        methods = self.config.allowed_methods
        headers = self.config.allowed_headers

        return f"""
from fastapi.middleware.cors import CORSMiddleware

CORS_ALLOWED_ORIGINS = {origins}

CORS_ALLOWED_METHODS = {methods}

CORS_ALLOWED_HEADERS = {headers}

CORS_EXPOSE_HEADERS = {self.config.exposed_headers}

CORS_ALLOW_CREDENTIALS = {str(self.config.allow_credentials).lower()}

CORS_MAX_AGE = {self.config.max_age}

def setup_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ALLOWED_ORIGINS,
        allow_credentials=CORS_ALLOW_CREDENTIALS,
        allow_methods=CORS_ALLOWED_METHODS,
        allow_headers=CORS_ALLOWED_HEADERS,
        expose_headers=CORS_EXPOSE_HEADERS,
        max_age=CORS_MAX_AGE
    )

# Usage in main.py:
# from fastapi import FastAPI
# app = FastAPI()
# setup_cors(app)
"""


def generate_cors_config(
    framework: str,
    allowed_origins: Optional[List[str]] = None,
    allowed_methods: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Generate CORS configuration.

    Args:
        framework: django or fastapi
        allowed_origins: list of allowed origins
        allowed_methods: list of allowed HTTP methods

    Returns: dict of {filename: code_content}
    """
    config = CORSConfig(
        allowed_origins=allowed_origins,
        allowed_methods=allowed_methods
    )

    generator = CORSGenerator(framework, config)
    output = {}

    if framework == "django":
        output["cors.py"] = generator.generate_django()
    elif framework == "fastapi":
        output["cors.py"] = generator.generate_fastapi()

    return output
