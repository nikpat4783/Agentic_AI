from app.rag.chunking import chunk_text
from app.rag.reranker import rerank
from app.rag.vector_store import get_or_create_collection


def index_documents(session_id: str, domain_id: str, docs: list[dict]) -> int:
    """Chunk + upsert docs into the session's collection, deduping by source_id
    so repeated/overlapping searches don't duplicate chunks. Each doc must have
    'source_id' (e.g. 'PMID:12345' or 'arXiv:2101.00001'), 'text', and 'metadata'.
    Returns the number of new chunks added.
    """
    collection = get_or_create_collection(session_id, domain_id)

    existing = collection.get(include=[])
    existing_ids = set(existing.get("ids", []))

    new_docs, new_ids, new_metadatas = [], [], []
    for doc in docs:
        chunks = chunk_text(doc["text"])
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{doc['source_id']}_{idx}"
            if chunk_id in existing_ids:
                continue
            new_docs.append(chunk)
            new_ids.append(chunk_id)
            new_metadatas.append(doc["metadata"])

    if new_docs:
        collection.add(documents=new_docs, ids=new_ids, metadatas=new_metadatas)
    return len(new_docs)


def query_index(session_id: str, domain_id: str, query: str, top_k: int = 5) -> list[dict]:
    collection = get_or_create_collection(session_id, domain_id)
    if collection.count() == 0:
        return []

    fetch_k = min(top_k * 4, collection.count())
    result = collection.query(query_texts=[query], n_results=fetch_k)
    hits = []
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    for text, metadata in zip(documents, metadatas):
        hits.append({"text": text, "metadata": metadata})
    return rerank(query, hits, top_k)
