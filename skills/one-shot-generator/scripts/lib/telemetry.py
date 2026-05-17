"""
OpenTelemetry integration — optional dependency, graceful no-op fallback.

The plugin's deterministic muscles (scanner, verifier, patcher, wirer,
critic_runner, agent_discovery, …) can emit OTLP spans to whatever
collector the user has running — Jaeger, Tempo, Honeycomb, Datadog,
or none at all. When ``opentelemetry-sdk`` isn't installed, every
function here becomes a no-op so the plugin still works fully.

Usage in a script:

    from lib.telemetry import span, current_traceparent

    with span("scan_codebase", attrs={"project": project_path}) as sp:
        ...  # work
        sp.set_attr("entities_found", len(entities))

The configuration is environment-driven:

  OSP_OTEL_ENABLED=1         turn it on  (default: off)
  OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318  collector
  OTEL_SERVICE_NAME=one-shot-prompting               service name

When ``OSP_OTEL_ENABLED`` is unset/0, the spans become free dataclasses
that still expose `.set_attr()` and a `.traceparent` (which is a
deterministic-but-fake W3C string) so call sites work either way.
"""

from __future__ import annotations

import contextlib
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Optional


# ─── Detection ───────────────────────────────────────────────────────────────

def _otel_enabled() -> bool:
    return os.getenv("OSP_OTEL_ENABLED", "").lower() in ("1", "true", "yes")


def _try_load_otel():
    """Return (tracer, propagator, status_codes) tuple or (None, None, None)."""
    if not _otel_enabled():
        return None, None, None
    try:
        from opentelemetry import trace
        from opentelemetry.propagate import inject as _inject
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor, ConsoleSpanExporter
        )
        from opentelemetry.trace import StatusCode
    except ImportError:
        return None, None, None

    # Initialise once per process
    if not hasattr(_try_load_otel, "_initialised"):
        provider = TracerProvider()
        # Default to ConsoleSpanExporter unless OTLP env is set
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter \
                    import OTLPSpanExporter
                provider.add_span_processor(
                    BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
                )
            except ImportError:
                provider.add_span_processor(
                    BatchSpanProcessor(ConsoleSpanExporter())
                )
        else:
            provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )
        trace.set_tracer_provider(provider)
        _try_load_otel._initialised = True

    service = os.getenv("OTEL_SERVICE_NAME", "one-shot-prompting")
    return trace.get_tracer(service), _inject, StatusCode


# ─── Public API ──────────────────────────────────────────────────────────────

@dataclass
class _NoOpSpan:
    """Stand-in span when otel isn't installed/enabled. Mirrors the
    subset of opentelemetry.trace.Span we actually use."""
    name: str
    started_at: float = field(default_factory=time.perf_counter)
    attributes: Dict[str, Any] = field(default_factory=dict)
    traceparent: str = field(
        default_factory=lambda: f"00-{uuid.uuid4().hex}-{uuid.uuid4().hex[:16]}-01"
    )

    def set_attr(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def set_status(self, code: str, description: str = "") -> None:
        self.attributes["__status"] = code
        if description:
            self.attributes["__status_description"] = description

    def record_exception(self, exc: BaseException) -> None:
        self.attributes["__exception"] = f"{type(exc).__name__}: {exc}"

    def duration_ms(self) -> float:
        return (time.perf_counter() - self.started_at) * 1000


@contextlib.contextmanager
def span(name: str, attrs: Optional[Dict[str, Any]] = None) -> Iterator[Any]:
    """Open a span. Use as a context manager:

        with span("scan_codebase", attrs={"project": path}) as sp:
            sp.set_attr("entities_found", n)
    """
    tracer, _, status_codes = _try_load_otel()
    if tracer is None:
        sp = _NoOpSpan(name=name, attributes=dict(attrs or {}))
        try:
            yield sp
        except Exception as exc:
            sp.record_exception(exc)
            raise
        return

    with tracer.start_as_current_span(name) as otel_sp:
        for k, v in (attrs or {}).items():
            otel_sp.set_attribute(k, v)

        # Adapter so callers can use the same .set_attr surface
        class _Adapter:
            def __init__(self, span_obj):
                self._span = span_obj
                self.traceparent = current_traceparent()

            def set_attr(self, key, value):
                self._span.set_attribute(key, value)

            def set_status(self, code, description=""):
                self._span.set_status(code, description)

            def record_exception(self, exc):
                self._span.record_exception(exc)

        adapter = _Adapter(otel_sp)
        try:
            yield adapter
        except Exception as exc:
            otel_sp.record_exception(exc)
            if status_codes is not None:
                otel_sp.set_status(status_codes.ERROR)
            raise


def current_traceparent() -> str:
    """W3C traceparent header for the current span (or a synthetic one
    if otel isn't enabled). Useful for passing through to subprocess /
    Task spawns so the spans link up."""
    tracer, _inject, _ = _try_load_otel()
    if tracer is None:
        return f"00-{uuid.uuid4().hex}-{uuid.uuid4().hex[:16]}-01"
    carrier: Dict[str, str] = {}
    if _inject is not None:
        _inject(carrier)
    return carrier.get("traceparent", "")


def is_enabled() -> bool:
    """True iff otel-sdk is installed AND OSP_OTEL_ENABLED is truthy."""
    tracer, _, _ = _try_load_otel()
    return tracer is not None


# ─── CLI (smoke) ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    print(f"OSP_OTEL_ENABLED = {_otel_enabled()}")
    print(f"is_enabled()     = {is_enabled()}")
    with span("smoke", attrs={"who": "telemetry-self-test"}) as sp:
        time.sleep(0.01)
        sp.set_attr("ok", True)
    print(f"smoke span duration: {sp.duration_ms() if isinstance(sp, _NoOpSpan) else 'n/a (otel)':}ms")
    print("traceparent:", current_traceparent())
