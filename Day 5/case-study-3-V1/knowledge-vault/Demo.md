#demo

# Demo — click-through script for a first user

Prereqs: `make install` once, then `make dev` (backend `:8002`, frontend
`:5174`). Optionally `cd observability && docker compose up -d` first if you
want live metrics/traces during the demo.

This script was validated end-to-end against the real running backend via
`curl` (see below for the exact sequence and responses) — the UI steps
below are the same flow through the pages the [[Frontend]] agent built.
No headless-browser tool exists in this environment, so the UI portion of
this script is a script to *run yourself* in a real browser, not something
this session visually verified — the API-level flow it wraps was verified.

## 0. Log in

Open http://localhost:5174 → redirects to **LoginPage**. Enter the demo
account (`admin` / `admin1234`) — shown as an on-screen hint. On success,
lands on the Upload page; every other page is unreachable without this.

## 1. Upload a document

**UploadPage**. Pick a **Domain** (`Cardiology — Cath Report` /
`General — Discharge Summary`, backed by the same `doc_type` values as
before, just relabeled) — pre-filled sample text is already realistic
(LVEF %, stenosis description, troponin value for the cardiology domain).
Leave the LLM API key blank for the "safe, free" path (fields resolve to
`llm_unavailable`), or paste a real Groq BYOK key to see the LLM-backed
fields actually resolve — leave the model field blank too and it defaults
server-side to `openai/gpt-oss-120b`. Submit.

## 2. Review extracted fields

Lands on **ExtractionReviewPage**. Point out:
- `troponin_level` is green (`straight_through`) — a rule-based regex
  match, resolved instantly, no LLM involved.
- `ejection_fraction`/`stenosis_severity` are amber (`pending_qa`) if no
  key was supplied — expand the `RationalePanel` to show the RAG-grounded
  explanation ("No LLM API key was supplied for this request; queued for
  QA") and the retrieved spec excerpt.
- The stats strip shows the live straight-through rate — **this number is
  the literal mechanism behind the product's "66% faster" claim**: it's
  the fraction of fields that never needed a human at all.
- "Build submission" is disabled with an explanatory tooltip while any
  field is still pending.

## 3. Correct the queued fields

Go to **QAQueuePage**. Each item shows the exact source excerpt it was
extracted from. Enter a corrected value + abstractor id, submit — item
disappears from the queue with a success banner.

## 4. Build the submission

Back on the review page, "Build submission" is now enabled. Click through
to **SubmissionPage** → the flat structured record renders as a clean
key/value table — this is the artifact that would flow to a real clinical
registry.

## 5. (Optional) Try to correct an already-resolved field

Attempt `POST /qa/{a straight_through field's id}/correct` (e.g. via the
API docs at `:8002/docs`) — it now correctly rejects with 409, a fix made
during this build's code-review pass (see `../reports/`).

## Verified API-level flow (what step 0-4 above wraps)

```
POST /auth/login {"username":"admin","password":"admin1234"}      -> {token}
POST /documents {"doc_type":"cath_report","content":"..."}        -> {document_id}   (Authorization: Bearer <token> on every call below)
POST /documents/{id}/extract {}                                   -> troponin_level straight_through,
                                                                       ejection_fraction/stenosis_severity pending_qa
GET  /qa/queue                                                     -> the 2 pending fields, with source excerpts
POST /qa/{field_id}/correct {"corrected_value":"35",...}           -> 200, twice
GET  /qa/queue                                                     -> []
POST /documents/{id}/submission                                    -> 200, flat record
GET  /documents/{id}/accuracy-audit                                 -> straight_through_rate: 0.333
```

All of the above was run for real against the live backend during this
build (see `../reports/` for the dated test/review report), including the
observability angle: `carta_fields_total` and `carta_http_requests_total`
were confirmed flowing through the OTel collector into this project's own
Prometheus (`:9091`) within seconds of each call, and traces for the same
requests appeared in Tempo (`:3201`) — see [[Observability]].
