"""Custom OpenTelemetry metric instruments for this app's domain-specific
signals - the ones the Grafana "App Overview" dashboard queries by name.

FastAPI auto-instrumentation (see observability.py) covers generic HTTP
server spans, but doesn't emit Prometheus-friendly counters/histograms named
the way this project's dashboard expects, and doesn't know anything about
extraction confidence or straight-through-vs-QA routing at all - that's
domain-specific and has to be recorded explicitly at the call site.

Safe to import/call even if OTel isn't instrumented (see instrument_metrics
below): every recorder function falls back to a no-op meter.
"""
from __future__ import annotations

from opentelemetry import metrics

_meter = metrics.get_meter("carta.extraction.backend")

http_requests_counter = _meter.create_counter(
    name="carta_http_requests_total",
    description="Total HTTP requests, by route and status code.",
)
http_request_duration = _meter.create_histogram(
    name="carta_http_request_duration_seconds",
    description="HTTP request duration in seconds, by route.",
    unit="s",
)
fields_counter = _meter.create_counter(
    name="carta_fields_total",
    description="Extracted fields, by resolution status (straight_through/pending_qa).",
)
confidence_histogram = _meter.create_histogram(
    name="carta_extraction_confidence",
    description="Calibrated confidence score for each extracted field (0-1).",
)


def record_request(route: str, method: str, status_code: int, duration_seconds: float) -> None:
    attrs = {"route": route, "method": method, "status_code": str(status_code)}
    http_requests_counter.add(1, attrs)
    http_request_duration.record(duration_seconds, {"route": route, "method": method})


def record_field(status: str, element_name: str) -> None:
    fields_counter.add(1, {"status": status, "element_name": element_name})


def record_confidence(value: float, element_name: str) -> None:
    confidence_histogram.record(value, {"element_name": element_name})
