"""Cross-service Pydantic models — canonical data formats."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Competency Question (shared format per INTERFACE_CONTRACT)
# ------------------------------------------------------------------

class QAQuestion(BaseModel):
    id: str
    question: str
    expected_answers: list[str] = Field(default_factory=list)
    query_type: str = "entity"
    difficulty: int = Field(default=3, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


# ------------------------------------------------------------------
# Gap Report (KGBuilder → OntologyExtender)
# ------------------------------------------------------------------

class GapReport(BaseModel):
    untyped_entities: list[str] = Field(default_factory=list)
    failed_queries: list[str] = Field(default_factory=list)
    low_confidence_answers: list[dict[str, str]] = Field(default_factory=list)
    suggested_new_classes: list[str] = Field(default_factory=list)
    suggested_new_relations: list[str] = Field(default_factory=list)
    coverage_score: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)


# ------------------------------------------------------------------
# TBox Change Request (KGBuilder → OntologyExtender)
# ------------------------------------------------------------------

class TBoxChangeType(str, Enum):
    NEW_CLASS = "tbox_new_class"
    MODIFY_CLASS = "tbox_modify_class"
    HIERARCHY_FIX = "tbox_hierarchy_fix"
    PROPERTY_FIX = "tbox_property_fix"


class TBoxChangeRequest(BaseModel):
    change_type: TBoxChangeType
    review_item_id: str
    reviewer_id: str
    rationale: str
    suggested_changes: dict[str, str] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


# ------------------------------------------------------------------
# Entity / Relation (shared view for explorer)
# ------------------------------------------------------------------

class EntitySummary(BaseModel):
    id: str
    label: str
    entity_type: str
    confidence: float
    description: str = ""


class RelationSummary(BaseModel):
    source_id: str
    target_id: str
    predicate: str
    confidence: float
