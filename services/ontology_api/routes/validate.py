"""SHACL validation endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SHACLValidationRequest(BaseModel):
    shapes_path: str | None = None
    data_graph_path: str | None = None


class SHACLViolation(BaseModel):
    focus_node: str
    path: str
    message: str
    severity: str


class SHACLValidationResponse(BaseModel):
    conforms: bool
    violations: list[SHACLViolation]
    total_shapes: int


@router.post("/validate/shacl", response_model=SHACLValidationResponse)
async def validate_shacl(request: SHACLValidationRequest) -> SHACLValidationResponse:
    """Validate an RDF graph against SHACL shapes."""
    # TODO: use pyshacl
    return SHACLValidationResponse(
        conforms=True,
        violations=[],
        total_shapes=0,
    )
