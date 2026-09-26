"""Local sentence-transformers embedding model, loaded once and reused.

Kept as a thin wrapper (rather than calling SentenceTransformer directly
everywhere) so tests can monkeypatch `get_embedder` / `embed_texts` without
downloading a real model.
"""
from __future__ import annotations

from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def get_embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model_name)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts, returning plain python lists (Chroma-friendly)."""
    model = get_embedder()
    vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return vectors.tolist()
