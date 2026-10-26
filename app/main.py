"""Shuqiao API. Real endpoints arrive with later tickets."""
from fastapi import FastAPI

app = FastAPI(title="Shuqiao")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
