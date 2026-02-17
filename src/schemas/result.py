"""Pydantic schemas for benchmark results and model configuration."""

from datetime import datetime

from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Configuration for a single model endpoint to benchmark."""

    model_name: str = Field(..., min_length=1, max_length=100, description="Model identifier")
    provider: str = Field(
        ...,
        pattern=r"^(openai|anthropic|suspect|generic)$",
        description="Provider type",
    )
    api_key: str = Field(default="", description="API key (loaded from env if empty)")
    api_base_url: str = Field(default="", description="Base URL for the API")
    protocol: str = Field(
        default="",
        pattern=r"^(openai|anthropic|)$",
        description="API protocol to use (openai or anthropic). Auto-detected from provider if empty.",
    )


class BenchmarkResultResponse(BaseModel):
    """Response schema for a single benchmark result."""

    id: str
    benchmark_run_id: str
    model_name: str
    provider: str
    api_base_url: str
    prompt_category: str
    prompt_text: str
    response_text: str
    error_message: str | None = None
    latency_ms: float | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ComparisonRequest(BaseModel):
    """Request schema to compare two benchmark runs."""

    baseline_run_id: str = Field(..., description="ID of the trusted baseline run")
    suspect_run_id: str = Field(..., description="ID of the suspect run to compare")


class ComparisonScore(BaseModel):
    """Result of comparing two benchmark runs."""

    baseline_run_id: str
    suspect_run_id: str
    overall_similarity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="0.0 = completely different, 1.0 = identical behavior",
    )
    dimensions: dict[str, float] = Field(
        default_factory=dict,
        description="Similarity scores per dimension (latency, style, content, etc.)",
    )
    verdict: str = Field(
        ...,
        description="MATCH, MISMATCH, or INCONCLUSIVE",
    )
    details: str = Field(default="", description="Human-readable explanation")
