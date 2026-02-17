"""Pydantic schemas for benchmark runs."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class PromptSuite(StrEnum):
    """Available prompt suites for benchmarking."""

    IDENTITY = "identity"
    CAPABILITY = "capability"
    FINGERPRINT = "fingerprint"


class BenchmarkRunStatus(StrEnum):
    """Possible states of a benchmark run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BenchmarkRunCreate(BaseModel):
    """Request schema to start a new benchmark run."""

    name: str = Field(..., min_length=1, max_length=255, description="Name for this benchmark run")
    description: str = Field(default="", max_length=2000)
    prompt_suite: PromptSuite = Field(
        default=PromptSuite.IDENTITY,
        description="Which prompt suite to run",
    )
    model_configs: list["ModelConfig"] = Field(  # type: ignore[name-defined]  # noqa: F821
        ...,
        min_length=1,
        description="List of model endpoints to benchmark",
    )


class BenchmarkRunResponse(BaseModel):
    """Response schema for a benchmark run."""

    id: str
    name: str
    description: str
    status: BenchmarkRunStatus
    prompt_suite: PromptSuite
    created_at: datetime
    completed_at: datetime | None = None
    result_count: int = 0

    model_config = {"from_attributes": True}


# Resolve forward reference after ModelConfig is importable
from src.schemas.result import ModelConfig  # noqa: E402, F811

BenchmarkRunCreate.model_rebuild()
