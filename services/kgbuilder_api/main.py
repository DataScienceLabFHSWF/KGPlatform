"""KGBuilder FastAPI service — wraps the KG construction pipeline."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.build import router as build_router
from routes.validate import router as validate_router
from routes.export import router as export_router
from routes.hitl import router as hitl_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: verify connections to Neo4j, Qdrant, Fuseki
    # (lazy init — services may still be starting)
    yield
    # Shutdown: cleanup


app = FastAPI(
    title="KGBuilder API",
    description="Ontology-driven Knowledge Graph construction service",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(build_router, prefix="/api/v1", tags=["build"])
app.include_router(validate_router, prefix="/api/v1", tags=["validate"])
app.include_router(export_router, prefix="/api/v1", tags=["export"])
app.include_router(hitl_router, prefix="/api/v1/hitl", tags=["hitl"])


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "kgbuilder"}
