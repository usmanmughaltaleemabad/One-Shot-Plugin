from opentelemetry.trace import set_span_in_context, SpanContext
from opentelemetry import trace
import contextvars
from typing import Any

# Note: trace_context ContextVar reserved for future use in async span propagation
trace_context = contextvars.ContextVar('trace_context', default=None)


def capture_context() -> SpanContext:
    """
    Get current span context.

    Returns:
        SpanContext: The span context of the current span
    """
    return trace.get_current_span().get_span_context()


def restore_context(ctx: SpanContext) -> Any:
    """
    Set span in context.

    Args:
        ctx: The span context to restore

    Returns:
        Context: The new context with the span set
    """
    return set_span_in_context(ctx)
