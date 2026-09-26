# Test & Code Review Report — 2026-09-19

Scope: full backend (`backend/app/`) and frontend (`frontend/src/`) as they
stand today. No diff/PR existed to review against (repo is not under git
yet), so this reviews the whole app.

## Test results

- **Backend**: `cd backend && .venv/bin/python -m pytest -q` → **29 passed**, 0 failed.
- **Frontend**: `npm run build` → succeeds, no build errors.
- **Gap**: the frontend has **no automated test suite** (no vitest/jest
  configured, no `*.test.*` files exist). All frontend verification so far
  has been manual/browser-driven, not regression-tested.

## Code review findings (`code-review` skill, high effort)

Ranked most-severe first, with my own rough P0-P3 severity call (per the
`p3-triage` subagent's scale) added in brackets.

1. **[P2] Missing session ownership check** — `backend/app/routers/research.py:32`.
   `session_id` from the request body is never bound to the authenticated
   user; it's used directly to pick the Chroma collection. If a `session_id`
   (a UUID) ever leaked, another user could read that session's indexed
   documents. Low likelihood (UUIDs aren't guessable) but a real missing
   authorization check.
2. **[P1] bcrypt 72-byte limit not handled** — `backend/app/security.py:17`.
   `UserCreate.password` allows up to 128 chars, but `bcrypt.hashpw` hard-fails
   above 72 bytes with no try/except around it in `routers/auth.py`. A
   legitimate 80+ character password 500s instead of getting a clean 400.
3. **[P2] `session_id` has no validation** — `backend/app/schemas.py:30`.
   Unlike `model`/`question` on the same request model, `session_id` has no
   length/charset constraint, and flows unvalidated into Chroma collection
   naming — an empty/huge/weird value produces an opaque exception deep in
   the agent loop instead of a clean 400.
4. **[P2] Orphaned vector-store chunks on re-index** — `backend/app/rag/indexer.py:21`.
   `chunk_id` dedup only skips IDs already present; it never removes stale
   trailing chunks if the same source is re-indexed with fewer chunks than
   before, so old content can linger and resurface in retrieval.
5. **[P2] Citation regex drops pre-2007 arXiv IDs** — `backend/app/agent/orchestrator.py:16`.
   `CITATION_PATTERN` doesn't allow `/`, so citations like
   `[arXiv:hep-th/9901001]` are silently dropped from the returned citation
   list even though the answer text references them.
6. **[P2] Frontend ignores the `:domainId` route param** — `frontend/src/App.jsx:27`.
   A refresh or a direct/bookmarked link to `/research/logistics` bounces the
   user back to domain selection, because `ResearchChatPage` only trusts
   in-memory `SessionContext` state, never the URL param.
7. **[P3] `max_results: null` from the LLM isn't defaulted** — `backend/app/agent/orchestrator.py:93`.
   `args.get("max_results", 5)` only applies the default when the key is
   *missing*, not when the model explicitly sends `null`; the resulting
   `TypeError` gets swallowed into a generic tool error instead of falling
   back to 5.
8. **[P3] Malformed tool-call JSON fails silently** — `backend/app/agent/orchestrator.py:57`.
   A `json.JSONDecodeError` becomes an empty args dict with no logging,
   unlike the sibling `OpenRouterError` path, which surfaces cleanly to the
   client.
9. **[P3] `retrieve_from_index`'s `top_k` isn't clamped** — `backend/app/rag/indexer.py:38`.
   `search_pubmed`/`search_arxiv` clamp `max_results` to `[1, 10]`; the vector
   tool doesn't clamp `top_k`, so `0`/negative values degrade to a generic
   Chroma error instead of a sane result.
10. **[P3] Raw error body shown to the user** — `frontend/src/api/research.js:21`.
    A non-2xx SSE response renders the literal JSON body
    (`Request failed (400): {"detail":"Unknown domain"}`) instead of
    extracting `.detail`, unlike the auth pages, which do this correctly.

## Suggested next step

None of these are fixed yet — this is the review/report only. #2 (bcrypt) is
the one most likely to actually bite a real user; #1, #3-#6 are worth fixing
before this goes beyond a demo. #7-#10 are minor/edge-case.
