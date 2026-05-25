"""Tests for OpenTelemetry trace initialization and context propagation."""

import pytest
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, 'scripts')


@patch('otel_tracer.JaegerExporter')
def test_tracer_initializes(mock_jaeger_exporter):
    """Verify init_tracer returns a tracer instance."""
    from otel_tracer import init_tracer

    service_name = "test-service"
    tracer = init_tracer(service_name)

    # Verify tracer is not None and has expected interface
    assert tracer is not None
    assert hasattr(tracer, 'start_as_current_span')


@patch('otel_tracer.JaegerExporter')
def test_span_created_and_exported(mock_jaeger_exporter):
    """Verify span can be created and attributes set."""
    from otel_tracer import init_tracer

    service_name = "test-span-service"
    tracer = init_tracer(service_name)

    # Create a span and verify it can be created
    with tracer.start_as_current_span("test-stage") as span:
        assert span is not None
        span.set_attribute("test_key", "test_value")
        assert span.get_span_context() is not None


@patch('otel_tracer.JaegerExporter')
def test_trace_stage_decorator_preserves_function_metadata(mock_jaeger_exporter):
    """Verify trace_stage decorator preserves decorated function metadata."""
    from otel_tracer import trace_stage

    @trace_stage("test-stage")
    def my_function(x, y):
        """Test function docstring."""
        return x + y

    # Verify functools.wraps preserves metadata
    assert my_function.__name__ == "my_function"
    assert my_function.__doc__ == "Test function docstring."


@patch('otel_tracer.JaegerExporter')
def test_trace_stage_decorator_handles_exceptions(mock_jaeger_exporter):
    """Verify trace_stage decorator handles exceptions and re-raises them."""
    from otel_tracer import trace_stage, init_tracer

    init_tracer("test-exception-service")

    @trace_stage("failing-stage")
    def failing_function():
        raise ValueError("Test error")

    # Verify exception is re-raised, not swallowed
    with pytest.raises(ValueError, match="Test error"):
        failing_function()


@patch('otel_tracer.JaegerExporter')
def test_span_attributes_set_correctly(mock_jaeger_exporter):
    """Verify span stage attribute and success status are recorded."""
    from otel_tracer import trace_stage, init_tracer

    init_tracer("test-attributes-service")

    @trace_stage("test-stage")
    def tracked_function():
        return "success"

    # Mock the span to verify attributes are set
    with patch('otel_tracer.trace.get_tracer') as mock_get_tracer:
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span
        mock_get_tracer.return_value = mock_tracer

        result = tracked_function()

        # Verify stage attribute is set
        calls = mock_span.set_attribute.call_args_list
        stage_set = any(call[0] == ("stage", "test-stage") for call in calls)
        assert stage_set, "Stage attribute not set on span"

        # Verify status is set to success
        status_set = any(call[0] == ("status", "success") for call in calls)
        assert status_set, "Success status not set on span"
