# Carta Healthcare — Automated Clinical Data Extraction (POC)

A proof-of-concept implementation of [Case Study 3](../03-carta-healthcare.md):
automates extraction of structured clinical data elements from source
documents, routes only low-confidence extractions to a human abstractor, and
builds a submission-ready structured record — demonstrating the **66% faster
/ 99% accuracy** claim end to end.

See [SPEC.md](SPEC.md) for the full functional/non-functional spec this app
is built and reviewed against.

## Architecture

- **Backend** (`backend/`) — FastAPI. A pluggable extractor registry (rule-based
  regex extractors for well-formatted fields, an LLM-backed extractor — BYOK,
  no stored key — for narrative fields), a RAG index (Chroma +
  sentence-transformers) over registry data-element specs used to ground every
  confidence decision, confidence-based routing to a QA queue, and a
  submission builder. OpenTelemetry-instrumented.
- **Frontend** (`frontend/`) — React + Vite. Upload a document, see extracted
  fields color-coded by confidence with the RAG-grounded rationale, correct
  queued fields, build a submission record.
- **`mcp-server/`** — a custom MCP server (`app-dev-orchestrator`) exposing
  reusable dev/ops tools (start/stop dev servers, run tests, run load tests,
  manage the observability stack, add a data-element spec without touching
  code). `.mcp.json` also wires up the official `fetch` MCP server.
- **`observability/`** — a self-contained OpenTelemetry + Prometheus + Loki +
  Tempo + Grafana stack (own ports, see below — a similar stack from a sibling
  project may already be running on the default ports).
- **`loadtest/`** — k6 scenarios (vendored binary, no system k6 required).
- **`knowledge-vault/`** — an Obsidian-compatible knowledge base of this app.
- **`.claude/`** — project subagents (`backend`, `frontend`, `p3-triage`), a
  `dev-workflow` skill, and hooks — see [CLAUDE.md](CLAUDE.md).

## Running locally

```bash
make install                                  # backend venv + frontend node_modules
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
make dev                                      # backend :8002, frontend :5174
```

Open http://localhost:5174 and log in with the demo account
(`admin` / `admin1234`, overridable via `ADMIN_USERNAME`/`ADMIN_PASSWORD`
in `backend/.env`). Pick a domain (document type), then paste your own
Groq API key (BYOK — used only for that extraction call, never stored;
default model `openai/gpt-oss-120b`) to see the LLM-backed fields resolve
instead of queuing for QA.

## Where things run

| Thing | URL |
|---|---|
| Frontend | http://localhost:5174 |
| Backend API (docs) | http://localhost:8002/docs |
| Grafana | http://localhost:3010 |
| Prometheus | http://localhost:9091 |

## Tests, load testing, observability

- `make test` — backend pytest suite.
- `docker compose -f observability/docker-compose.yml up -d` — starts the
  local telemetry stack (see [observability/README.md](observability/README.md)
  for the port map and why it differs from the stack's usual defaults).
- `loadtest/install-k6.sh && loadtest/run-smoke.sh` — safe smoke load test,
  visualized on the `k6-load-test` Grafana dashboard.

## Knowledge vault & graph

- `knowledge-vault/` — open as an Obsidian vault (File → Open folder as
  vault), or just read the Markdown directly. Start at `Home.md`.
- `graphify-out/` — a generated knowledge graph of this codebase (run
  `/graphify case-study-3` from Claude Code to regenerate after major changes).

## Reports

`reports/` holds dated test/code-review output — see the latest file there
for the current pass/fail state of the test suite and review findings.
