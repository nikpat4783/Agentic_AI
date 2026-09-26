# Data Element: discharge_disposition

**Doc type**: discharge_summary

**Meaning**: Where/how the patient was discharged (disposition), as
described in the discharge summary narrative.

**Valid value format**: One of `"home"`, `"snf"` (skilled nursing facility),
`"rehab"`, `"transferred"`, or `"expired"` (lowercase, single word).

**Example source phrasings**:
- "discharged home in stable condition" -> extract `"home"`
- "transferred to a skilled nursing facility for continued rehabilitation" ->
  extract `"snf"`
