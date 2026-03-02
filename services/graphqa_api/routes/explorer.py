"""KG and ontology explorer endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class EntityInfo(BaseModel):
    id: str
    label: str
    entity_type: str
    confidence: float
    description: str
    neighbors: list[dict]


class SubgraphResponse(BaseModel):
    nodes: list[dict]
    edges: list[dict]


@router.get("/kg/entity/{entity_id}", response_model=EntityInfo)
async def get_entity(entity_id: str) -> EntityInfo:
    """Get entity details with neighbors."""
    # TODO: query Neo4j
    return EntityInfo(
        id=entity_id,
        label="",
        entity_type="",
        confidence=0.0,
        description="",
        neighbors=[],
    )


@router.get("/kg/subgraph", response_model=SubgraphResponse)
async def get_subgraph(
    center_id: str,
    depth: int = 1,
) -> SubgraphResponse:
    """Get subgraph around an entity."""
    # TODO: query Neo4j
    return SubgraphResponse(nodes=[], edges=[])


@router.get("/kg/search")
async def search_entities(query: str, limit: int = 10) -> list[dict]:
    """Search entities by label (fuzzy)."""
    # TODO: query Qdrant or Neo4j full-text index
    return []
