"""Shuqiao API. Real endpoints arrive with later tickets."""
from fastapi import FastAPI

from app.auth import router as auth_router

app = FastAPI(title="Shuqiao")

app.include_router(auth_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
