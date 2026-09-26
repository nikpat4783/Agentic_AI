# Sample documents for manual testing

10 synthetic (not real patient data) clinical documents — 5 `cath_report`,
5 `discharge_summary` — designed to exercise the extraction pipeline's
happy path *and* its interesting edge cases: missing values, unit
mismatches, conflicting mentions, and ambiguous phrasing.

## How to use them

1. Log in at http://localhost:5174 (`admin` / `admin1234`).
2. On the Upload page, pick the matching **Domain** (Cardiology — Cath
   Report, or General — Discharge Summary).
3. Open one of these `.txt` files, copy its contents, paste into the
   document-content field (there's no file-picker in the UI — it's a
   plain-text POC, per `SPEC.md`'s non-goals — so copy/paste is the path).
4. Optionally paste a real Groq API key to see the LLM-backed fields
   actually resolve instead of queuing for QA.
5. Submit, and watch which fields land `straight_through` (green) vs.
   `pending_qa` (amber) on the review page, and why (expand each field's
   rationale).

## What each file demonstrates

Rule-based fields (`troponin_level`, `primary_diagnosis_code`) are
regex-matched — see `backend/app/extraction/rule_extractors.py` for the
exact patterns — so their pass/fail behavior below is deterministic and
doesn't depend on whether you supply an LLM key.

| File | Domain | What it's testing |
|---|---|---|
| `01-cath-clear-complete.txt` | Cath Report | The happy path — all 3 fields clearly stated in expected format. `troponin_level` → straight-through. `ejection_fraction`/`stenosis_severity` → straight-through if an LLM key is supplied (clear, unambiguous mentions), `pending_qa` otherwise. |
| `02-cath-missing-troponin.txt` | Cath Report | Troponin is explicitly *not reported* ("results pending"). `troponin_level` → `pending_qa` via the **rule** extractor's own no-match path (not just LLM fields can queue). |
| `03-cath-ambiguous-stenosis.txt` | Cath Report | Stenosis severity is deliberately unclassifiable ("moderate to severe... further evaluation recommended"). Tests the LLM's confidence-calibration rubric — should self-report low confidence and queue even with a key, unlike EF/troponin in the same doc which are clear. |
| `04-cath-conflicting-ef.txt` | Cath Report | Two different EF values from two sources (echo vs. cath) with an explicit note on which to trust. Tests whether the LLM correctly resolves to the more authoritative (catheterization) value rather than getting confused. |
| `05-cath-unusual-troponin-unit.txt` | Cath Report | Troponin value is present (`45 pg/mL`) but in a unit the regex doesn't recognize (only `ng/mL`/`ug/L`/`mcg/L` are accepted). `troponin_level` → `pending_qa` — a genuine, honest gap in the rule extractor's pattern coverage, worth seeing surfaced rather than silently missed. |
| `06-discharge-clear-complete.txt` | Discharge Summary | The happy path — explicit ICD-10 code + explicit "home" disposition. Both fields should resolve straight-through (rule always; LLM disposition if a key is supplied). |
| `07-discharge-missing-code.txt` | Discharge Summary | No ICD-10-shaped code anywhere in the text (diagnosis stated only in prose, coding "not yet finalized"). `primary_diagnosis_code` → `pending_qa` via the rule extractor's no-match path. |
| `08-discharge-facility-transfer.txt` | Discharge Summary | Disposition is *not* home — patient goes to a skilled nursing facility. Tests that the LLM extracts a real, specific non-default value rather than defaulting to "home". |
| `09-discharge-multiple-codes.txt` | Discharge Summary | Two ICD-10-shaped codes present (primary `E10.10` + secondary `I10`). The regex takes the *first* match in the text — this file places the true primary diagnosis first, so it should correctly pick `E10.10`, not the secondary code. |
| `10-discharge-ambiguous-disposition.txt` | Discharge Summary | Disposition is genuinely undecided at time of dictation ("plan still being coordinated... pending placement"). Should stay `pending_qa` even with an LLM key, since there's no actual answer in the text to extract. |

## Why this set is useful

Together these 10 documents give you at least one straight-through case and
one legitimate QA-queue case for every one of the 5 seeded data elements —
so you can see both halves of the confidence-routing story (not just the
demo-friendly happy path) and try correcting a few queued fields through
to a built submission.
