---
name: dev-workflow
description: Use for any question about how to run, test, or extend this repo — starting the backend and frontend dev servers, adding a new domain, adding a new agent tool, or running the test suite. Trigger on "run the app", "start dev servers", "add a domain", "add a tool", "run tests" in this repo.
---

# Dev workflow — Agentic RAG literature review app

This is a two-part app: `backend/` (FastAPI, Python 3.14, venv at
`backend/.venv`) and `frontend/` (React + Vite, plain JS). There is a root
`Makefile` with `install`, `dev-backend`, `dev-frontend`, `dev`, `test` targets
— prefer those over ad-hoc commands.

## Running locally

```bash
make install                                # first time only
cp backend/.env.example backend/.env        # edit JWT_SECRET_KEY
cp frontend/.env.example frontend/.env
make dev                                    # backend :8001, frontend :5173
```

Backend deliberately runs on **:8001**, not :8000 — a different, unrelated
service already occupies :8000 on this machine. The frontend's
`VITE_API_BASE_URL` must point at :8001.

The Groq API key and model are entered in the UI per session — there is
no `GROQ_API_KEY` env var anywhere, by design (see `README.md`).

## Running tests

```bash
cd backend && .venv/bin/python -m pytest -q
```

A project hook (`.claude/settings.json`) already runs this automatically after
any edit under `backend/app/`, so you often don't need to run it by hand — but
do run it explicitly after multi-file changes or before calling something done.

## Adding a new domain

Edit only `backend/app/domains/config.py`: add a `DomainConfig` entry to
`DOMAIN_REGISTRY` with `id`, `name`, `description`, `system_prompt_suffix`
(steers the agent's tool preference and vocabulary for that domain), and
`example_questions`. Nothing else needs to change — the frontend's
`DomainSelectPage` and `ResearchChatPage` read the registry via `GET /domains`.

## Adding a new agent tool

1. Add the OpenAI-style function schema to
   `backend/app/agent/tools/schemas.py` (`TOOL_SCHEMAS`).
2. Implement the tool in `backend/app/agent/tools/<name>_tool.py`. It must
   never raise — catch everything and return `{"error": "..."}`, matching
   `pubmed_tool.py`/`arxiv_tool.py`.
3. Dispatch it in `backend/app/agent/orchestrator.py`'s `_dispatch_tool`.
4. If it should feed the vector store (like the search tools do), call
   `app.rag.indexer.index_documents` on its results and merge into
   `source_registry` the same way `_index_pubmed_results`/`_index_arxiv_results`
   do.
5. Add a test in `backend/tests/test_<name>_tool.py` (mock HTTP with `respx`
   if it calls an external API) and extend
   `backend/tests/test_agent_orchestrator.py` to cover the new dispatch path.

## Delegating work

For backend-only changes, delegate to the `backend` subagent; for
frontend-only changes, delegate to the `frontend` subagent. For a
severity-triaged cleanup pass (cosmetic/nice-to-have items only, separate from
blocking bugs), use the `p3-triage` subagent.
