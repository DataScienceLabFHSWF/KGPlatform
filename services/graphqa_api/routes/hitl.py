"""HITL integration — report low-confidence answers to KGBuilder."""

from __future__ import annotations

import os

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()

KGBUILDER_API_URL = os.getenv("KGBUILDER_API_URL", "http://kgbuilder-api:8001")


class LowConfidenceReport(BaseModel):
    """Batch of QA results to report for gap detection."""

    qa_results: list[dict[str, str | float]]


class ReportResponse(BaseModel):
    status: str
    gaps_detected: int
    suggested_classes: list[str]


@router.post("/report-low-confidence", response_model=ReportResponse)
async def report_low_confidence(request: LowConfidenceReport) -> ReportResponse:
    """Report low-confidence QA answers to KGBuilder for gap detection.

    This triggers the HITL feedback loop:
    GraphQAAgent → KGBuilder (gap detection) → OntologyExtender (if needed)
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{KGBUILDER_API_URL}/api/v1/hitl/gaps/detect",
                json={"qa_results": request.qa_results},
            )
            resp.raise_for_status()
            data = resp.json()
            return ReportResponse(
                status="reported",
                gaps_detected=len(data.get("suggested_new_classes", [])),
                suggested_classes=data.get("suggested_new_classes", []),
            )
        except httpx.HTTPError:
            return ReportResponse(
                status="kgbuilder_unreachable",
                gaps_detected=0,
                suggested_classes=[],
            )
