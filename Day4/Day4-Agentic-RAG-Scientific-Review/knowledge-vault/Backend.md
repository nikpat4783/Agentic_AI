#backend

# Backend

FastAPI app at `backend/app/main.py`, Python 3.14, deps in
`backend/requirements.txt`, venv at `backend/.venv`. Entrypoint:
`app.main:app`, served on **:8001** (`make dev-backend` /
`uvicorn app.main:app --reload --port 8001`).

## Routers (`backend/app/routers/`)

- `auth.py` — `POST /auth/register`, `POST /auth/login` → `{access_token}`,
  `GET /auth/me`. See [[Auth]].
- `domains.py` — `GET /domains`, lists `DOMAIN_REGISTRY`. See [[Domains]].
- `research.py` — `POST /research/stream`, the SSE endpoint that drives
  [[Agent-Orchestrator]]. Requires a JWT **and** a per-request
  `X-Groq-Key` header — the app is BYOK, no Groq key is ever
  stored server-side.

Plus `GET /health` defined directly in `main.py`.

## Lifespan

`main.py`'s `lifespan` context manager creates DB tables, warms the
embedding/reranker models used by [[RAG-Pipeline]], and starts a background
loop that purges idle Chroma collections (`_IDLE_TTL_SECONDS`, 2h).

## Logging

`logging.basicConfig` + `configure_logging()` (`backend/app/utils/logging.py`)
adds a `RedactSensitiveFilter` that scrubs anything that looks like an API
key/authorization header before it reaches any log sink — this runs
underneath the OTel logging handler added for [[Observability]], not instead
of it.

## Config

Pydantic-settings `Settings` class in `backend/app/config.py`, backed by
`backend/.env` (copy of `.env.example`). Notable vars: `JWT_SECRET_KEY`,
`DATABASE_URL`, `EMBEDDING_MODEL_NAME`, `CORS_ORIGINS`,
`OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME` (the last two added for
[[Observability]]).

## Tests

`backend/tests/` — plain pytest + pytest-asyncio, run via
`cd backend && .venv/bin/python -m pytest -q`. External clients (Groq,
PubMed, arXiv) are faked in tests rather than hit for real — see
`FakeGroqClient` in `test_agent_orchestrator.py`, reused for
[[Prompt-Engineering]] regression tests.
