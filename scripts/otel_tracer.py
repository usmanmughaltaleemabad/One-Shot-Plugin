import json
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource


def init_tracer(service_name: str):
    """
    Initialize Jaeger exporter and tracer.

    Args:
        service_name: The name of the service for the tracer

    Returns:
        tracer: OpenTelemetry tracer instance
    """
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )
    trace.set_tracer_provider(
        TracerProvider(resource=Resource.create({SERVICE_NAME: service_name}))
    )
    trace.get_tracer_provider().add_span_processor(
        SimpleSpanProcessor(jaeger_exporter)
    )
    return trace.get_tracer(__name__)


def trace_stage(stage_name: str):
    """
    Decorator factory to trace function execution.

    Args:
        stage_name: The name of the stage for the span

    Returns:
        decorator: A decorator function that wraps the target function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(stage_name) as span:
                span.set_attribute("stage", stage_name)
                result = func(*args, **kwargs)
                span.set_attribute("status", "success")
                return result
        return wrapper
    return decorator
