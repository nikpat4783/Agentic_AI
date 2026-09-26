#backend

# Backend

FastAPI (Python 3.14), SQLAlchemy + SQLite (`backend/app.db`), on `:8002`.

## Layout

- `app/main.py` — app creation, CORS (`http://localhost:5174`), lifespan
  hook (create tables, seed the 5 `DataElementSpec` rows from
  `seed_specs.py` if empty, warm the RAG index), a request-timing
  middleware recording `carta_http_requests_total`/`_duration_seconds`
  (see [[Observability]]), router wiring, `/health` and `/specs`.
- `app/config.py` — env-driven settings (CORS origin, DB URL, Chroma
  persist dir, embedding model name, default BYOK LLM base URL/model,
  OTel endpoint/service name). No secrets live here.
- `app/models/` — `SourceDocument`, `DataElementSpec`, `ExtractedField`,
  `AbstractorCorrection`, `SubmissionRecord`.
- `app/routers/{documents,extraction,qa,submissions}.py` — see
  [[Extraction-Pipeline]] for the extraction/QA/submission flow in detail.
  `POST /documents/{id}/extract` is idempotent per document (a second call
  returns the already-persisted fields rather than duplicating rows).
- `app/extraction/{registry,rule_extractors,llm_extractor,confidence,
  seed_specs}.py` and `app/rag/{embeddings,vector_store,retriever,specs/*.md}`
  — see [[Extraction-Pipeline]] and [[RAG-Engine]].
- `app/metrics.py` / `app/observability.py` — custom OTel metric
  instruments and the trace/metric/log provider wiring — see
  [[Observability]].
- `app/schemas.py` — shared Pydantic request/response models used across
  more than one router.
- `app/auth.py` + `app/routers/auth.py` — a single hardcoded demo login
  gate (`admin`/`admin1234` by default). `POST /auth/login` issues an
  opaque, in-memory-only bearer token (never persisted, mirroring the BYOK
  key's "never stored" rule); `POST /auth/logout` revokes it. Every
  documents/extraction/QA/submission endpoint requires
  `Authorization: Bearer <token>` (enforced at router-include time in
  `main.py`, not inside the router files); `/health` and `/specs` stay
  public. This is a demo gate for one account, not a real user system.

## BYOK LLM extraction

`llm_extractor.py` is generic (not hardcoded per element): given the
document text, the element's RAG-retrieved spec excerpt, and the caller's
API key/model/base_url (all optional, per-request only, never persisted),
it calls an OpenAI-compatible chat-completions endpoint (default: Groq's
`openai/gpt-oss-120b` — `llama-3.1-8b-instant` was confirmed deprecated by
Groq during the build and swapped out, and the default was later moved
from the smaller `gpt-oss-20b` to `gpt-oss-120b` per a follow-up request)
asking for a value + self-reported confidence. It never raises: no key →
`extraction_method="llm_unavailable"`; a failed call → `"llm_error"` — both
resolve to confidence 0.0 (queued for QA) rather than breaking the
pipeline.

## Seed data element specs

| element_name | doc_type | strategy | requires_llm | threshold |
|---|---|---|---|---|
| ejection_fraction | cath_report | llm | true | 0.75 |
| stenosis_severity | cath_report | llm | true | 0.75 |
| troponin_level | cath_report | rule | false | 0.9 |
| primary_diagnosis_code | discharge_summary | rule | false | 0.9 |
| discharge_disposition | discharge_summary | llm | true | 0.7 |

## Tests

`backend/tests/` — rule extractors (deterministic), confidence/threshold
routing (including the no-key and LLM-failure paths, and a guard proving
rule-strategy elements never call the LLM even if a key is supplied), the
submission-build 409→200 precondition, `/health`+`/specs`, and a
fixture-based end-to-end test (both sample doc types, LLM extractor
monkeypatched so tests never hit the network). **18 passed.**
