#load-testing

# Load Testing

k6, in `loadtest/` at the repo root. Metrics push straight into the same
Prometheus container from [[Observability]] via k6's built-in
`experimental-prometheus-rw` output — no separate InfluxDB/xk6 build
needed. Visualized on the **k6 Load Test** Grafana dashboard
(`/d/k6-load-test`), filterable by a `testid` variable so repeated runs
don't collide.

## Setup

```bash
cd loadtest && ./install-k6.sh   # local binary at loadtest/bin/k6, no sudo
```

## Scenarios

1. **`scripts/smoke.js`** (`./run-smoke.sh`) — safe, free. Registers a
   throwaway user, logs in, ramps `GET /domains` up to 10 concurrent VUs.
   Thresholds: <1% failed requests, p95 < 1s.
2. **`scripts/agentic_rag.js`** (`GROQ_API_KEY=... ./run-agentic-rag.sh`)
   — opt-in, **costs real money**: drives the full `POST /research/stream`
   flow (real Groq + PubMed/arXiv calls per iteration). Refuses to
   run without `GROQ_API_KEY`; defaults to 1 VU / 3 iterations on
   purpose. See [[Auth]] for why login has to happen first.

## Dashboard metrics (k6's real Prometheus metric names — verified live,
not assumed)

`k6_vus`, `k6_http_reqs_total`, `k6_http_req_duration_p95` /
`_p99` / `_avg` (via `K6_PROMETHEUS_RW_TREND_STATS=p(95),p(99),avg`, set by
the `run-*.sh` wrappers), `k6_http_req_failed_rate`.

## Reading results alongside app traces

Because load-test traffic and app instrumentation share the same Grafana,
a slow p95 on the k6 dashboard can be cross-referenced against the
**Agentic RAG - App Overview** dashboard's per-route latency panel and
Tempo trace list from the same time window — see [[Observability]].
