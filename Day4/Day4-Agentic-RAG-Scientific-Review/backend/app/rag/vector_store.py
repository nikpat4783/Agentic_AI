import asyncio
import time

import chromadb

from app.rag.embeddings import SentenceTransformerEmbeddingFunction

_client = None
_embedding_fn = None
_last_used: dict[str, float] = {}
_IDLE_TTL_SECONDS = 2 * 60 * 60


def get_client():
    global _client, _embedding_fn
    if _client is None:
        _client = chromadb.EphemeralClient()
        _embedding_fn = SentenceTransformerEmbeddingFunction()
    return _client


def get_collection_name(session_id: str, domain_id: str) -> str:
    return f"sess_{session_id}_{domain_id}"


def get_or_create_collection(session_id: str, domain_id: str):
    client = get_client()
    name = get_collection_name(session_id, domain_id)
    collection = client.get_or_create_collection(name=name, embedding_function=_embedding_fn)
    _last_used[name] = time.time()
    return collection


async def purge_idle_collections_loop():
    """Background task: periodically drop collections idle longer than the TTL,
    bounding memory growth in a long-running dev server."""
    while True:
        await asyncio.sleep(600)
        now = time.time()
        client = get_client()
        stale = [name for name, ts in _last_used.items() if now - ts > _IDLE_TTL_SECONDS]
        for name in stale:
            try:
                client.delete_collection(name)
            except Exception:
                pass
            _last_used.pop(name, None)
