"""OntologyExtender FastAPI service."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.extend import router as extend_router
from routes.browse import router as browse_router
from routes.validate import router as validate_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(
    title="OntologyExtender API",
    description="Human-in-the-loop ontology extension service",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(extend_router, prefix="/api/v1", tags=["extend"])
app.include_router(browse_router, prefix="/api/v1/ontology", tags=["browse"])
app.include_router(validate_router, prefix="/api/v1", tags=["validate"])


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ontology-extender"}
