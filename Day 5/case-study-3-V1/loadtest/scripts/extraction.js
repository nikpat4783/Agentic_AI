// Drives the real extraction flow: POST /documents then POST
// /documents/{id}/extract, for both sample doc types.
//
// Safe by default: if LLM_API_KEY is not set, the backend's LLM-backed
// fields resolve to extraction_method="llm_unavailable" (queued for QA)
// rather than making any external call -- so this scenario costs nothing
// unless you explicitly opt in with a real key.
//
// Usage:
//   ../bin/k6 run extraction.js
//   LLM_API_KEY=gsk_... VUS=2 ITERATIONS=5 ../bin/k6 run extraction.js
import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8002";
const LLM_API_KEY = __ENV.LLM_API_KEY || null;
const VUS = parseInt(__ENV.VUS || "1", 10);
const ITERATIONS = parseInt(__ENV.ITERATIONS || "3", 10);
const ADMIN_USERNAME = __ENV.ADMIN_USERNAME || "admin";
const ADMIN_PASSWORD = __ENV.ADMIN_PASSWORD || "admin1234";

const SAMPLE_DOCS = [
  {
    doc_type: "cath_report",
    content:
      "Cardiac catheterization performed. LVEF estimated at 35% by " +
      "ventriculography. Severe stenosis of the LAD noted. Troponin 0.04 ng/mL.",
  },
  {
    doc_type: "discharge_summary",
    content:
      "Patient admitted with chest pain, diagnosis I21.09. Discharged home " +
      "in stable condition on hospital day 3.",
  },
];

export const options = {
  scenarios: {
    extraction: {
      executor: "shared-iterations",
      vus: VUS,
      iterations: ITERATIONS,
      maxDuration: "5m",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.05"],
  },
};

export function setup() {
  // The documents/extract endpoints now require a login token (see
  // backend/app/auth.py). Log in once per test run, not per iteration.
  const loginRes = http.post(
    `${BASE_URL}/auth/login`,
    JSON.stringify({ username: ADMIN_USERNAME, password: ADMIN_PASSWORD }),
    { headers: { "Content-Type": "application/json" } }
  );
  check(loginRes, { "login succeeded": (r) => r.status === 200 });
  return { token: loginRes.json("token") };
}

export default function (data) {
  const doc = SAMPLE_DOCS[Math.floor(Math.random() * SAMPLE_DOCS.length)];
  const authHeaders = { "Content-Type": "application/json", Authorization: `Bearer ${data.token}` };

  const createRes = http.post(`${BASE_URL}/documents`, JSON.stringify(doc), { headers: authHeaders });
  check(createRes, { "document created": (r) => r.status === 200 || r.status === 201 });
  const documentId = createRes.json("document_id");

  const extractBody = { llm_api_key: LLM_API_KEY };
  const extractRes = http.post(
    `${BASE_URL}/documents/${documentId}/extract`,
    JSON.stringify(extractBody),
    { headers: authHeaders }
  );
  check(extractRes, { "extraction succeeded": (r) => r.status === 200 });

  sleep(1);
}
