"""Shuqiao API. Real endpoints arrive with later tickets."""
import uvicorn

from fastapi import FastAPI

app = FastAPI(title="Shuqiao")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
