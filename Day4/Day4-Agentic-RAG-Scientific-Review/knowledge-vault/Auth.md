#auth #backend

# Auth

JWT-based, via `backend/app/routers/auth.py` + `backend/app/security.py`.

- `POST /auth/register` / `POST /auth/login` — both take
  `{"username": str (3-64 chars), "password": str (8-128 chars)}`
  (`UserCreate` schema).
- Login response: `{"access_token": "<jwt>", "token_type": "bearer"}`
  (`Token` schema).
- Protected routes depend on `get_current_user`
  (`OAuth2PasswordBearer(tokenUrl="/auth/login")`, `python-jose` for JWT
  verification, `bcrypt` for password hashing) — send
  `Authorization: Bearer <access_token>`.
- `GET /domains` and `POST /research/stream` both require this; the latter
  additionally requires the per-request `X-Groq-Key` header (see
  [[Backend]] — the app never stores a Groq key server-side).

## Known issues

- `[P1]` bcrypt hard-fails above 72 bytes with no try/except in the auth
  router — a legitimate 80+ character password 500s instead of a clean 400
  (`backend/app/security.py`, `reports/2026-09-19-test-and-review.md`).
- `[P2]` `session_id` from the request body is never bound to the
  authenticated user — it's used directly to pick the Chroma collection, so
  a leaked `session_id` (a UUID, low likelihood) could let another user
  read that session's indexed documents (`backend/app/routers/research.py`).

## Load-testing implication

[[Load-Testing]] scripts must register + login before hitting any
protected endpoint — see `loadtest/scripts/smoke.js`'s `setup()`.
