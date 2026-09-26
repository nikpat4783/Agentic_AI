# Test & Code-Review Report — 2026-09-26

Scope: initial build of the Carta Healthcare extraction POC (`backend/`,
`frontend/`, `mcp-server/`, `observability/`, `loadtest/`). No git history
exists for this project yet, so the `/code-review` pass reviewed the source
tree directly (backend + frontend + mcp-server) against `../SPEC.md`,
supplemented by a dedicated `p3-triage` pass and manual end-to-end
verification.

## Automated tests

`make test` (backend pytest): **21 passed** (18 from the initial build, plus
3 regression tests added during this review for the two fixes below).
Covers: rule extractors, confidence/threshold routing (including the
no-key/LLM-failure/rule-never-calls-LLM paths), the submission-build
409→200 precondition, the new QA-correction guard, the new
pick-up-a-later-added-spec behavior, and a fixture-based end-to-end flow.

## Manual end-to-end verification

Ran the full stack for real (backend `:8002`, frontend `:5174`, this
project's observability stack on its own ports): ingested a `cath_report`,
extracted (rule field straight-through, LLM fields queued for QA with no
key supplied), corrected both queued fields, built the submission, and
confirmed the accuracy-audit numbers. Confirmed `carta_fields_total` and
`carta_http_requests_total` (custom OTel metrics added during this pass)
flow through the collector into Prometheus within ~5s, and traces appear in
Tempo. Ran both k6 scenarios (`smoke`, `extraction`) against the live
backend — both passed all thresholds (0% failures).

## Code-review findings and disposition

A multi-angle `/code-review` pass plus a separate `p3-triage` pass covered
correctness, invariants, cross-file call/route consistency, reuse/
duplication, efficiency, and cosmetic backlog. Findings and what was done:

### Fixed during this pass

1. **Extraction idempotency froze a document's field set** (`routers/
   extraction.py`) — re-running `POST .../extract` short-circuited on "any
   existing fields" rather than per-element, so a `DataElementSpec` added
   after a document's first extraction could never be picked up, making
   that document permanently unsubmittable. Fixed to diff against existing
   `element_name`s and only resolve genuinely new specs. Regression test
   added.
2. **`POST /qa/{field_id}/correct` accepted a correction for any field**,
   including ones already `straight_through` or already corrected once —
   no status/idempotency check. Fixed to reject (409) correcting a
   non-`pending_qa` field or a field that already has a correction.
   Regression tests added.
3. **`scaffold_new_extractor`'s generated stub** (`mcp-server/server.py`)
   returned a bare `str | None`, which doesn't match the actual dict-based
   contract (`{value, raw_confidence, error}`) every real rule extractor
   uses and `registry.py`'s dict-spread dispatch depends on — a filled-in
   stub following the tool's own scaffold would have raised inside
   `registry.run_extraction`, violating the "extractors never raise"
   guarantee. Fixed the scaffold to emit the correct dict shape, with an
   explicit docstring explanation of why.
4. **`add_data_element_spec` allowed `strategy`/`requires_llm` to
   contradict each other** (e.g. `strategy="llm"` with
   `requires_llm=False`), silently producing a permanently-unresolvable
   element with no error anywhere. Added cross-field validation.
5. **RAG spec excerpt was retrieved twice per LLM-backed field** (once in
   `registry.py` for the prompt, again in `confidence.py` for the
   rationale) — doubling Chroma query volume per field for no reason.
   Consolidated to a single retrieval in `registry.py`, threaded through.
6. **LLM-call exception messages were persisted/returned verbatim**
   (`llm_extractor.py`) — `str(exc)` flowed into `ExtractedField.rationale`
   (DB + API responses) with no scrubbing, relying only on the assumption
   that no httpx exception ever echoes request internals. Narrowed to the
   exception type name only, matching what the logger already did.
7. **`SPEC.md` said the BYOK key travels via header**; the actual (and
   frontend-matching) contract is a JSON body field on the extract call.
   Fixed the doc to match reality rather than changing the contract.
8. **Prompt engineering** (`llm_extractor.py`'s system prompt): added an
   explicit confidence-calibration rubric (discrete bands tied to how
   explicit the source mention is) and a required `source_phrase` field so
   every LLM-sourced rationale cites the exact supporting text — see
   `../knowledge-vault/Prompt-Engineering.md`.

### Noted, not fixed (POC-appropriate, documented as follow-ups)

- N+1 query patterns in `routers/qa.py` (unscoped corrections scan +
  per-field document lookup) and `routers/submissions.py` (one corrections
  query per spec) — real but low-impact at POC data volumes.
- Independent LLM-backed fields within one document are resolved
  sequentially rather than concurrently — would help the per-document
  latency NFR at higher `requires_llm`-element counts.
- Duplicated "find the effective/latest value for a field" logic between
  `qa.py` and `submissions.py` — a shared helper would remove the drift
  risk, not currently causing incorrect behavior.
- 8 cosmetic/P3 items from the triage pass (frontend error-message
  duplication across 4 pages, a percent-formatting snippet duplicated 3x, a
  couple of ORM style inconsistencies, one dead defensive branch, a stale
  comment, one dev-note-flavored user-facing string, and no direct test for
  `app/metrics.py`'s trivial recorder functions) — none block correctness;
  left as a cleanup backlog rather than fixed in this pass.

## Verdict

Core correctness/robustness bar from `SPEC.md` (extractors never raise, BYOK
never logged/persisted, additive corrections, submission precondition,
graceful degradation) holds, and the two genuine correctness gaps the
review surfaced (idempotency freeze, missing QA-status guard) are fixed and
covered by new tests. Remaining findings are efficiency/style items
appropriate to leave as backlog for a POC at this scale.

## Addendum (same day): login gate + domain/model UX

Added after the review above, per a follow-up request: a single hardcoded
demo login (`admin`/`admin1234`, `app/auth.py` + `app/routers/auth.py`),
enforced on every documents/extraction/QA/submission route via
`Depends(require_auth)` at router-include time (`/health`/`/specs` remain
public); the doc-type selector relabeled "Domain" in the UI (values
unchanged); and the LLM default model changed from `openai/gpt-oss-20b` to
`openai/gpt-oss-120b`. Backend: 5 new tests (login success/failure,
protected-without-token, protected-with-invalid-token, health/specs stay
public) — **26 passed total**. `SPEC.md` updated to describe auth as a real
functional requirement rather than an excluded non-goal. The k6
`extraction` scenario updated to log in during `setup()` — re-verified
passing against the live backend after the change. Frontend build verified
(`npm run build`, zero errors) and the full contract re-confirmed via curl
against the live backend; no browser-based click-through of the login form
itself was possible in this environment (no headless-browser tool) — see
`../knowledge-vault/Demo.md` for what was and wasn't verified.
