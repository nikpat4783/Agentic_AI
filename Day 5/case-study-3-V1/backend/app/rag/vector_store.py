"""Chroma persistent collection over app/rag/specs/*.md.

Idempotent build: on startup, `build_index()` skips re-indexing if the
collection already holds the expected number of documents (one per spec
file), so repeated app restarts don't redundantly re-embed.
"""
from __future__ import annotations

import glob
import os
from functools import lru_cache

from app.config import settings
from app.rag.embeddings import embed_texts


@lru_cache(maxsize=1)
def get_client():
    import chromadb

    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)


def get_collection():
    client = get_client()
    return client.get_or_create_collection(name=settings.chroma_collection_name)


def _spec_files() -> list[str]:
    return sorted(glob.glob(os.path.join(settings.specs_dir, "*.md")))


def build_index(force: bool = False) -> int:
    """Build (or confirm) the spec index. Returns the number of docs indexed."""
    collection = get_collection()
    spec_files = _spec_files()

    if not force and collection.count() == len(spec_files) and spec_files:
        return collection.count()

    if not spec_files:
        return 0

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []
    for path in spec_files:
        element_name = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        ids.append(element_name)
        documents.append(text)
        metadatas.append({"element_name": element_name, "path": path})

    embeddings = embed_texts(documents)
    # upsert-by-recreate: rely on Chroma's add() with matching ids being a
    # no-op-safe overwrite via delete+add for idempotent rebuilds.
    existing = set(collection.get(ids=ids).get("ids", []))
    if existing:
        collection.delete(ids=list(existing))
    collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
    return collection.count()
