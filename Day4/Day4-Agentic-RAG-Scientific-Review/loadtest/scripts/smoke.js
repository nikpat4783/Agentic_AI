// Safe load test: registers a throwaway user, logs in, then hammers the
// non-LLM endpoints (GET /domains). No Groq calls -- costs nothing,
// safe to run any time to see how the app behaves under concurrent load.
//
// Usage:
//   ../bin/k6 run smoke.js
//   ../bin/k6 run --vus 20 --duration 30s smoke.js
//
// Visualize live in Grafana (http://localhost:3000) via the "k6 Load Test"
// dashboard -- this pushes metrics straight into the Prometheus container
// started by observability/docker-compose.yml using k6's built-in
// experimental-prometheus-rw output (no separate flag needed, see run-*.sh).
import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8001";

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

export function setup() {
  const username = `loadtest_${Date.now()}_${Math.floor(Math.random() * 1e6)}`;
  const password = "loadtest-password-123";

  const registerRes = http.post(
    `${BASE_URL}/auth/register`,
    JSON.stringify({ username, password }),
    { headers: { "Content-Type": "application/json" } }
  );
  check(registerRes, { "register succeeded": (r) => r.status === 200 || r.status === 201 });

  const loginRes = http.post(
    `${BASE_URL}/auth/login`,
    JSON.stringify({ username, password }),
    { headers: { "Content-Type": "application/json" } }
  );
  check(loginRes, { "login succeeded": (r) => r.status === 200 });
  const token = loginRes.json("access_token");

  return { token };
}

export default function (data) {
  const res = http.get(`${BASE_URL}/domains`, {
    headers: { Authorization: `Bearer ${data.token}` },
  });
  check(res, { "domains 200": (r) => r.status === 200 });
  sleep(1);
}
