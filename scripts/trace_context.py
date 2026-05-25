from opentelemetry.trace import set_span_in_context
from opentelemetry import trace
import contextvars

# Pass context across Task boundaries
trace_context = contextvars.ContextVar('trace_context', default=None)

def capture_context():
    return trace.get_current_span().get_span_context()

def restore_context(ctx):
    return set_span_in_context(ctx)
