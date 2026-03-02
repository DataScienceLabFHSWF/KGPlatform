"""GraphQAAgent FastAPI service — extends existing server with new routes."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the existing GraphQAAgent routes
# from kgrag.api.routes import router as existing_router

from routes.chat import router as chat_router
from routes.explorer import router as explorer_router
from routes.hitl import router as hitl_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: initialize KGRAG orchestrator
    yield


app = FastAPI(
    title="GraphQAAgent API",
    description="Ontology-informed GraphRAG QA with streaming chat",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount existing routes (from the GraphQAAgent repo)
# app.include_router(existing_router, prefix="/api/v1", tags=["qa"])

# New routes
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
app.include_router(explorer_router, prefix="/api/v1", tags=["explorer"])
app.include_router(hitl_router, prefix="/api/v1/hitl", tags=["hitl"])


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "graphqa"}
