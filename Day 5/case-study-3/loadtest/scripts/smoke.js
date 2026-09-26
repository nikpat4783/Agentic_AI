// Safe load test: hits /health and /specs at increasing concurrency. No
// document ingestion, no extraction, no LLM calls -- costs nothing, safe to
// run any time to see how the app behaves under concurrent read load.
//
// Usage:
//   ../bin/k6 run smoke.js
//   ../bin/k6 run --vus 20 --duration 30s smoke.js
//
// Visualize live in Grafana (http://localhost:3010) via the "k6 Load Test"
// dashboard -- this pushes metrics straight into this project's own
// Prometheus container using k6's built-in experimental-prometheus-rw
// output (see run-smoke.sh for the exact flags).
import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8002";

export const options = {
  scenarios: {
    smoke: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "10s", target: 10 },
        { duration: "30s", target: 10 },
        { duration: "10s", target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<1000"],
  },
};

export default function () {
  const health = http.get(`${BASE_URL}/health`);
  check(health, { "health 200": (r) => r.status === 200 });

  const specs = http.get(`${BASE_URL}/specs`);
  check(specs, { "specs 200": (r) => r.status === 200 });

  sleep(1);
}
