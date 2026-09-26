"""OpenTelemetry wiring: traces, logs, and metrics exported over OTLP/gRPC to
the local collector (see `Settings.otel_exporter_otlp_endpoint` /
`Settings.otel_service_name` in `app.config`).

The three metric instruments (`app_http_requests_total`,
`app_http_request_duration_seconds`, `app_agent_loop_iterations`) and the
module-level tracer/meter are created at *import* time against OpenTelemetry's
global proxy providers. Per the SDK's documented pattern, a proxy
tracer/meter/instrument created before a real provider is installed starts out
as a no-op and automatically begins delegating to the real backend the moment
`setup_observability()` calls `trace.set_tracer_provider(...)` /
`metrics.set_meter_provider(...)`. That means other modules (e.g.
`app.agent.orchestrator`) can `import app.observability` and use these
instruments/tracer immediately, with no ordering dependency on whether
`setup_observability()` has run yet.
"""

import logging
import time

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.logging.handler import LoggingHandler
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import settings

tracer = trace.get_tracer(__name__)
_meter = metrics.get_meter(__name__)

# Names are load-bearing: a Grafana dashboard already queries
# app_http_requests_total / app_http_request_duration_seconds. Do not rename.
http_requests_total = _meter.create_counter(
    "app_http_requests_total",
    description="Total number of HTTP requests handled by the backend.",
)
http_request_duration_seconds = _meter.create_histogram(
    "app_http_request_duration_seconds",
    unit="s",
    description="HTTP request duration in seconds.",
)
agent_loop_iterations = _meter.create_histogram(
    "app_agent_loop_iterations",
    description="Number of agent tool-call iterations completed per /research/stream request.",
)


class _MetricsMiddleware:
    """Plain ASGI middleware (deliberately not Starlette's BaseHTTPMiddleware,
    which buffers/re-wraps the response and would otherwise measure only
    time-to-first-byte for the SSE stream from /research/stream instead of
    full request duration)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.perf_counter() - start
            route = scope.get("route")
            # Templated path (e.g. "/research/stream") for low-cardinality
            # labeling; falls back to the raw path for unmatched (404) routes.
            route_path = route.path if route is not None else scope.get("path", "unknown")
            attributes = {
                "route": route_path,
                "method": scope.get("method", ""),
                "status_code": status_code,
            }
            http_requests_total.add(1, attributes)
            http_request_duration_seconds.record(duration, attributes)


def setup_observability(app: FastAPI) -> None:
    """Wire up OTel traces/logs/metrics export to the collector and instrument
    the FastAPI app + outbound httpx calls. Call exactly once, right after the
    FastAPI `app` is constructed, before the app serves traffic."""
    endpoint = settings.otel_exporter_otlp_endpoint
    resource = Resource.create({"service.name": settings.otel_service_name})

    # --- Traces ---
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
    )
    trace.set_tracer_provider(tracer_provider)

    # --- Logs ---
    # Layered on top of the handlers `configure_logging()` already attached to
    # the root logger (which carry the RedactSensitiveFilter) -- this adds an
    # OTLP-exporting handler, it does not remove or replace the existing ones.
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=endpoint, insecure=True))
    )
    set_logger_provider(logger_provider)
    otel_log_handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    logging.getLogger().addHandler(otel_log_handler)
    # Injects trace_id/span_id into stdlib LogRecords so exported/console logs
    # correlate with the active trace.
    LoggingInstrumentor().instrument(set_logging_format=True)

    # --- Metrics ---
    metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint, insecure=True))
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # --- Auto-instrumentation ---
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()  # traces every outbound call: Groq, PubMed, arXiv

    app.add_middleware(_MetricsMiddleware)
