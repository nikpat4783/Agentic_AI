# Data Element: stenosis_severity

**Doc type**: cath_report

**Meaning**: The qualitative severity of coronary artery stenosis (narrowing)
described in the catheterization report narrative, for the most severely
affected vessel mentioned.

**Valid value format**: One of `"mild"`, `"moderate"`, `"severe"`, or
`"occluded"` (lowercase, single word).

**Example source phrasings**:
- "severe stenosis of the LAD" -> extract `"severe"`
- "moderate narrowing of the right coronary artery" -> extract `"moderate"`
