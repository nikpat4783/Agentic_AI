// OPT-IN, COST-INCURRING load test: drives the real agentic RAG flow
// (POST /research/stream), which calls out to Groq (and PubMed/arXiv)
// for every single iteration. Each iteration is a real, billed LLM call.
//
// Refuses to run unless GROQ_API_KEY is set, and defaults to a very
// low VU/iteration count on purpose -- override deliberately if you want
// more load, understanding it costs more real money each time you do.
//
// Usage:
//   GROQ_API_KEY=gsk_... ../bin/k6 run scripts/agentic_rag.js
//   GROQ_API_KEY=gsk_... ../bin/k6 run --env VUS=3 --env ITERATIONS=6 scripts/agentic_rag.js
import http from "k6/http";
import { check, sleep, fail } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8001";
const GROQ_API_KEY = __ENV.GROQ_API_KEY || "";
const MODEL = __ENV.MODEL || "openai/gpt-oss-120b";
const DOMAIN_ID = __ENV.DOMAIN_ID || "healthcare";
const VUS = parseInt(__ENV.VUS || "1", 10);
const ITERATIONS = parseInt(__ENV.ITERATIONS || "3", 10);

const QUESTIONS = [
  "What are the reported adverse events for GLP-1 receptor agonists in recent literature?",
  "Summarize recent evidence on biomarkers for early sepsis detection.",
  "What does the literature say about supply chain resilience strategies for cold-chain vaccine logistics?",
];

export const options = {
  scenarios: {
    agentic_rag: {
      executor: "shared-iterations",
      vus: VUS,
      iterations: ITERATIONS,
      maxDuration: "10m",
    },
  },
};

export function setup() {
  if (!GROQ_API_KEY) {
    fail(
      "GROQ_API_KEY is not set. This scenario makes real, billed " +
        "Groq calls and refuses to run without an explicit key. " +
        "Set GROQ_API_KEY=gsk_... and re-run."
    );
  }

  const username = `loadtest_llm_${Date.now()}_${Math.floor(Math.random() * 1e6)}`;
  const password = "loadtest-password-123";

  http.post(
    `${BASE_URL}/auth/register`,
    JSON.stringify({ username, password }),
    { headers: { "Content-Type": "application/json" } }
  );

  const loginRes = http.post(
    `${BASE_URL}/auth/login`,
    JSON.stringify({ username, password }),
    { headers: { "Content-Type": "application/json" } }
  );
  check(loginRes, { "login succeeded": (r) => r.status === 200 });

  return { token: loginRes.json("access_token") };
}

export default function (data) {
  const question = QUESTIONS[Math.floor(Math.random() * QUESTIONS.length)];
  const res = http.post(
    `${BASE_URL}/research/stream`,
    JSON.stringify({
      domain_id: DOMAIN_ID,
      model: MODEL,
      question,
      session_id: `loadtest-${__VU}-${__ITER}`,
    }),
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${data.token}`,
        "X-Groq-Key": GROQ_API_KEY,
      },
      timeout: "120s",
    }
  );
  check(res, {
    "research/stream 200": (r) => r.status === 200,
    "got a final event": (r) => r.body && r.body.includes('"type": "final"'),
  });
  sleep(2);
}
