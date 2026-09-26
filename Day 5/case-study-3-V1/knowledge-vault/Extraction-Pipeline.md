#backend #extraction

# Extraction pipeline

The core of the POC: a pluggable extractor registry dispatching purely off
each [[Backend|DataElementSpec]]'s `strategy` field, so adding a new data
element never requires touching the dispatch logic itself.

## Flow

1. A `SourceDocument` is ingested (`POST /documents`) with a `doc_type`.
2. `POST /documents/{id}/extract` runs, for every `DataElementSpec` whose
   `doc_type` matches, the extractor named by `strategy`:
   - `"rule"` → a regex/pattern function in `rule_extractors.py`, keyed by
     `element_name` in a `RULE_EXTRACTORS` dict.
   - `"llm"` → the generic BYOK LLM extractor in `llm_extractor.py`, which
     builds a prompt from the document text + the element's [[RAG-Engine|
     RAG-retrieved spec text]] and asks the model to extract a value and
     self-report a confidence.
3. `confidence.py` calibrates the raw extractor confidence and compares it
   to the element's `threshold`: at/above → `status="straight_through"`;
   below → `status="pending_qa"` and it appears in the QA queue.
4. An abstractor corrects queued fields via `POST /qa/{field_id}/correct` —
   this creates an `AbstractorCorrection` row without touching the original
   `ExtractedField`, preserving the audit trail.
5. Once every field for a document is straight-through or corrected,
   `POST /documents/{id}/submission` builds a flat `SubmissionRecord`.

## Why this is the "66% faster" lever

Human touch-time per chart scales with how many fields land in step 3's
`pending_qa` branch, not with total field count. The straight-through
fraction — visible live on the [[Observability|app-overview Grafana
dashboard]] — is the direct, measurable driver of the speed claim, and
`GET /documents/{id}/accuracy-audit` makes it checkable per document rather
than asserted.

## Cost control

Only fields whose spec sets `requires_llm=true` may invoke the LLM
extractor; rule-eligible fields never make an LLM call (see `SPEC.md` KPI
8). The LLM extractor itself never raises — missing/invalid credentials or
a failed call resolve to `extraction_method="llm_unavailable"`/`"llm_error"`
(confidence 0.0, queued for QA) so the pipeline always completes.

## Extending it

See `.claude/skills/dev-workflow/SKILL.md` → "Adding a new data element", or
use the `app-dev-orchestrator` MCP server's `add_data_element_spec` /
`scaffold_new_extractor` tools (see [[MCP-Servers]]) to do it without
hand-editing files.
