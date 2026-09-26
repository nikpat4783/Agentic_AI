import hashlib

import numpy as np
import pytest

import app.rag.embeddings as embeddings
import app.rag.indexer as indexer
import app.rag.vector_store as vector_store
from app.rag.indexer import index_documents, query_index


class _StubEncoder:
    """Deterministic, offline stand-in for the real sentence-transformers model
    so vector-store tests don't need to download weights or hit the network."""

    def encode(self, texts, convert_to_numpy=True):
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode()).digest()
            vector = np.frombuffer(digest, dtype=np.uint8).astype(float)[:16]
            vectors.append(vector)
        return np.array(vectors)


@pytest.fixture(autouse=True)
def reset_vector_store(monkeypatch):
    monkeypatch.setattr(embeddings, "get_embedding_model", lambda: _StubEncoder())
    monkeypatch.setattr(indexer, "rerank", lambda query, candidates, top_k: candidates[:top_k])
    vector_store._client = None
    vector_store._embedding_fn = None
    vector_store._last_used.clear()
    yield
    vector_store._client = None
    vector_store._embedding_fn = None
    vector_store._last_used.clear()


def test_index_documents_adds_new_chunks():
    docs = [
        {
            "source_id": "PMID:1",
            "text": "A short abstract about hepatotoxicity.",
            "metadata": {"source_id": "PMID:1", "title": "T1", "url": "http://example.com/1"},
        }
    ]
    added = index_documents("session-a", "healthcare", docs)
    assert added == 1


def test_index_documents_dedupes_repeated_source():
    docs = [
        {
            "source_id": "PMID:1",
            "text": "A short abstract about hepatotoxicity.",
            "metadata": {"source_id": "PMID:1", "title": "T1", "url": "http://example.com/1"},
        }
    ]
    first = index_documents("session-b", "healthcare", docs)
    second = index_documents("session-b", "healthcare", docs)
    assert first == 1
    assert second == 0


def test_query_index_returns_hits_with_metadata():
    docs = [
        {
            "source_id": "PMID:2",
            "text": "Cold-chain logistics for vaccine distribution.",
            "metadata": {"source_id": "PMID:2", "title": "Cold chain paper", "url": "http://example.com/2"},
        }
    ]
    index_documents("session-c", "logistics", docs)

    hits = query_index("session-c", "logistics", "vaccine cold chain", top_k=5)

    assert len(hits) == 1
    assert hits[0]["metadata"]["title"] == "Cold chain paper"


def test_query_index_empty_collection_returns_no_hits():
    hits = query_index("session-empty", "logistics", "anything", top_k=5)
    assert hits == []


def test_sessions_and_domains_are_isolated():
    docs_a = [
        {
            "source_id": "PMID:10",
            "text": "Session A document.",
            "metadata": {"source_id": "PMID:10", "title": "A", "url": "http://example.com/a"},
        }
    ]
    docs_b = [
        {
            "source_id": "PMID:11",
            "text": "Session B document.",
            "metadata": {"source_id": "PMID:11", "title": "B", "url": "http://example.com/b"},
        }
    ]
    index_documents("session-x", "healthcare", docs_a)
    index_documents("session-y", "healthcare", docs_b)

    hits_x = query_index("session-x", "healthcare", "document", top_k=5)
    hits_y = query_index("session-y", "healthcare", "document", top_k=5)

    assert {h["metadata"]["title"] for h in hits_x} == {"A"}
    assert {h["metadata"]["title"] for h in hits_y} == {"B"}
