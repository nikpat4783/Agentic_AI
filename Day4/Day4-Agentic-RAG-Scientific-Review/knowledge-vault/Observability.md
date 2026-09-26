#observability

# Observability

OpenTelemetry (traces, logs, metrics) → an OTel Collector → Prometheus /
Loki / Tempo, all viewed through Grafana. Stack defined in
`observability/docker-compose.yml`, brought up with
`docker compose up -d` from that directory (or the `start_observability_stack`
MCP tool on `app-dev-orchestrator`).

## Topology

```
backend (uvicorn :8001) --OTLP gRPC:4317--> otel-collector --+--> tempo:4317 (traces)
                                                               +--> loki:3100/otlp (logs)
                                                               +--> :8889/metrics <-- scraped by prometheus:9090
grafana:3000 --queries--> prometheus, loki, tempo (all pre-provisioned datasources)
```

## Ports

| Service | Port |
|---|---|
| Grafana | 3000 |
| Prometheus | 9090 |
| Loki | 3100 |
| Tempo (query API) | 3200 |
| OTel Collector (OTLP grpc / http) | 4317 / 4318 |

## Backend instrumentation

`backend/app/observability.py` (`setup_observability(app)`, called once
from `main.py`) sets up:
- Traces: `FastAPIInstrumentor` (every route) + `HTTPXClientInstrumentor`
  (every outbound call — Groq, PubMed, arXiv — with zero changes to
  the client code, see [[Agent-Orchestrator]]), plus manual spans around
  each tool-dispatch iteration.
- Logs: an OTel `LoggingHandler` added to the root logger *alongside* the
  existing `RedactSensitiveFilter`-based handlers (see [[Backend]]) —
  redaction still applies, and log records now carry `trace_id`/`span_id`
  for Grafana's log↔trace correlation (Loki → Tempo derived field).
- Metrics: two hand-defined instruments so dashboard queries don't depend
  on auto-instrumentation's metric-naming across versions —
  `app_http_requests_total` (counter) and `app_http_request_duration_seconds`
  (histogram), both labeled `route`/`method`/`status_code`; plus
  `app_agent_loop_iterations` (histogram, one observation per completed
  `/research/stream` request).

Config: `OTEL_EXPORTER_OTLP_ENDPOINT` (default `http://localhost:4317`),
`OTEL_SERVICE_NAME` (default `agentic-rag-backend`) — see `backend/.env.example`.

## Dashboards (provisioned automatically)

- **Agentic RAG - App Overview** (`/d/app-overview`) — request rate,
  5xx rate, and p95 latency by route, agent tool-loop iteration count, and
  a live trace list.
- **k6 Load Test** (`/d/k6-load-test`) — see [[Load-Testing]].

## Using it during a demo

Explore → Tempo → search by `service.name = agentic-rag-backend` to pull up
the trace for one specific request; click through to its correlated Loki
logs. See [[Demo]] for the exact click-through.
