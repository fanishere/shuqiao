"""Authentication: signup, login, refresh, logout.

Users and refresh tokens persist to Postgres; refresh tokens are stored
as sha256 hashes so a database dump cannot replay them. Deferred until a
later ticket: authenticated logout, access-token revocation, iss/aud/jti
claims, and per-user token-count caps.
"""
import hashlib
import logging
import os
import secrets
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException
from pwdlib import PasswordHash
from psycopg import errors
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, Field

logger = logging.getLogger("shuqiao.auth")

_env_key = os.environ.get("SHUQIAO_SECRET_KEY")
if _env_key:
    SECRET_KEY = _env_key
else:
    SECRET_KEY = secrets.token_urlsafe(32)
    logger.warning(
        "SHUQIAO_SECRET_KEY not set; using a random per-process key, so "
        "issued tokens will not validate after a restart"
    )

def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    return "postgresql://shuqiao:%s@localhost:5432/shuqiao" % os.environ.get(
        "POSTGRES_PASSWORD", ""
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_TTL = timedelta(minutes=15)
REFRESH_TOKEN_TTL = timedelta(days=7)

password_hash = PasswordHash.recommended()
# Verified against when the username is unknown, so login costs one argon2
# op on both paths and response timing does not reveal registered usernames.
_dummy_hash = password_hash.hash(secrets.token_urlsafe(16))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS refresh_tokens (
    token_hash TEXT PRIMARY KEY,
    username TEXT NOT NULL REFERENCES users (username) ON DELETE CASCADE,
    issued_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);
"""

router = APIRouter(prefix="/auth")

_pool: ConnectionPool | None = None


def init_pool() -> None:
    global _pool
    _pool = ConnectionPool(_database_url(), open=True, check=ConnectionPool.check_connection)
    with _pool.connection() as conn:
        conn.execute(_SCHEMA)


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def db():
    if _pool is None:
        raise RuntimeError("database not initialized; call init_pool at startup")
    with _pool.connection() as conn:
        yield conn


class Credentials(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=1024)


class RefreshRequest(BaseModel):
    refresh_token: str


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _issue_access_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": username, "exp": now + ACCESS_TOKEN_TTL, "iat": now},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def _issue_refresh_token(conn, username: str) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    conn.execute(
        "INSERT INTO refresh_tokens (token_hash, username, issued_at, expires_at)"
        " VALUES (%s, %s, %s, %s)",
        (_token_hash(token), username, now, now + REFRESH_TOKEN_TTL),
    )
    return token


@router.post("/signup", status_code=201)
def signup(creds: Credentials) -> dict[str, str]:
    with db() as conn:
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (creds.username, password_hash.hash(creds.password)),
            )
        except errors.UniqueViolation:
            raise HTTPException(status_code=409, detail="username already taken")
    return {"username": creds.username}


@router.post("/login")
def login(creds: Credentials) -> dict[str, str]:
    with db() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE username = %s", (creds.username,)
        ).fetchone()
        valid = (
            password_hash.verify(creds.password, row[0])
            if row is not None
            else password_hash.verify(creds.password, _dummy_hash)
        )
        if not valid:
            raise HTTPException(status_code=401, detail="invalid credentials")
        return {
            "access_token": _issue_access_token(creds.username),
            "refresh_token": _issue_refresh_token(conn, creds.username),
            "token_type": "bearer",
        }


@router.post("/refresh")
def refresh(request: RefreshRequest) -> dict[str, str]:
    with db() as conn:
        # DELETE ... RETURNING consumes the old token atomically; a reused
        # token finds nothing and gets 401.
        row = conn.execute(
            "DELETE FROM refresh_tokens WHERE token_hash = %s"
            " AND expires_at > now() RETURNING username",
            (_token_hash(request.refresh_token),),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="invalid refresh token")
        return {
            "access_token": _issue_access_token(row[0]),
            "refresh_token": _issue_refresh_token(conn, row[0]),
            "token_type": "bearer",
        }


@router.post("/logout", status_code=204)
def logout(request: RefreshRequest) -> None:
    with db() as conn:
        conn.execute(
            "DELETE FROM refresh_tokens WHERE token_hash = %s",
            (_token_hash(request.refresh_token),),
        )
