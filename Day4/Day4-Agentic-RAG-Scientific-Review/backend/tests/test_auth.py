def _register(client, username="alice", password="supersecret1"):
    return client.post("/auth/register", json={"username": username, "password": password})


def test_register_creates_user_with_hashed_password(client):
    response = _register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_username_rejected(client):
    _register(client)
    response = _register(client)
    assert response.status_code == 400


def test_login_success_returns_token(client):
    _register(client)
    response = client.post("/auth/login", json={"username": "alice", "password": "supersecret1"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_wrong_password_rejected(client):
    _register(client)
    response = client.post("/auth/login", json={"username": "alice", "password": "wrongpassword"})
    assert response.status_code == 401


def test_me_requires_valid_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user_with_valid_token(client):
    _register(client)
    login = client.post("/auth/login", json={"username": "alice", "password": "supersecret1"})
    token = login.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_me_rejects_garbage_token(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
