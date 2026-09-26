"""FastAPI app entrypoint: CORS, startup (create tables, seed specs, warm
the embedding model + RAG index), OTel instrumentation, and router wiring.
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.auth import require_auth
from app.config import settings
from app.db import get_db, init_db, seed_data_element_specs
from app.metrics import record_request
from app.observability import instrument_app
from app.routers import auth, documents, extraction, qa, submissions
from app.schemas import SpecOut

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_data_element_specs()

    # Warm the embedding model + build/confirm the RAG index. Never let a
    # RAG/embedding hiccup prevent the app from starting - degrade to the
    # retriever's own file-read fallback (see app/rag/retriever.py).
    try:
        from app.rag.vector_store import build_index

        count = build_index()
        logger.info("RAG spec index ready (%d docs)", count)
    except Exception as exc:
        logger.warning("RAG index build skipped/failed at startup: %s", exc)

    yield


app = FastAPI(title="Carta Extraction Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

instrument_app(app)


@app.middleware("http")
async def record_request_metrics(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    route = request.scope.get("route")
    route_path = route.path if route is not None else request.url.path
    record_request(route_path, request.method, response.status_code, duration)
    return response


# /auth/login and /auth/logout are the only public (unauthenticated) real
# endpoints besides /health and /specs below. Everything that touches
# documents/extraction/QA/submissions requires a valid session token from a
# prior login - protected at include_router() level so the router modules
# themselves stay unaware of auth (no per-file changes needed).
app.include_router(auth.router)
app.include_router(documents.router, dependencies=[Depends(require_auth)])
app.include_router(extraction.router, dependencies=[Depends(require_auth)])
app.include_router(qa.router, dependencies=[Depends(require_auth)])
app.include_router(submissions.router, dependencies=[Depends(require_auth)])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/specs", response_model=list[SpecOut])
def list_specs(db: Session = Depends(get_db)) -> list[SpecOut]:
    from app.models import DataElementSpec

    specs = db.query(DataElementSpec).all()
    return [
        SpecOut(
            element_name=s.element_name,
            doc_type=s.doc_type,
            strategy=s.strategy,
            requires_llm=s.requires_llm,
            threshold=s.threshold,
        )
        for s in specs
    ]
