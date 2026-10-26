"""Shuqiao API. Real endpoints arrive with later tickets."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool

from app import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_in_threadpool(auth.init_pool)
    try:
        yield
    finally:
        await run_in_threadpool(auth.close_pool)


app = FastAPI(title="Shuqiao", lifespan=lifespan)

app.include_router(auth.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
