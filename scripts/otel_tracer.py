import functools
from typing import Callable, TypeVar, Any
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider, Tracer
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource


F = TypeVar('F', bound=Callable[..., Any])


def init_tracer(service_name: str) -> Tracer:
    """
    Initialize Jaeger exporter and tracer.

    Args:
        service_name: The name of the service for the tracer

    Returns:
        tracer: OpenTelemetry tracer instance

    Raises:
        RuntimeError: If Jaeger exporter cannot connect to Jaeger agent
    """
    try:
        jaeger_exporter = JaegerExporter(
            agent_host_name="localhost",
            agent_port=6831,
        )
    except Exception as e:
        raise RuntimeError(
            f"Failed to initialize Jaeger exporter for service '{service_name}': {e}"
        ) from e

    trace.set_tracer_provider(
        TracerProvider(resource=Resource.create({SERVICE_NAME: service_name}))
    )
    trace.get_tracer_provider().add_span_processor(
        SimpleSpanProcessor(jaeger_exporter)
    )
    return trace.get_tracer(__name__)


def trace_stage(stage_name: str) -> Callable[[F], F]:
    """
    Decorator factory to trace function execution.

    Args:
        stage_name: The name of the stage for the span

    Returns:
        decorator: A decorator function that wraps the target function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(stage_name) as span:
                span.set_attribute("stage", stage_name)
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("status", "error")
                    span.record_exception(e)
                    raise
        return wrapper  # type: ignore
    return decorator
