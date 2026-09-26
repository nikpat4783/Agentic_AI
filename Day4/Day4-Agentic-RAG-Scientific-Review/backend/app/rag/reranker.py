_model = None


def get_reranker_model():
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder

        _model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _model


def rerank(query: str, candidates: list[dict], top_k: int) -> list[dict]:
    """candidates: list of {"text": ..., "metadata": ...} dicts (indexer.py's
    hit shape). Returns the top_k candidates sorted by cross-encoder relevance
    to `query`, each with an added "rerank_score" float field. Returns []
    unchanged if candidates is empty."""
    if not candidates:
        return []

    model = get_reranker_model()
    scores = model.predict([(query, c["text"]) for c in candidates])

    scored = [
        {**candidate, "rerank_score": float(score)}
        for candidate, score in zip(candidates, scores)
    ]
    scored.sort(key=lambda c: c["rerank_score"], reverse=True)
    return scored[:top_k]
