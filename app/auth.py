"""Authentication: signup, login, refresh, logout.

User storage is in-memory (no database yet); a later ticket replaces it.
Deferred until that storage ticket: authenticated logout, access-token
revocation, iss/aud/jti claims, and per-user token-count caps.
"""
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException
from pwdlib import PasswordHash
from pydantic import BaseModel, Field

logger = logging.getLogger("shuqiao.auth")

_env_key = os.environ.get("SHUQIAO_SECRET_KEY")
if _env_key is not None:
    SECRET_KEY = _env_key
else:
    SECRET_KEY = secrets.token_urlsafe(32)
    logger.warning(
        "SHUQIAO_SECRET_KEY not set; using a random per-process key, so "
        "issued tokens will not validate after a restart"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_TTL = timedelta(minutes=15)
REFRESH_TOKEN_TTL = timedelta(days=7)

password_hash = PasswordHash.recommended()
# Verified against when the username is unknown, so login costs one argon2
# op on both paths and response timing does not reveal registered usernames.
_dummy_hash = password_hash.hash(secrets.token_urlsafe(16))

# Registry of users keyed by username.
users: dict[str, str] = {}  # username -> argon2 hash
# Opaque refresh tokens, stored server-side so logout can revoke them.
refresh_tokens: dict[str, tuple[str, datetime]] = {}  # token -> (username, issued_at)

router = APIRouter(prefix="/auth")


class Credentials(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=1024)


class RefreshRequest(BaseModel):
    refresh_token: str


def _issue_access_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": username, "exp": now + ACCESS_TOKEN_TTL, "iat": now},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def _issue_refresh_token(username: str) -> str:
    token = secrets.token_urlsafe(32)
    refresh_tokens[token] = (username, datetime.now(timezone.utc))
    return token


def _lookup_refresh(token: str) -> str | None:
    entry = refresh_tokens.get(token)
    if entry is None:
        return None
    username, issued_at = entry
    if datetime.now(timezone.utc) - issued_at > REFRESH_TOKEN_TTL:
        del refresh_tokens[token]
        return None
    return username


@router.post("/signup", status_code=201)
def signup(creds: Credentials) -> dict[str, str]:
    if creds.username in users:
        raise HTTPException(status_code=409, detail="username already taken")
    users[creds.username] = password_hash.hash(creds.password)
    return {"username": creds.username}


@router.post("/login")
def login(creds: Credentials) -> dict[str, str]:
    stored = users.get(creds.username)
    valid = (
        password_hash.verify(creds.password, stored)
        if stored is not None
        else password_hash.verify(creds.password, _dummy_hash)
    )
    if not valid:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {
        "access_token": _issue_access_token(creds.username),
        "refresh_token": _issue_refresh_token(creds.username),
        "token_type": "bearer",
    }


@router.post("/refresh")
def refresh(request: RefreshRequest) -> dict[str, str]:
    username = _lookup_refresh(request.refresh_token)
    if username is None:
        raise HTTPException(status_code=401, detail="invalid refresh token")
    del refresh_tokens[request.refresh_token]
    return {
        "access_token": _issue_access_token(username),
        "refresh_token": _issue_refresh_token(username),
        "token_type": "bearer",
    }


@router.post("/logout", status_code=204)
def logout(request: RefreshRequest) -> None:
    refresh_tokens.pop(request.refresh_token, None)
