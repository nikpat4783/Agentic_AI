"""Auth: login success/failure, and that protected endpoints reject a
request with no (or an invalid) token. The shared `client` fixture already
has a valid token attached (see conftest.py) for every other test file, so
this file builds its own fresh, unauthenticated TestClient where needed.
"""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_login_succeeds_with_correct_credentials(client):
    resp = client.post("/auth/login", json={"username": "admin", "password": "admin1234"})
    assert resp.status_code == 200
    assert resp.json()["token"]


def test_login_rejects_wrong_password(client):
    resp = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


def test_protected_endpoint_rejects_missing_token():
    from app.main import app

    with TestClient(app) as anon_client:
        resp = anon_client.get("/qa/queue")
        assert resp.status_code == 401


def test_protected_endpoint_rejects_invalid_token():
    from app.main import app

    with TestClient(app) as anon_client:
        anon_client.headers.update({"Authorization": "Bearer not-a-real-token"})
        resp = anon_client.get("/qa/queue")
        assert resp.status_code == 401


def test_health_and_specs_remain_public():
    """`/health` and `/specs` are intentionally not behind auth (see main.py)."""
    from app.main import app

    with TestClient(app) as anon_client:
        assert anon_client.get("/health").status_code == 200
        assert anon_client.get("/specs").status_code == 200
