"""
Security Headers Generator - HTTP security headers

Generates security headers for:
- Content Security Policy (CSP)
- X-Content-Type-Options
- X-Frame-Options
- Strict-Transport-Security
- X-XSS-Protection
- Referrer-Policy
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SecurityHeadersConfig:
    """Security headers configuration"""
    enable_csp: bool = True
    enable_hsts: bool = True
    enable_x_frame_options: bool = True
    enable_x_content_type_options: bool = True
    enable_x_xss_protection: bool = True
    enable_referrer_policy: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False
    csp_policy: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"


class SecurityHeadersGenerator:
    """Generate security headers code"""

    def __init__(self, framework: str, config: SecurityHeadersConfig):
        self.framework = framework
        self.config = config

    def generate_django(self) -> str:
        """Generate Django security headers middleware"""
        return f"""
from django.http import HttpResponse

SECURITY_HEADERS = {{}}

{f'SECURITY_HEADERS["Content-Security-Policy"] = "{self.config.csp_policy}"' if self.config.enable_csp else '# CSP disabled'}

{f'SECURITY_HEADERS["Strict-Transport-Security"] = "max-age={self.config.hsts_max_age}' + ('; includeSubDomains' if self.config.hsts_include_subdomains else '') + ('; preload' if self.config.hsts_preload else '') + '"' if self.config.enable_hsts else '# HSTS disabled'}

{f'SECURITY_HEADERS["X-Frame-Options"] = "DENY"' if self.config.enable_x_frame_options else '# X-Frame-Options disabled'}

{f'SECURITY_HEADERS["X-Content-Type-Options"] = "nosniff"' if self.config.enable_x_content_type_options else '# X-Content-Type-Options disabled'}

{f'SECURITY_HEADERS["X-XSS-Protection"] = "1; mode=block"' if self.config.enable_x_xss_protection else '# X-XSS-Protection disabled'}

{f'SECURITY_HEADERS["Referrer-Policy"] = "strict-origin-when-cross-origin"' if self.config.enable_referrer_policy else '# Referrer-Policy disabled'}

SECURITY_HEADERS["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add security headers to response
        for header, value in SECURITY_HEADERS.items():
            response[header] = value

        return response

def apply_security_headers(response):
    for header, value in SECURITY_HEADERS.items():
        response[header] = value
    return response

def security_headers_decorator(view_func):
    def wrapper(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        return apply_security_headers(response)
    return wrapper
"""

    def generate_fastapi(self) -> str:
        """Generate FastAPI security headers middleware"""
        return f"""
from fastapi import FastAPI
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

SECURITY_HEADERS = {{}}

{f'SECURITY_HEADERS["Content-Security-Policy"] = "{self.config.csp_policy}"' if self.config.enable_csp else '# CSP disabled'}

{f'SECURITY_HEADERS["Strict-Transport-Security"] = "max-age={self.config.hsts_max_age}' + ('; includeSubDomains' if self.config.hsts_include_subdomains else '') + ('; preload' if self.config.hsts_preload else '') + '"' if self.config.enable_hsts else '# HSTS disabled'}

{f'SECURITY_HEADERS["X-Frame-Options"] = "DENY"' if self.config.enable_x_frame_options else '# X-Frame-Options disabled'}

{f'SECURITY_HEADERS["X-Content-Type-Options"] = "nosniff"' if self.config.enable_x_content_type_options else '# X-Content-Type-Options disabled'}

{f'SECURITY_HEADERS["X-XSS-Protection"] = "1; mode=block"' if self.config.enable_x_xss_protection else '# X-XSS-Protection disabled'}

{f'SECURITY_HEADERS["Referrer-Policy"] = "strict-origin-when-cross-origin"' if self.config.enable_referrer_policy else '# Referrer-Policy disabled'}

SECURITY_HEADERS["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        return response

def setup_security_headers(app: FastAPI):
    app.add_middleware(SecurityHeadersMiddleware)

def apply_security_headers(response):
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response
"""


def generate_security_headers(
    framework: str,
    enable_csp: bool = True,
    enable_hsts: bool = True
) -> Dict[str, str]:
    """
    Generate security headers code.

    Args:
        framework: django or fastapi
        enable_csp: enable Content Security Policy
        enable_hsts: enable HTTP Strict Transport Security

    Returns: dict of {filename: code_content}
    """
    config = SecurityHeadersConfig(
        enable_csp=enable_csp,
        enable_hsts=enable_hsts
    )

    generator = SecurityHeadersGenerator(framework, config)
    output = {}

    if framework == "django":
        output["security_headers.py"] = generator.generate_django()
    elif framework == "fastapi":
        output["security_headers.py"] = generator.generate_fastapi()

    return output
