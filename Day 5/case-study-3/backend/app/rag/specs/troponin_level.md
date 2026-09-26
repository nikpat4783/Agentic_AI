# Data Element: troponin_level

**Doc type**: cath_report

**Meaning**: The patient's measured troponin lab value, a well-formatted
numeric lab result with a unit, extracted deterministically via regex (no
narrative interpretation needed).

**Valid value format**: A decimal number followed by a unit, as a string
(e.g. `"0.04 ng/mL"`).

**Example source phrasings**:
- "troponin 0.04 ng/mL" -> extract `"0.04 ng/mL"`
- "Troponin I level: 1.2 ng/mL on admission" -> extract `"1.2 ng/mL"`
