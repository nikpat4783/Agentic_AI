"""Shared pytest fixtures.

Sets env vars for an isolated temp SQLite DB + Chroma dir *before* any
`app.*` module is imported (env vars are read once, at import time, in
app/config.py), then exposes a session-scoped TestClient that runs the
app's real lifespan (create tables, seed DataElementSpec rows, build the
RAG index against the real spec files / real sentence-transformers model -
only the LLM HTTP call itself is mocked in individual tests, never the RAG
or DB layers).
"""
from __future__ import annotations

import os
import tempfile

_TMP_DIR = tempfile.mkdtemp(prefix="carta_backend_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DIR}/test_app.db"
os.environ["CHROMA_PERSIST_DIR"] = os.path.join(_TMP_DIR, "chroma_data")
os.environ["CHROMA_COLLECTION_NAME"] = "data_element_specs_test"
os.environ["OTEL_ENABLED"] = "false"
os.environ.setdefault("CORS_ORIGIN", "http://localhost:5174")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session")
def client():
    from app.main import app

    with TestClient(app) as test_client:
        # Log in once and attach the token to every request this client
        # makes by default (httpx.Client.headers merges into each call) so
        # existing tests don't need to thread an Authorization header
        # through every client.post/get call individually.
        login = test_client.post("/auth/login", json={"username": "admin", "password": "admin1234"})
        token = login.json()["token"]
        test_client.headers.update({"Authorization": f"Bearer {token}"})
        yield test_client


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def read_fixture(name: str) -> str:
    with open(os.path.join(FIXTURES_DIR, name), encoding="utf-8") as fh:
        return fh.read()
