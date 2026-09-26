#load-testing

# Load testing

k6, vendored as a local binary (`loadtest/install-k6.sh` downloads it into
`loadtest/bin/k6` — no system-wide k6 install exists on this machine, and
none is required). Metrics push live into this project's own Prometheus
(`:9091`) via k6's `experimental-prometheus-rw` output, visualized on the
**"k6 Load Test"** Grafana dashboard (`:3010/d/k6-load-test`).

## Scenarios

1. **`smoke`** (`scripts/smoke.js`, `./run-smoke.sh`) — `GET /health` +
   `GET /specs` at increasing concurrency. No document ingestion, no LLM
   calls. Safe to run any time.
2. **`extraction`** (`scripts/extraction.js`, `./run-extraction.sh`) — the
   real `POST /documents` → `POST .../extract` flow, for both sample doc
   types. **Safe/free by default** — unlike a typical "opt-in, costs money"
   load-test scenario, this one doesn't need a cost guard at all: without
   `LLM_API_KEY` set, the backend's own designed-to-never-fail behavior
   resolves LLM-backed fields to `"llm_unavailable"` rather than calling
   out. Set `LLM_API_KEY` (plus optionally `VUS`/`ITERATIONS`) to exercise
   the real LLM extraction path instead.

## Reading results

Each run is tagged `testid=<scenario>-<unix-timestamp>` — use the dashboard's
`testid` variable to isolate a run or compare across runs. Cross-reference
with the [[Observability|app-overview dashboard]]'s straight-through-vs-QA
panel to see whether load shifted the confidence-routing behavior, not just
raw latency.
