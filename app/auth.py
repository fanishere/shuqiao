"""Authentication: signup, login, refresh, logout.

User storage is in-memory (no database yet); a later ticket replaces it.
"""
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException
from pwdlib import PasswordHash

SECRET_KEY = os.environ.get(
    "SHUQIAO_SECRET_KEY", "dev-only-secret-key-change-me-0123456789ab"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_TTL = timedelta(minutes=15)

password_hash = PasswordHash.recommended()

# Registry of users keyed by username.
users: dict[str, str] = {}  # username -> argon2 hash
# Opaque refresh tokens, stored server-side so logout can revoke them.
refresh_tokens: dict[str, str] = {}  # token -> username

router = APIRouter(prefix="/auth")


@dataclass
class Credentials:
    username: str
    password: str


def _issue_access_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": username, "exp": now + ACCESS_TOKEN_TTL, "iat": now},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def _issue_refresh_token(username: str) -> str:
    token = secrets.token_urlsafe(32)
    refresh_tokens[token] = username
    return token


@router.post("/signup", status_code=201)
def signup(creds: Credentials) -> dict[str, str]:
    if creds.username in users:
        raise HTTPException(status_code=409, detail="username already taken")
    users[creds.username] = password_hash.hash(creds.password)
    return {"username": creds.username}


@router.post("/login")
def login(creds: Credentials) -> dict[str, str]:
    stored = users.get(creds.username)
    if stored is None or not password_hash.verify(creds.password, stored):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {
        "access_token": _issue_access_token(creds.username),
        "refresh_token": _issue_refresh_token(creds.username),
        "token_type": "bearer",
    }


@router.post("/refresh")
def refresh(request: dict[str, str]) -> dict[str, str]:
    token = request.get("refresh_token", "")
    username = refresh_tokens.get(token)
    if username is None:
        raise HTTPException(status_code=401, detail="invalid refresh token")
    return {
        "access_token": _issue_access_token(username),
        "token_type": "bearer",
    }


@router.post("/logout", status_code=204)
def logout(request: dict[str, str]) -> None:
    refresh_tokens.pop(request.get("refresh_token", ""), None)
