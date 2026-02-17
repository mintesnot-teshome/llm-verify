"""Pydantic schemas for deep analysis requests and reports."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.schemas.result import ModelConfig


class DeepAnalysisRequest(BaseModel):
    """Request to run a deep analysis against one or more suspect models."""

    name: str = Field(
        default="Deep Analysis",
        min_length=1,
        max_length=255,
        description="Name for this analysis run",
    )
    model_configs: list[ModelConfig] = Field(
        ...,
        min_length=1,
        description="List of suspect model endpoints to analyze",
    )
    suites: list[str] = Field(
        default=["identity", "capability", "fingerprint"],
        description="Which prompt suites to run (default: all three)",
    )


class RedFlag(BaseModel):
    """A single red flag detected during analysis."""

    severity: str = Field(
        ...,
        description="HIGH, MEDIUM, or LOW",
    )
    category: str = Field(
        ...,
        description="Category (identity, consistency, latency, similarity, capability)",
    )
    description: str = Field(..., description="Human-readable explanation")
    evidence: str = Field(default="", description="Supporting data")


class ModelReport(BaseModel):
    """Analysis report for a single model."""

    model_name: str
    provider: str
    benchmark_run_ids: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of suite name → benchmark run ID",
    )
    identity_claims: list[str] = Field(
        default_factory=list,
        description="What the model claims to be from identity probes",
    )
    knowledge_cutoffs: list[str] = Field(
        default_factory=list,
        description="Knowledge cutoff dates mentioned",
    )
    avg_latency_ms: float = 0.0
    total_probes: int = 0
    errors: int = 0
    timeout_rate: float = 0.0
    fingerprint: dict[str, object] = Field(default_factory=dict)


class CrossModelComparison(BaseModel):
    """Comparison between two models to check if they're the same."""

    model_a: str
    model_b: str
    similarity_score: float = Field(
        ge=0.0,
        le=1.0,
        description="0.0 = completely different, 1.0 = likely same model",
    )
    shared_phrases: list[str] = Field(
        default_factory=list,
        description="Notable identical phrases across models",
    )
    verdict: str = Field(
        default="",
        description="SAME_MODEL, DIFFERENT_MODELS, or INCONCLUSIVE",
    )


class DeepAnalysisReport(BaseModel):
    """Complete deep analysis report with all findings."""

    name: str
    started_at: datetime
    completed_at: datetime | None = None
    model_reports: list[ModelReport] = Field(default_factory=list)
    cross_model_comparisons: list[CrossModelComparison] = Field(default_factory=list)
    red_flags: list[RedFlag] = Field(default_factory=list)
    verdict: str = Field(
        default="INCONCLUSIVE",
        description="FRAUD_DETECTED, LEGITIMATE, or INCONCLUSIVE",
    )
    summary: str = Field(default="", description="Human-readable summary")
