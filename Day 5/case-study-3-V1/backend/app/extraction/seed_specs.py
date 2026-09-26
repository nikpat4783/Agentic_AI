"""The 5 seed `DataElementSpec` rows, as a plain, greppable, appendable list.

This is the single source of truth for the demo's seed data elements. It is
imported by the startup-seed logic (see `app/db.py` / `app/main.py`) to
populate the `DataElementSpec` table if empty, and is also the intended
integration point for external tooling (e.g. an MCP server's
`add_data_element_spec` tool) that wants to add/inspect specs without
depending on any other internal implementation detail of this backend.

Adding a new element: append a dict here, and add its spec text file under
`app/rag/specs/<element_name>.md`. No other file needs to change unless the
new element needs a genuinely new extraction strategy beyond "rule"/"llm".
"""
from __future__ import annotations

SEED_SPECS: list[dict] = [
    {
        "element_name": "ejection_fraction",
        "doc_type": "cath_report",
        "strategy": "llm",
        "requires_llm": True,
        "threshold": 0.75,
        "spec_text_path": "app/rag/specs/ejection_fraction.md",
    },
    {
        "element_name": "stenosis_severity",
        "doc_type": "cath_report",
        "strategy": "llm",
        "requires_llm": True,
        "threshold": 0.75,
        "spec_text_path": "app/rag/specs/stenosis_severity.md",
    },
    {
        "element_name": "troponin_level",
        "doc_type": "cath_report",
        "strategy": "rule",
        "requires_llm": False,
        "threshold": 0.9,
        "spec_text_path": "app/rag/specs/troponin_level.md",
    },
    {
        "element_name": "primary_diagnosis_code",
        "doc_type": "discharge_summary",
        "strategy": "rule",
        "requires_llm": False,
        "threshold": 0.9,
        "spec_text_path": "app/rag/specs/primary_diagnosis_code.md",
    },
    {
        "element_name": "discharge_disposition",
        "doc_type": "discharge_summary",
        "strategy": "llm",
        "requires_llm": True,
        "threshold": 0.7,
        "spec_text_path": "app/rag/specs/discharge_disposition.md",
    },
]
