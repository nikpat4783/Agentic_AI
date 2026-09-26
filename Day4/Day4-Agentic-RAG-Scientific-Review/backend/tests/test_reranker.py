import pytest

import app.rag.reranker as reranker
from app.rag.reranker import rerank


class _StubCrossEncoder:
    """Deterministic, offline stand-in for the real CrossEncoder so reranker
    tests don't need to download weights or hit the network. Score is simply
    the length of the candidate text, so longer candidates rank first."""

    def predict(self, pairs):
        return [float(len(text)) for _query, text in pairs]


@pytest.fixture(autouse=True)
def stub_reranker_model(monkeypatch):
    monkeypatch.setattr(reranker, "get_reranker_model", lambda: _StubCrossEncoder())
    yield


def test_rerank_sorts_candidates_by_model_score():
    candidates = [
        {"text": "short", "metadata": {"id": 1}},
        {"text": "a much longer piece of text", "metadata": {"id": 2}},
        {"text": "medium length text", "metadata": {"id": 3}},
    ]

    result = rerank("query", candidates, top_k=3)

    assert [c["metadata"]["id"] for c in result] == [2, 3, 1]
    assert all("rerank_score" in c for c in result)


def test_rerank_trims_to_top_k():
    candidates = [
        {"text": "a" * i, "metadata": {"id": i}} for i in range(1, 6)
    ]

    result = rerank("query", candidates, top_k=2)

    assert len(result) == 2
    # highest-scoring (longest) candidates should be kept
    assert [c["metadata"]["id"] for c in result] == [5, 4]


def test_rerank_empty_candidates_returns_empty_without_calling_model(monkeypatch):
    called = False

    def fail_if_called():
        nonlocal called
        called = True
        raise AssertionError("get_reranker_model should not be called for empty candidates")

    monkeypatch.setattr(reranker, "get_reranker_model", fail_if_called)

    result = rerank("query", [], top_k=5)

    assert result == []
    assert called is False
