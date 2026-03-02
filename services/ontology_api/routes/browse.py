"""Ontology browsing endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class OntologyClass(BaseModel):
    uri: str
    label: str
    description: str
    parent_uri: str | None = None
    properties: list[dict[str, str]]
    examples: list[str] = []


class OntologyRelation(BaseModel):
    uri: str
    label: str
    description: str
    domain: list[str]
    range: list[str]


class OntologySummary(BaseModel):
    classes: list[OntologyClass]
    relations: list[OntologyRelation]
    hierarchy: list[dict[str, str]]
    class_count: int
    relation_count: int


@router.get("/summary", response_model=OntologySummary)
async def get_ontology_summary() -> OntologySummary:
    """Get full ontology summary (classes, relations, hierarchy)."""
    # TODO: query Fuseki or parse OWL file
    return OntologySummary(
        classes=[],
        relations=[],
        hierarchy=[],
        class_count=0,
        relation_count=0,
    )


@router.get("/classes", response_model=list[OntologyClass])
async def get_classes() -> list[OntologyClass]:
    """List all ontology classes."""
    return []


@router.get("/relations", response_model=list[OntologyRelation])
async def get_relations() -> list[OntologyRelation]:
    """List all ontology relations."""
    return []
