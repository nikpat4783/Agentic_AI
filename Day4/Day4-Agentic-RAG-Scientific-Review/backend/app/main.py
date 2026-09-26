import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import Base, engine
from app.observability import setup_observability
from app.rag.embeddings import get_embedding_model
from app.rag.reranker import get_reranker_model
from app.rag.vector_store import purge_idle_collections_loop
from app.routers import auth, domains, research
from app.utils.logging import configure_logging

logging.basicConfig(level=logging.INFO)
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    try:
        get_embedding_model()  # warm the embedding model once, not on the first request
    except Exception:
        logging.getLogger(__name__).warning(
            "Could not pre-warm the embedding model; it will load lazily on first use.",
            exc_info=True,
        )
    try:
        get_reranker_model()  # warm the reranker model once, not on the first request
    except Exception:
        logging.getLogger(__name__).warning(
            "Could not pre-warm the reranker model; it will load lazily on first use.",
            exc_info=True,
        )
    purge_task = asyncio.create_task(purge_idle_collections_loop())
    try:
        yield
    finally:
        purge_task.cancel()


app = FastAPI(title="Agentic RAG for Scientific Literature & Drug-Discovery Intelligence", lifespan=lifespan)

setup_observability(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(domains.router)
app.include_router(research.router)


@app.get("/health")
def health():
    return {"status": "ok"}
