"""POST /auth/login, POST /auth/logout."""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from app.auth import issue_token, revoke_token, verify_credentials
from app.schemas import LoginRequest, LoginResponse, LogoutResponse

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    if not verify_credentials(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return LoginResponse(token=issue_token())


@router.post("/auth/logout", response_model=LogoutResponse)
def logout(authorization: str | None = Header(default=None)) -> LogoutResponse:
    if authorization and authorization.startswith("Bearer "):
        revoke_token(authorization.removeprefix("Bearer ").strip())
    return LogoutResponse(status="logged_out")
