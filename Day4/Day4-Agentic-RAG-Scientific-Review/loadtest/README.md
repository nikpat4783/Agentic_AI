# Load testing (k6 → Grafana)

Two scenarios, both driving the real backend at `http://localhost:8001`.
Metrics are pushed live into the same Prometheus/Grafana stack from
`../observability/`, visualized on the **"k6 Load Test"** dashboard at
<http://localhost:3000/d/k6-load-test>.

## Setup (one-time)

```bash
./install-k6.sh          # downloads a local k6 binary into ./bin/k6
```

The observability stack must be running (`docker compose up -d` in
`../observability/`) so Prometheus is there to receive metrics, and the
backend must be running on :8001 (`make dev` from the repo root, or the
`start_dev_servers` MCP tool).

## 1. Smoke test (safe, no cost)

Registers a throwaway user, logs in, then hits `GET /domains` at increasing
concurrency. No calls to Groq/PubMed/arXiv — safe to run any time.

```bash
./run-smoke.sh
./run-smoke.sh --vus 50 --duration 1m   # override load shape
```

## 2. Agentic RAG scenario (opt-in, COSTS MONEY)

Drives the full `POST /research/stream` flow, which makes a real, billed
Groq call (plus PubMed/arXiv calls) per iteration. Refuses to run
without an explicit key, and defaults to a low VU/iteration count:

```bash
GROQ_API_KEY=gsk_... ./run-agentic-rag.sh
GROQ_API_KEY=gsk_... VUS=3 ITERATIONS=6 MODEL=openai/gpt-oss-120b ./run-agentic-rag.sh
```

Env vars: `GROQ_API_KEY` (required), `VUS` (default 1),
`ITERATIONS` (default 3), `MODEL` (default `openai/gpt-oss-120b`),
`DOMAIN_ID` (default `healthcare`, must be a valid id from
`backend/app/domains/config.py`).

## Reading the dashboard

Each run is tagged `testid=<scenario>-<unix-timestamp>`; use the `testid`
dropdown at the top of the dashboard to isolate one run, or leave it on
"All" to compare runs over time. Panels: virtual users, request rate,
request duration (p95/p99/avg), failed-request rate.

The same time window also shows up on the **"Agentic RAG - App Overview"**
dashboard (request rate/latency/error-rate by route, plus a live trace list)
if you want to correlate load-test traffic with backend-side traces —
useful for seeing exactly which Groq/PubMed/arXiv call was the
bottleneck during a run.
