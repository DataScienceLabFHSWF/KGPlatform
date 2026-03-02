"""Validation endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ValidationRequest(BaseModel):
    checkpoint_path: str | None = None
    run_shacl: bool = True
    run_rules: bool = True
    run_consistency: bool = True


class ValidationResponse(BaseModel):
    passed: bool
    total_checks: int
    pass_rate: float
    violations: list[dict]


@router.post("/validate", response_model=ValidationResponse)
async def validate_kg(request: ValidationRequest) -> ValidationResponse:
    """Run SHACL + semantic rule validation on the current KG."""
    # TODO: import and run kgbuilder.validation pipeline
    return ValidationResponse(
        passed=True,
        total_checks=0,
        pass_rate=1.0,
        violations=[],
    )
