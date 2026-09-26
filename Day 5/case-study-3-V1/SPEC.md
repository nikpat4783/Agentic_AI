# Spec — Carta Healthcare: Automated Clinical Data Extraction

This is the project's specification: what the app is for, what it must do, and
the quality bar it's held to. It exists so a code review has a fixed target to
check against, rather than an implicit or shifting one. Keep it in sync with
reality — if the app's behavior and this file disagree, that's a defect in
whichever one is wrong.

Source design docs: `../03-carta-healthcare.md` (HLD/LLD this POC implements).

## 1. Purpose

A demo web app that automates extraction of structured clinical data elements
(the kind used by clinical registries — e.g. ejection fraction, lab values,
diagnosis codes) from source documents, routes low-confidence extractions to a
human abstractor for correction, and builds a submission-ready structured
record. The product claim being demonstrated: **66% faster** chart processing
than full manual abstraction, at **99% accuracy** on final submitted values.

## 2. Users

- **Abstractor**: reviews/corrects only the fields the system flagged as
  low-confidence; never re-keys a whole chart.
- **Registry program manager**: defines data-element specs (via the RAG spec
  corpus + `DataElementSpec` records) — a POC persona, exercised via the
  `add_data_element_spec` MCP tool rather than a UI in this build.
- **Quality/compliance reviewer**: consumes the accuracy-audit endpoint and the
  observability dashboards.

## 3. Functional requirements

- **Auth**: a login gate in front of the app — a single hardcoded demo
  account (`admin`/`admin1234`, overridable via `ADMIN_USERNAME`/
  `ADMIN_PASSWORD`). `POST /auth/login` issues an opaque bearer token held
  only in-memory server-side (never persisted to disk) and only in React
  state client-side (never `localStorage`); every document/extraction/QA/
  submission endpoint requires it. This is a single-account demo gate, not
  a real multi-user auth system — see non-goals.
- **Document ingestion**: accept a source document (plain text for the POC —
  standing in for an already-OCR'd scanned document or a structured excerpt)
  tagged with a `doc_type`.
- **Extraction**: for each `DataElementSpec` applicable to the document's
  `doc_type`, run the appropriate extractor (rule-based for well-formatted
  fields, LLM-backed for narrative fields) and produce an `ExtractedField`
  with a `value`, a calibrated `confidence` (0-1), and `extraction_method`.
- **RAG grounding**: every extraction is checked against the relevant spec
  text retrieved from the RAG index; the rationale returned to the UI cites
  that spec text, not just a bare model confidence number.
- **Confidence routing**: fields with `confidence >= threshold` (per-element,
  configurable) are marked `straight_through`; fields below threshold are
  queued for QA (`AbstractorCorrection`).
- **QA correction**: an abstractor can fetch the low-confidence queue and post
  a corrected value; this must never silently overwrite — every correction is
  recorded, keeping the original model output for audit.
- **Submission build**: once every field for a document is resolved
  (straight-through or corrected), build a `SubmissionRecord` — a flat
  structured JSON keyed by data-element name.
- **Accuracy audit**: an endpoint reports the straight-through rate and (for a
  sampled set of documents with a known gold-standard fixture) the accuracy
  of straight-through fields, so the 99% claim is checkable, not asserted.
- **BYOK**: the LLM-backed extractor requires the caller to supply their own
  LLM API key per request (a JSON body field on the extract call, not
  stored); the app never persists or
  logs it.

## 4. Non-functional requirements (the 10 KPIs)

1. **Accuracy / groundedness** — every `ExtractedField` traces to either a
   regex match span or an LLM extraction with a RAG-cited spec; no field value
   appears without a traceable source.
2. **Robustness / error handling** — extractor functions never raise; they
   return an error-tagged result so one bad field doesn't fail the whole
   document. A malformed/empty document degrades to "all fields queued for
   QA," never a 500.
3. **Security** — no PHI-bearing document text or LLM API key ever reaches a
   log line, and the BYOK key never reaches the database or a response body.
4. **Performance** — processing time per document (ingest → all fields
   resolved-or-queued) is measured and reported; the design goal is that the
   straight-through fraction (not raw compute speed) is what drives the
   64-66% reduction in human-touch time versus full manual abstraction.
5. **Observability** — every extraction, confidence score, and QA correction
   emits a trace/metric (OpenTelemetry → the local observability stack).
6. **Test coverage** — the extraction registry, confidence routing, and
   submission-build logic each have unit tests; a fixture-based end-to-end
   test covers ingest → extract → QA-correct → submit.
7. **Maintainability** — adding a new data element is a config change
   (`DataElementSpec` + a RAG spec doc), never a pipeline code change, unless
   it needs a genuinely new extraction strategy.
8. **Cost awareness** — the LLM-backed extractor is only invoked for fields
   whose spec marks them `requires_llm`; rule-based fields never make an LLM
   call. Load-test scenarios that would incur LLM cost are opt-in and guarded
   behind an explicit env var.
9. **Documentation** — `knowledge-vault/` covers every subsystem; `README.md`
   covers how to run it.
10. **Usability** — the review UI shows confidence visually (not just a
    number) and never lets an abstractor approve a document with unresolved
    low-confidence fields.

## 5. Explicit non-goals

- No real OCR (documents are submitted as plain text, standing in for
  already-digitized text).
- No real clinical registry integration (submission records are built and
  stored locally, not transmitted to an external registry API).
- No real multi-user auth system — a single hardcoded demo account gates
  the UI (see Functional requirements); no user table, no registration, no
  per-user data isolation, no password hashing/rotation.
- No production-grade PHI de-identification pipeline — sample documents are
  synthetic, not real patient data.
