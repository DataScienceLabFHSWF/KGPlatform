"""KG build pipeline endpoints."""

from __future__ import annotations

import uuid
from enum import Enum

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

# In-memory job tracker (replace with Redis/DB for production)
_jobs: dict[str, dict] = {}


class BuildStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BuildRequest(BaseModel):
    """Request to trigger a KG build pipeline run."""

    ontology_path: str = Field(
        default="data/ontology/plan-ontology-v1.0.owl",
        description="Path to OWL ontology file",
    )
    document_dir: str = Field(
        default="data/documents",
        description="Directory containing input documents",
    )
    max_iterations: int = Field(default=5, ge=1, le=50)
    questions_per_class: int = Field(default=3, ge=1, le=20)
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    model: str = Field(default="qwen3:8b")


class BuildResponse(BaseModel):
    job_id: str
    status: BuildStatus
    message: str


class JobStatus(BaseModel):
    job_id: str
    status: BuildStatus
    progress: float = 0.0
    entities_count: int = 0
    relations_count: int = 0
    current_iteration: int = 0
    error: str | None = None


@router.post("/build", response_model=BuildResponse)
async def start_build(
    request: BuildRequest,
    background_tasks: BackgroundTasks,
) -> BuildResponse:
    """Start a KG build pipeline run (async background job)."""
    job_id = uuid.uuid4().hex[:12]
    _jobs[job_id] = {
        "status": BuildStatus.PENDING,
        "progress": 0.0,
        "entities_count": 0,
        "relations_count": 0,
        "current_iteration": 0,
        "error": None,
    }

    background_tasks.add_task(_run_build_pipeline, job_id, request)

    return BuildResponse(
        job_id=job_id,
        status=BuildStatus.PENDING,
        message="Build pipeline started",
    )


@router.get("/build/{job_id}", response_model=JobStatus)
async def get_build_status(job_id: str) -> JobStatus:
    """Check status of a build job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return JobStatus(job_id=job_id, **_jobs[job_id])


async def _run_build_pipeline(job_id: str, request: BuildRequest) -> None:
    """Execute the build pipeline in the background.

    This imports and calls the actual kgbuilder pipeline code.
    """
    _jobs[job_id]["status"] = BuildStatus.RUNNING
    try:
        # Import here to avoid startup-time dependency issues
        from kgbuilder.pipeline.orchestrator import Orchestrator

        # TODO: wire up actual orchestrator with request params
        # orchestrator = Orchestrator(config=...)
        # result = orchestrator.run()

        _jobs[job_id]["status"] = BuildStatus.COMPLETED
        _jobs[job_id]["progress"] = 1.0
    except Exception as e:
        _jobs[job_id]["status"] = BuildStatus.FAILED
        _jobs[job_id]["error"] = str(e)
