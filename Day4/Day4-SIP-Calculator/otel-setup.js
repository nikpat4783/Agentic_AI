const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');
const { OTLPMetricExporter } = require('@opentelemetry/exporter-metrics-otlp-http');
const { PeriodicExportingMetricReader } = require('@opentelemetry/sdk-metrics');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const { ExpressInstrumentation } = require('@opentelemetry/instrumentation-express');
const { HttpInstrumentation } = require('@opentelemetry/instrumentation-http');
const { FsInstrumentation } = require('@opentelemetry/instrumentation-fs');

// Create a resource to identify the service
const resource = Resource.default().merge(
  new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'sip-calculator-api',
    [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
    environment: process.env.NODE_ENV || 'development',
  }),
);

// Configure the OTLP exporter endpoints
const otlpTraceExporter = new OTLPTraceExporter({
  url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4318/v1/traces',
  headers: {},
  concurrencyLimit: 10,
});

const otlpMetricExporter = new OTLPMetricExporter({
  url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4318/v1/metrics',
  headers: {},
  concurrencyLimit: 10,
});

// Create SDK with auto-instrumentation
const sdk = new NodeSDK({
  resource,
  traceExporter: otlpTraceExporter,
  metricReader: new PeriodicExportingMetricReader({
    exporter: otlpMetricExporter,
    intervalMillis: 10000, // Export metrics every 10 seconds
  }),
  instrumentations: [
    new ExpressInstrumentation({
      requestHook: (span, request) => {
        span.setAttribute('http.client_ip', request.ip);
      },
    }),
    new HttpInstrumentation({
      requestHook: (span, request) => {
        span.setAttribute('http.method', request.method);
      },
    }),
    new FsInstrumentation(),
  ],
});

// Initialize the SDK
sdk.start();

console.log('[OpenTelemetry] SDK initialized');
console.log(`[OpenTelemetry] Service: sip-calculator-api`);
console.log(`[OpenTelemetry] Exporting traces to: ${process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4318'}`);

// Graceful shutdown
process.on('SIGTERM', () => {
  sdk.shutdown()
    .then(() => console.log('[OpenTelemetry] SDK shut down successfully'))
    .catch((err) => console.error('[OpenTelemetry] Error shutting down SDK:', err))
    .finally(() => process.exit(0));
});
