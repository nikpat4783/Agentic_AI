# Data Element: primary_diagnosis_code

**Doc type**: discharge_summary

**Meaning**: The primary discharge diagnosis, coded to ICD-10-CM, as a
well-formatted structured code extracted deterministically via regex (no
narrative interpretation needed).

**Valid value format**: An ICD-10-shaped code: one letter, two digits,
optionally a `.` followed by one or more digits (e.g. `"I21.4"`, `"I50"`).

**Example source phrasings**:
- "Primary diagnosis: I21.4 (Non-ST elevation myocardial infarction)" ->
  extract `"I21.4"`
- "Discharge diagnosis code I50.9" -> extract `"I50.9"`
