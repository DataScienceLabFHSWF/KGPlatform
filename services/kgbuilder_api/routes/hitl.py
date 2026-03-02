"""HITL (Human-in-the-Loop) feedback endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


class GapReportResponse(BaseModel):
    untyped_entities: list[str]
    failed_queries: list[str]
    suggested_new_classes: list[str]
    suggested_new_relations: list[str]
    coverage_score: float
    low_confidence_answers: list[dict[str, str]]


class FeedbackRequest(BaseModel):
    """Feedback from an expert or from GraphQAAgent."""

    review_item_id: str
    reviewer_id: str
    decision: str = Field(description="accepted | rejected | modified | needs_discussion")
    rationale: str
    suggested_changes: dict[str, str] = Field(default_factory=dict)
    new_competency_questions: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class FeedbackResponse(BaseModel):
    status: str
    routed_to: list[str]


class GapDetectRequest(BaseModel):
    """Trigger gap detection from QA feedback."""

    qa_results: list[dict[str, str | float]]


@router.get("/gaps", response_model=GapReportResponse)
async def get_gaps() -> GapReportResponse:
    """Get the latest gap report."""
    # TODO: import GapDetector, run against current KG
    return GapReportResponse(
        untyped_entities=[],
        failed_queries=[],
        suggested_new_classes=[],
        suggested_new_relations=[],
        coverage_score=1.0,
        low_confidence_answers=[],
    )


@router.post("/gaps/detect", response_model=GapReportResponse)
async def detect_gaps(request: GapDetectRequest) -> GapReportResponse:
    """Run gap detection from QA results (called by GraphQAAgent)."""
    from kgbuilder.hitl.config import GapDetectionConfig
    from kgbuilder.hitl.gap_detector import GapDetector

    detector = GapDetector(GapDetectionConfig())
    report = detector.detect_from_qa_feedback(request.qa_results)

    return GapReportResponse(
        untyped_entities=report.untyped_entities,
        failed_queries=report.failed_queries,
        suggested_new_classes=report.suggested_new_classes,
        suggested_new_relations=report.suggested_new_relations,
        coverage_score=report.coverage_score,
        low_confidence_answers=report.low_confidence_answers,
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """Submit expert feedback — routes to OntologyExtender or KGBuilder."""
    # TODO: import FeedbackIngester, process and route
    return FeedbackResponse(
        status="accepted",
        routed_to=["kg_builder"],
    )
