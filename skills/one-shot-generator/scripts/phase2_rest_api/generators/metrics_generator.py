"""
Metrics Generator - Prometheus metrics for APIs

Generates:
- Prometheus metrics endpoints
- Request/response metrics
- Custom business metrics
- Grafana dashboard configs
"""

from typing import Dict, Any, List, Optional


class MetricsGenerator:
    """Generate metrics code"""

    def __init__(self, framework: str):
        self.framework = framework

    def generate_django_metrics(self) -> str:
        """Generate Django Prometheus metrics"""
        return """
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import REGISTRY, CollectorRegistry
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
import time

# Define metrics
REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'api_active_requests',
    'Number of active API requests',
    ['method', 'endpoint']
)

ERRORS = Counter(
    'api_errors_total',
    'Total API errors',
    ['method', 'endpoint', 'error_type']
)

class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        method = request.method
        path = request.path

        # Skip metrics endpoint
        if path == '/metrics':
            return self.get_response(request)

        ACTIVE_REQUESTS.labels(method=method, endpoint=path).inc()

        try:
            response = self.get_response(request)
            duration = time.time() - start_time

            # Record metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                status=response.status_code
            ).inc()

            REQUEST_DURATION.labels(
                method=method,
                endpoint=path
            ).observe(duration)

            return response
        except Exception as e:
            ERRORS.labels(
                method=method,
                endpoint=path,
                error_type=type(e).__name__
            ).inc()
            raise
        finally:
            ACTIVE_REQUESTS.labels(method=method, endpoint=path).dec()

@require_http_methods(['GET'])
def metrics_view(request):
    '''Prometheus metrics endpoint'''
    return HttpResponse(generate_latest(REGISTRY), content_type='text/plain')

# Custom business metrics
class BusinessMetrics:
    @staticmethod
    def record_user_signup():
        signup_counter = Counter(
            'user_signups_total',
            'Total user signups'
        )
        signup_counter.inc()

    @staticmethod
    def record_transaction(amount):
        transaction_gauge = Gauge(
            'transaction_amount_total',
            'Total transaction amount'
        )
        transaction_gauge.inc(amount)
"""

    def generate_fastapi_metrics(self) -> str:
        """Generate FastAPI Prometheus metrics"""
        return """
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response
from prometheus_client import REGISTRY
import time

# Define metrics
REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'api_active_requests',
    'Number of active API requests',
    ['method', 'endpoint']
)

ERRORS = Counter(
    'api_errors_total',
    'Total API errors',
    ['method', 'endpoint', 'error_type']
)

async def metrics_middleware(request, call_next):
    '''Middleware to track metrics'''
    start_time = time.time()
    method = request.method
    path = request.url.path

    # Skip metrics endpoint
    if path == '/metrics':
        return await call_next(request)

    ACTIVE_REQUESTS.labels(method=method, endpoint=path).inc()

    try:
        response = await call_next(request)
        duration = time.time() - start_time

        # Record metrics
        REQUEST_COUNT.labels(
            method=method,
            endpoint=path,
            status=response.status_code
        ).inc()

        REQUEST_DURATION.labels(
            method=method,
            endpoint=path
        ).observe(duration)

        return response
    except Exception as e:
        ERRORS.labels(
            method=method,
            endpoint=path,
            error_type=type(e).__name__
        ).inc()
        raise
    finally:
        ACTIVE_REQUESTS.labels(method=method, endpoint=path).dec()

async def metrics_endpoint():
    '''Prometheus metrics endpoint'''
    return Response(
        content=generate_latest(REGISTRY),
        media_type='text/plain'
    )

# Custom business metrics
class BusinessMetrics:
    signup_counter = Counter('user_signups_total', 'Total user signups')
    transaction_gauge = Gauge('transaction_amount_total', 'Total transaction amount')
    api_latency = Histogram('api_latency_seconds', 'API latency', ['endpoint'])

    @staticmethod
    def record_signup():
        BusinessMetrics.signup_counter.inc()

    @staticmethod
    def record_transaction(amount):
        BusinessMetrics.transaction_gauge.inc(amount)

    @staticmethod
    def record_latency(endpoint: str, duration: float):
        BusinessMetrics.api_latency.labels(endpoint=endpoint).observe(duration)
"""


def generate_metrics(framework: str) -> Dict[str, str]:
    """
    Generate metrics code.

    Args:
        framework: django or fastapi

    Returns: dict of {filename: code_content}
    """
    generator = MetricsGenerator(framework)
    output = {}

    if framework == "django":
        output["metrics.py"] = generator.generate_django_metrics()
    elif framework == "fastapi":
        output["metrics.py"] = generator.generate_fastapi_metrics()

    return output
