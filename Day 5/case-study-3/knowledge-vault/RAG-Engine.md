#backend #rag

# RAG engine

A small retrieval-augmented-generation layer whose only job is to ground
extraction confidence decisions in documented registry data-element specs —
not a general-purpose document search feature.

## What's indexed

`backend/app/rag/specs/*.md` — one file per data element, hand-authored,
each describing what the field means, its valid value format/range, and 1-2
example source phrasings (e.g. `ejection_fraction.md` explains that LVEF is
reported as a percentage 0-100 and is usually phrased as "LVEF estimated
at N%" in a cath report).

## How it's built

`app/rag/embeddings.py` — local `sentence-transformers` model (no API key
required). `app/rag/vector_store.py` — a Chroma persistent collection at
`backend/chroma_data/` (gitignored), built from the spec files at backend
startup; idempotent, so a restart doesn't re-embed everything if the
collection already has the expected document count.

## How it's used

`app/rag/retriever.py` is called from [[Extraction-Pipeline|
confidence.py]] for the field's `element_name`; the retrieved spec excerpt
is woven into that field's `rationale` string, which the frontend shows in
its `RationalePanel` (see [[Frontend]]). This is what makes a flagged
field's explanation something an abstractor can actually verify against —
"per spec, X" — rather than a bare model confidence number.

## Extending it

Adding a new data element's spec text under `app/rag/specs/<name>.md` (via
`add_data_element_spec` on the `app-dev-orchestrator` MCP server, see
[[MCP-Servers]]) and restarting the backend re-indexes it automatically.
