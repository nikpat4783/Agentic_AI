"""Single hardcoded demo admin account - not a real user system.

Tokens are opaque, random, and held only in an in-memory set for this
process's lifetime (cleared on restart, never written to disk) - the same
"never persisted" posture this codebase already applies to the BYOK LLM
key. This is intentionally not JWT/sessions/a user table: there is exactly
one account, and the point is to gate the demo UI, not to model real
multi-user auth.
"""
from __future__ import annotations

import secrets

from fastapi import Header, HTTPException

from app.config import settings

_active_tokens: set[str] = set()


def verify_credentials(username: str, password: str) -> bool:
    return username == settings.admin_username and password == settings.admin_password


def issue_token() -> str:
    token = secrets.token_urlsafe(32)
    _active_tokens.add(token)
    return token


def revoke_token(token: str) -> None:
    _active_tokens.discard(token)


def require_auth(authorization: str | None = Header(default=None)) -> str:
    """FastAPI dependency: raises 401 unless a valid `Bearer <token>` header
    (from a prior successful /auth/login) is present."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="not authenticated")
    token = authorization.removeprefix("Bearer ").strip()
    if token not in _active_tokens:
        raise HTTPException(status_code=401, detail="not authenticated")
    return token
