import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
import sys
from pathlib import Path

# Add scripts to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from otel_tracer import init_tracer, trace_stage

class TestTracerInitialization:
    def test_tracer_initializes(self):
        """Test that tracer initializes without error."""
        tracer = init_tracer("test-service")
        assert tracer is not None
    
    def test_span_created_and_exported(self):
        """Test that spans can be created and attributed."""
        tracer = init_tracer("test-service")
        with tracer.start_as_current_span("test-span") as span:
            span.set_attribute("test", "value")
            assert span is not None

class TestTraceDecorator:
    def test_trace_stage_decorator_wraps_function(self):
        """Test that @trace_stage decorator works."""
        @trace_stage("test-operation")
        def sample_function():
            return "result"
        
        result = sample_function()
        assert result == "result"
    
    def test_trace_stage_decorator_with_args(self):
        """Test that @trace_stage preserves function arguments."""
        @trace_stage("computation")
        def add(a, b):
            return a + b
        
        result = add(2, 3)
        assert result == 5
