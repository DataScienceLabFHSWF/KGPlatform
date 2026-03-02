"""Ontology extension endpoints — process TBox change requests."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class TBoxChangeRequest(BaseModel):
    """Request from KGBuilder's HITL module to extend the ontology."""

    change_type: str = Field(
        description="tbox_new_class | tbox_modify_class | tbox_hierarchy_fix | tbox_property_fix"
    )
    review_item_id: str
    reviewer_id: str
    rationale: str
    suggested_changes: dict[str, str] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class TBoxChangeResponse(BaseModel):
    status: str
    change_id: str
    changes_applied: list[str]
    new_ontology_version: str | None = None


@router.post("/extend", response_model=TBoxChangeResponse)
async def extend_ontology(request: TBoxChangeRequest) -> TBoxChangeResponse:
    """Apply a TBox change (new class, hierarchy fix, etc.)."""
    # TODO: import OntologyExtender logic
    return TBoxChangeResponse(
        status="accepted",
        change_id=request.review_item_id,
        changes_applied=[request.change_type],
    )


class BulkExtendRequest(BaseModel):
    changes: list[TBoxChangeRequest]


@router.post("/extend/bulk", response_model=list[TBoxChangeResponse])
async def extend_ontology_bulk(request: BulkExtendRequest) -> list[TBoxChangeResponse]:
    """Apply multiple TBox changes in batch."""
    results = []
    for change in request.changes:
        results.append(TBoxChangeResponse(
            status="accepted",
            change_id=change.review_item_id,
            changes_applied=[change.change_type],
        ))
    return results
