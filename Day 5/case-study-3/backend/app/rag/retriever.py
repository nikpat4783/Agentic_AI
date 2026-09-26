"""Retrieval of grounding spec text for a given data element.

`confidence.py` calls `retrieve_spec_excerpt()` for the field's element_name
and cites the result in the field's rationale, so every extraction is
checked against - and cites - the relevant spec text (SPEC.md: RAG
grounding).
"""
from __future__ import annotations

import os

from app.config import settings
from app.rag.embeddings import embed_texts
from app.rag.vector_store import get_collection


def _excerpt(text: str, max_chars: int = 220) -> str:
    text = " ".join(text.split())
    return text if len(text) <= max_chars else text[: max_chars - 1].rstrip() + "..."


def _fallback_read(element_name: str) -> str | None:
    """Read the spec file directly, for use when the vector store is empty
    or unavailable (e.g. Chroma/embedding model not installed in a test
    environment)."""
    path = os.path.join(settings.specs_dir, f"{element_name}.md")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    return None


def retrieve_spec_excerpt(element_name: str, query_text: str | None = None) -> str:
    """Return a short excerpt of the most relevant spec text for element_name.

    Queries the Chroma collection by the element's own spec text (or, if
    given, richer query text) and falls back to reading the spec file
    directly if the vector store can't answer (keeps confidence.py robust
    per the "extractors never raise / degrade gracefully" rule).
    """
    try:
        collection = get_collection()
        query = query_text or element_name
        query_embedding = embed_texts([query])[0]
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=1,
            where={"element_name": element_name},
        )
        documents = result.get("documents") or []
        if documents and documents[0]:
            return _excerpt(documents[0][0])
    except Exception:
        pass

    fallback = _fallback_read(element_name)
    if fallback:
        return _excerpt(fallback)
    return f"(no spec text found for {element_name})"
