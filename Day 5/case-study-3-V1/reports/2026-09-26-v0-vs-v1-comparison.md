# v0 vs V1 Comparison — 2026-09-26

Scope: `case-study-3-v0` (existing/baseline) vs. `case-study-3-V1` (this
project) — the Carta Healthcare clinical-data-extraction POC.

## Baseline

Before this pass, `case-study-3-V1`'s source tree was byte-identical to
`case-study-3-v0` (`diff -rq`, excluding `.venv`/`node_modules`/`.git`/
`.pytest_cache`) except for one missing file: **`.mcp.json`** (the custom
`app-dev-orchestrator` + `fetch` MCP server config) was present in v0 but
absent from V1. Every difference described below is therefore a genuine V1
advancement, not pre-existing drift between the two copies.

The two directories had already been through one shared review pass
(`reports/2026-09-26-test-and-review.md`), which fixed two correctness bugs
common to both, and explicitly left several items as backlog:

> N+1 query patterns in `routers/qa.py`... and `routers/submissions.py`...
> Independent LLM-backed fields within one document are resolved
> sequentially rather than concurrently... Duplicated "find the effective/
> latest value for a field" logic between `qa.py` and `submissions.py`.

V1 closes that backlog (plus one new bug the fresh review below surfaced)
that v0 still carries as-is.

## New in V1: a dedicated `code-reviewer` subagent

Added `.claude/agents/code-reviewer.md` — a project subagent (`tools: Read,
Grep, Glob, Bash, ReportFindings`, read-only) that reviews `backend/` and/or
`frontend/` for P0-P2 correctness, security, and genuine efficiency/reuse
issues. It's deliberately scoped **not** to overlap the two review tools v0
already had:

| Reviewer | Scope |
|---|---|
| `p3-triage` (existing) | P3/cosmetic backlog only |
| `pr-review-toolkit` plugin (existing) | deep security pass |
| **`code-reviewer` (new in V1)** | P0-P2 correctness / security / efficiency, explicitly declines P3 |

It was used in this pass to review `backend/app/` and `frontend/src/`
against `SPEC.md` and surfaced Finding 3 below (a real bug neither of the
other two tools would have caught: `p3-triage` because it's P1, not P3;
`pr-review-toolkit` because it's a UI-state bug, not a security issue).

## Code advancements

### 1. N+1 queries in the QA queue — `backend/app/routers/qa.py`

**Before**: `get_qa_queue` ran an unscoped `AbstractorCorrection.field_id`
full-table scan (every correction in the DB, regardless of relevance), plus
one `db.get(SourceDocument, ...)` per pending field inside the loop.

**After**: the corrected-ids lookup is scoped to just the pending fields'
ids, and all needed `SourceDocument`s are batch-fetched once into a dict
before the loop. Same output, O(1) extra queries instead of O(pending
fields).

### 2. N+1 queries + missing idempotency in submission build — `backend/app/routers/submissions.py`

**Before**: `build_submission` ran one `AbstractorCorrection` query per
`DataElementSpec` in its loop, and had no guard against building a second
`SubmissionRecord` for an already-fully-resolved document — calling the
endpoint twice silently created two identical rows.

**After**: corrections for the document's fields are fetched once and
reduced to latest-per-field in Python. The endpoint now checks for an
existing `SubmissionRecord` for the document first and returns it unchanged
(200) instead of inserting a duplicate — matching this codebase's existing
idempotency pattern for extraction (per-element) and QA correction
(rejects duplicates). Covered by a new test,
`test_submission_build_is_idempotent_for_already_resolved_document`.

### 3. Submission gate silently broken after any QA correction (new finding) — `backend/app/schemas.py`, `backend/app/routers/extraction.py`, `frontend/src/pages/ExtractionReviewPage.jsx`

**Found by the new `code-reviewer` agent**, not in the original backlog.
`ExtractedField.status` deliberately never flips after a QA correction (an
audit-trail invariant — only the additive `AbstractorCorrection` row
records that a field was resolved). The frontend's "Build submission" gate,
however, computed readiness from `status !== 'pending_qa'` — so once *any*
field on a document needed a correction, the gate stayed disabled forever,
even after that field was corrected and the backend would have accepted
the submission. This broke the UI path for the app's own core workflow
(ingest → extract → QA-correct → submit) for the ordinary case where not
every field resolves straight-through.

**Fix**: added a purely additive `resolved: bool` to `FieldOut` (`status`
untouched), computed server-side from `status == "straight_through" OR has
a correction on file`, exposed on both `POST /documents/{id}/extract` and
`GET /documents/{id}/fields`. The frontend's gate/pending-count now use
`field.resolved` instead of re-deriving (and mis-deriving) it from `status`.
Verified end-to-end: `frontend/src/api/client.js` passes response bodies
through untransformed, so the new field reaches the page unmodified.

### 4. Sequential LLM extraction calls — `backend/app/routers/extraction.py`, `backend/app/extraction/llm_extractor.py`

**Before**: `extract_document` resolved every newly-added `DataElementSpec`
one at a time in a `for` loop, each potentially making a blocking,
synchronous LLM HTTP call — so a document with N `requires_llm` elements
paid N sequential round-trips.

**After**: resolution (not the DB writes) runs through a bounded
`ThreadPoolExecutor(max_workers=4)`, order-preserving, before the existing
sequential `db.add`/`db.commit` loop. Safe because `resolve_field` touches
no DB session (only Chroma + `httpx`, verified by reading `confidence.py`/
`registry.py`) and existing test mocking
(`monkeypatch.setattr(llm_extractor, "extract", ...)`) still applies
correctly under threads since it patches the module object itself. Covered
by a new deterministic test, `test_extract_parallel_resolution_preserves_
order_and_values` (asserts correct per-field values/order — no timing
assertions, so no flakiness risk).

### 5. Shared "latest correction per field" helper — `backend/app/models/abstractor_correction.py`

Fixes 1, 2, and 3 all need "the latest `AbstractorCorrection` per field, for
a batch of field ids." Rather than writing that query three times (or once
and letting it drift), added one helper, `latest_by_field(db, field_ids)`,
now used by `qa.py`, `submissions.py`, and `extraction.py`. This directly
resolves the "duplicated effective-value logic" item noted (but not fully
realized until Finding 3 needed it a third time) in the original backlog —
and matches this project's own convention that a shared helper is
justified once there are 3+ real call sites, not before.

### 6. Tooling parity — `.mcp.json`

Copied `.mcp.json` (the `app-dev-orchestrator` + `fetch` MCP server config)
from v0 into V1's repo root, closing the one non-code gap found. V1 is now
a strict superset of v0's setup, not a regression on it.

## Test verification

| | v0 / V1 before this pass | V1 after this pass |
|---|---|---|
| Backend pytest | 26 passed | **28 passed** (+2: submission idempotency, extraction concurrency) |
| Frontend build | — | `npm run build`: clean, 111 modules, no errors |

## Summary

| | v0 | V1 |
|---|---|---|
| Code-review coverage | `p3-triage` (P3 only) + `pr-review-toolkit` (security) | + new `code-reviewer` agent (P0-P2 correctness/efficiency) |
| QA queue query cost | O(all corrections) + O(pending fields) doc lookups | O(1) batched queries |
| Submission build | duplicate rows on repeat calls | idempotent (returns existing record) |
| Submission-readiness UI gate | broken after any QA correction | fixed via new `resolved` field |
| Per-document LLM extraction latency | sequential per `requires_llm` element | parallelized (bounded thread pool) |
| `.mcp.json` | present | present (copied) |
| Backend tests | 26 passed | 28 passed |
