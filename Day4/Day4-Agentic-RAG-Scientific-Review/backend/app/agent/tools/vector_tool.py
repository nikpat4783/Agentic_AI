from app.rag.indexer import query_index


async def retrieve_from_index(session_id: str, domain_id: str, query: str, top_k: int = 5) -> dict:
    """Query the session's vector store built from prior search results."""
    try:
        hits = query_index(session_id, domain_id, query, top_k=top_k)
        return {"results": hits}
    except Exception as exc:
        return {"error": f"Index retrieval failed: {exc}"}
