---
name: dev-workflow
description: Use for any question about how to run, test, or extend this repo — starting the backend and frontend dev servers, adding a new data-element spec/extractor, or running the test suite. Trigger on "run the app", "start dev servers", "add a data element", "add an extractor", "run tests" in this repo.
---

# Dev workflow — Carta Healthcare extraction POC

This is a two-part app: `backend/` (FastAPI, Python 3.14, venv at
`backend/.venv`) and `frontend/` (React + Vite, plain JS). There is a root
`Makefile` with `install`, `dev-backend`, `dev-frontend`, `dev`, `test`
targets — prefer those over ad-hoc commands.

## Running locally

```bash
make install                                # first time only
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
make dev                                    # backend :8002, frontend :5174
```

Backend deliberately runs on **:8002**, not :8000/:8001 — other, unrelated
services already occupy those ports on this machine. The frontend's
`VITE_API_BASE_URL` must point at :8002.

The LLM API key (used only by the narrative-field extractor) is entered in
the UI per session — there is no stored API key anywhere, by design.

## Running tests

```bash
cd backend && .venv/bin/python -m pytest -q
```

A project hook (`.claude/settings.json`) already runs this automatically
after any edit under `backend/app/`, so you often don't need to run it by
hand — but do run it explicitly after multi-file changes or before calling
something done.

## Adding a new data element

1. Add a `DataElementSpec` row (name, `doc_type`, `strategy` = `"rule"` or
   `"llm"`, `requires_llm`, confidence `threshold`) — via a fixture/seed or
   the `add_data_element_spec` MCP tool.
2. Add its spec text under `backend/app/rag/specs/<element_name>.md` (what
   the field means, valid value format/range, source document types) — this
   is what the RAG retriever grounds the extraction rationale in.
3. Rebuild the RAG index (re-run the indexer, or restart the backend if it
   indexes on startup).
4. If `strategy = "rule"`, add a pattern to `rule_extractors.py`; if
   `"llm"`, no code change is needed — the LLM extractor is generic and
   driven by the spec text.

Nothing else needs to change — the extraction registry dispatches purely
off the `DataElementSpec` row.

## Delegating work

For backend-only changes, delegate to the `backend` subagent; for
frontend-only changes, delegate to the `frontend` subagent. For a
severity-triaged cleanup pass (cosmetic/nice-to-have items only, separate
from blocking bugs), use the `p3-triage` subagent.
