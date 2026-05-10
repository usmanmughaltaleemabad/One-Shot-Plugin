"""
Tracing Generator - Distributed tracing with OpenTelemetry

Generates:
- OpenTelemetry instrumentation
- Span creation and context
- Trace propagation
- Jaeger/Zipkin integration
"""

from typing import Dict, Any


class TracingGenerator:
    """Generate tracing code"""

    def __init__(self, framework: str):
        self.framework = framework

    def generate_otel_django(self) -> str:
        """Generate OpenTelemetry for Django"""
        return """
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# Initialize Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name='localhost',
    agent_port=6831,
)

# Set up tracing
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Instrument libraries
DjangoInstrumentor().instrument()
RequestsInstrumentor().instrument()
SQLAlchemyInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

class TracingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        with tracer.start_as_current_span(f'{request.method} {request.path}') as span:
            span.set_attribute('http.method', request.method)
            span.set_attribute('http.url', str(request.build_absolute_uri()))
            span.set_attribute('http.client_ip', self.get_client_ip(request))

            response = self.get_response(request)

            span.set_attribute('http.status_code', response.status_code)
            return response

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

def trace_function(func):
    '''Decorator to trace function execution'''
    def wrapper(*args, **kwargs):
        with tracer.start_as_current_span(func.__name__) as span:
            span.set_attribute('function', func.__name__)
            return func(*args, **kwargs)
    return wrapper
"""

    def generate_otel_fastapi(self) -> str:
        """Generate OpenTelemetry for FastAPI"""
        return """
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from fastapi import Request

# Initialize Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name='localhost',
    agent_port=6831,
)

# Set up tracing
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Instrument libraries
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()
SQLAlchemyInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

async def tracing_middleware(request: Request, call_next):
    '''Middleware to trace requests'''
    with tracer.start_as_current_span(f'{request.method} {request.url.path}') as span:
        span.set_attribute('http.method', request.method)
        span.set_attribute('http.url', str(request.url))
        span.set_attribute('http.client_ip', request.client.host)

        response = await call_next(request)

        span.set_attribute('http.status_code', response.status_code)
        return response

def trace_function(func):
    '''Decorator to trace function execution'''
    async def async_wrapper(*args, **kwargs):
        with tracer.start_as_current_span(func.__name__):
            return await func(*args, **kwargs)

    def sync_wrapper(*args, **kwargs):
        with tracer.start_as_current_span(func.__name__):
            return func(*args, **kwargs)

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
"""


def generate_tracing(framework: str) -> Dict[str, str]:
    """
    Generate tracing code.

    Args:
        framework: django or fastapi

    Returns: dict of {filename: code_content}
    """
    generator = TracingGenerator(framework)
    output = {}

    if framework == "django":
        output["tracing.py"] = generator.generate_otel_django()
    elif framework == "fastapi":
        output["tracing.py"] = generator.generate_otel_fastapi()

    return output
