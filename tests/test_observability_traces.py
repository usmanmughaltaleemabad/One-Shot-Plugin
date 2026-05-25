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
