"""OpenTelemetry setup: traces (FastAPI + httpx auto-instrumentation), logs,
and metrics, all exported via OTLP (gRPC) to this project's own collector on
localhost:4327 (a sibling project's stack already uses 4317, so this
project stays off it). Custom metric instruments live in app/metrics.py -
this module only wires up the providers/exporters.

If the collector isn't running, the OTel SDK's default batch-export
processors already tolerate export failures (they retry/drop in the
background) - nothing here turns an export failure into an app crash.
"""
from __future__ import annotations

import logging

from app.config import settings

logger = logging.getLogger(__name__)

_instrumented = False


def instrument_app(app) -> None:
    """Wire OTel into the FastAPI app. Safe to call once at app creation.

    Never raises: if the OTel SDK/exporter packages are missing or
    misconfigured, this logs a warning and the app continues without
    tracing rather than failing to start.
    """
    global _instrumented
    if not settings.otel_enabled or _instrumented:
        return

    try:
        from opentelemetry import _logs as logs_api
        from opentelemetry import metrics, trace
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.logging import LoggingInstrumentor
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({SERVICE_NAME: settings.otel_service_name})
        endpoint = settings.otel_exporter_endpoint

        # Traces
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
        )
        trace.set_tracer_provider(tracer_provider)

        # Metrics (feeds the custom carta_* instruments in app/metrics.py)
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=endpoint, insecure=True), export_interval_millis=5000
        )
        metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

        # Logs
        logger_provider = LoggerProvider(resource=resource)
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(OTLPLogExporter(endpoint=endpoint, insecure=True))
        )
        logs_api.set_logger_provider(logger_provider)
        logging.getLogger().addHandler(LoggingHandler(logger_provider=logger_provider))

        FastAPIInstrumentor().instrument_app(app)
        HTTPXClientInstrumentor().instrument()
        LoggingInstrumentor().instrument(set_logging_format=True)

        _instrumented = True
        logger.info(
            "OpenTelemetry instrumentation enabled (service=%s, endpoint=%s)",
            settings.otel_service_name,
            settings.otel_exporter_endpoint,
        )
    except Exception as exc:
        logger.warning("OpenTelemetry instrumentation disabled: %s", exc)
