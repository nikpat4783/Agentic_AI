# Data Element: ejection_fraction

**Doc type**: cath_report

**Meaning**: Left ventricular ejection fraction (LVEF), the percentage of
blood pumped out of the left ventricle with each contraction, as documented
by the cardiologist in the catheterization report narrative.

**Valid value format**: A bare integer or integer range as a string, no
percent sign (e.g. `"35"`, `"55-60"`).

**Example source phrasings**:
- "LVEF estimated at 35%" -> extract `"35"`
- "Left ventricular ejection fraction is normal at 55-60%" -> extract `"55-60"`
