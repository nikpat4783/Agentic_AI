#prompt-engineering

# Prompt engineering log

The only prompt in this codebase that matters is
`backend/app/extraction/llm_extractor.py`'s `_SYSTEM_PROMPT` — the one
instruction set governing every narrative-field extraction
(`ejection_fraction`, `stenosis_severity`, `discharge_disposition`). There's
no stored LLM API key in this environment to run live A/B completions
against, so this is a design-time iteration based on prompt-engineering
principles and the review findings below, not an empirical accuracy
comparison — that empirical pass is exactly what a real deployment's
[[Extraction-Pipeline#Why this is the "66% faster" lever|accuracy-audit
loop]] is for, once real usage data exists.

## v1 → v2

**v1** asked for `{"value": ..., "confidence": ...}` with one line of
guidance: "confidence must reflect how certain you are." That's the
textbook failure mode for LLM self-reported confidence — no calibration
anchor, so the model has nothing to calibrate against except vibes, and no
way for a human reviewer to check the extraction without re-reading the
whole source document.

**v2** (current) adds two concrete things:

1. **A calibration rubric instead of a vibe**: explicit bands —
   `>=0.85` only for an explicit, unambiguous, correctly-formatted mention;
   `0.5-0.84` for a value present but requiring minor interpretation
   (synonym, inferred unit, one of several candidates); `<0.5` for weakly
   implied, contradicted, or guessed values. This is the single highest-
   leverage change: it's what actually determines the straight-through
   rate (the number the whole product claim rests on), and a rubric is far
   more reproducible across different documents than "be honest about your
   confidence."
2. **`source_phrase`**: the model now also returns the exact substring of
   the document supporting its extraction. This flows through
   `confidence.py`'s `build_rationale` into every field's `rationale`
   (`'... Source: "LVEF estimated at 35%".'`), which is what the frontend's
   `RationalePanel` displays — turning "trust the AI" into "here's exactly
   where I found this, go check it yourself."

## Why this matters more than model choice

For this product, the RAG-grounded spec text handed to the model (see
[[RAG-Engine]]) does more accuracy work than the base model's raw
capability — a small, fast model with a precise spec excerpt and a
calibration rubric will out-perform a larger model given only the bare
element name. The confidence-routing design (see
[[Extraction-Pipeline]]) means the LLM doesn't need to be right every
time — it needs to be *honestly uncertain* when it isn't, so the field
lands in the QA queue instead of silently shipping a wrong value at high
confidence. Prompt iteration here is therefore aimed squarely at confidence
calibration, not raw extraction accuracy.

## Next empirical step (not done here — no LLM key in this environment)

Once a real BYOK key is used against real (de-identified) sample charts:
compare the straight-through rate and the `accuracy-audit` numbers before
vs. after this prompt change, on the same document set, holding thresholds
fixed. If the straight-through rate rises without straight-through accuracy
dropping, the calibration rubric is doing its job; if straight-through
accuracy drops, the confidence bands need tightening, not loosening.
