"""KG export endpoints."""

from __future__ import annotations

from enum import Enum

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

router = APIRouter()


class ExportFormat(str, Enum):
    JSON_LD = "json-ld"
    TURTLE = "turtle"
    CYPHER = "cypher"
    GRAPHML = "graphml"
    KGBUILDER_JSON = "kgbuilder-json"


class ExportRequest(BaseModel):
    format: ExportFormat = ExportFormat.KGBUILDER_JSON
    include_metadata: bool = True
    min_confidence: float = 0.0


@router.post("/export")
async def export_kg(request: ExportRequest) -> Response:
    """Export the KG in the requested format."""
    # TODO: import and run kgbuilder.storage.export
    return Response(
        content="{}",
        media_type="application/json",
    )
