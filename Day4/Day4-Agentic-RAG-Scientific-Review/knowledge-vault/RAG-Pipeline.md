#rag #backend

# RAG Pipeline

`backend/app/rag/` — per-session, in-memory retrieval-augmented generation.

## Vector store

`backend/app/rag/vector_store.py` — `chromadb.EphemeralClient()`, **in
memory, not persisted to disk**. Collections are named
`sess_{session_id}_{domain_id}` and purged after 2h idle by a background
loop started in `main.py`'s lifespan. This means restarting the backend
wipes all indexed documents — expected for a BYOK demo, but worth knowing
before treating this as a durable knowledge base.

## Indexing

`backend/app/rag/indexer.py` — `index_documents` chunks source text via
`chunking.chunk_text` (`chunk_size=800`, `overlap=120`, sentence-aware) and
upserts into Chroma, deduping by `f"{source_id}_{idx}"`. **Known gap**:
dedup only skips IDs already present, it never removes stale trailing
chunks when a source is re-indexed with *fewer* chunks than before — old
content can resurface in retrieval (`reports/2026-09-19-test-and-review.md`).

## Embeddings & reranking

- Embedding model: `sentence-transformers`, `all-MiniLM-L6-v2` by default
  (`EMBEDDING_MODEL_NAME` setting), wired in as a custom Chroma
  `EmbeddingFunction` (`backend/app/rag/embeddings.py`).
- Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2` via
  `sentence_transformers.CrossEncoder` (`backend/app/rag/reranker.py`).
  `query_index` over-fetches (`top_k*4`) then reranks down to `top_k`.

Both models are warmed during `main.py`'s `lifespan` startup so the first
real request isn't slow.

## Where this shows up in [[Observability]]

Retrieval itself isn't a network call, so it won't show as an HTTPX span —
but it happens inside an `agent.tool_iteration` span (see
[[Agent-Orchestrator]]) when the `retrieve_from_index` tool is called, so
its wall-clock cost is still visible in the trace waterfall in Tempo.
