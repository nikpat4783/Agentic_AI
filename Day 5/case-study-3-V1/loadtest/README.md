# Load testing (k6 → Grafana)

Two scenarios, both driving the real backend at `http://localhost:8002`.
Metrics are pushed live into this project's own Prometheus/Grafana stack
from `../observability/`, visualized on the **"k6 Load Test"** dashboard at
<http://localhost:3010/d/k6-load-test>.

## Setup (one-time)

```bash
./install-k6.sh          # downloads a local k6 binary into ./bin/k6
```

The observability stack must be running (`docker compose up -d` in
`../observability/`) so Prometheus is there to receive metrics, and the
backend must be running on `:8002` (`make dev` from the repo root, or the
`start_dev_servers` MCP tool).

## 1. Smoke test (safe, no cost)

Hits `GET /health` and `GET /specs` at increasing concurrency. No document
ingestion, no LLM calls — safe to run any time.

```bash
./run-smoke.sh
```

## 2. Extraction scenario (safe by default, opt-in cost path)

Drives the real `POST /documents` → `POST /documents/{id}/extract` flow for
both sample doc types. **Safe/free by default**: without `LLM_API_KEY` set,
the backend's LLM-backed fields resolve to `"llm_unavailable"` (queued for
QA) rather than making an external call — this is the pipeline's designed
degrade-gracefully behavior, not a workaround.

```bash
./run-extraction.sh
LLM_API_KEY=gsk_... VUS=2 ITERATIONS=5 ./run-extraction.sh   # exercises the real LLM path
```

## Reading the dashboard

Each run is tagged `testid=<scenario>-<unix-timestamp>`; use the `testid`
dropdown at the top of the dashboard to isolate one run, or leave it on
"All" to compare runs over time. Panels: virtual users, request rate,
request duration (p95/p99/avg), failed-request rate.

The same time window also shows up on the **"Carta Extraction - App
Overview"** dashboard (request rate/latency by route, straight-through-vs-QA
rate, confidence distribution, live traces) if you want to correlate load
with backend-side behavior — e.g. whether load-test traffic shifted the
straight-through rate.
