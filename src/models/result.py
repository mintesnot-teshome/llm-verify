"""BenchmarkResult ORM model — a single prompt/response result within a benchmark run."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class BenchmarkResult(Base):
    """One prompt-response pair from a benchmark run."""

    __tablename__ = "benchmark_results"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    benchmark_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("benchmark_runs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Model info ──
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="openai | anthropic | suspect | generic",
    )
    api_base_url: Mapped[str] = mapped_column(String(500), default="")

    # ── Prompt & Response ──
    prompt_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="identity | capability | fingerprint",
    )
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, default="")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Metrics ──
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Timestamps ──
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )

    benchmark_run: Mapped["BenchmarkRun"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "BenchmarkRun",
        back_populates="results",
    )

    def __repr__(self) -> str:
        return (
            f"<BenchmarkResult id={self.id!r} model={self.model_name!r} "
            f"category={self.prompt_category!r}>"
        )
