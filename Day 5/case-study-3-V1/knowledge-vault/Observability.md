#observability

# Observability

OpenTelemetry SDK in the backend (`app/observability.py`) exports traces,
logs, and metrics via OTLP to a local collector, which fans them out to
Prometheus (metrics), Loki (logs), and Tempo (traces) — all visualized in
Grafana. Service name: `carta-extraction-backend`.

## Why this project's ports differ from the "usual" ones

A near-identical stack from a sibling project already runs on the default
ports (Grafana 3000, Prometheus 9090, Loki 3100, Tempo 3200, OTel collector
4317/4318) on this machine, and both projects' compose files live in a
directory literally named `observability` — which Docker Compose uses as
the default project name, so running this stack unmodified would collide on
both container names and ports. This project's
`observability/docker-compose.yml` sets an explicit `name:
case-study-3-observability` and remaps every host port (see
`observability/README.md` for the full table: Grafana **3010**, Prometheus
**9091**, Loki **3101**, Tempo **3201**, OTel collector **4327/4328**) so
both stacks can run side by side.

## Dashboards

- **"Carta Extraction - App Overview"** (`app-overview.json`) — request
  rate/p95 latency by route, and the two panels that matter most for this
  product's story: fields-by-resolution-status over time (straight-through
  vs. QA — the literal mechanism behind the 66%-faster claim) and the
  extraction-confidence distribution as a heatmap. Plus a live trace list
  scoped to this service.
- **"k6 Load Test"** — see [[Load-Testing]].

Custom metrics (`carta_http_requests_total`, `carta_http_request_duration_
seconds_bucket`, `carta_fields_total{status=...}`,
`carta_extraction_confidence_bucket`) are emitted by the backend's own
instrumentation code (not just FastAPI auto-instrumentation defaults) so the
dashboard's domain-specific panels have a stable metric name to query — see
[[Backend]] for where these are defined.

## Running it

```bash
cd observability && docker compose up -d
```
