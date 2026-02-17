"""BenchmarkRun ORM model — represents a single benchmark execution."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class BenchmarkRun(Base):
    """A single benchmark run against one or more models."""

    __tablename__ = "benchmark_runs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        doc="pending | running | completed | failed",
    )
    prompt_suite: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Which prompt suite was used (identity, capability, fingerprint)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    results: Mapped[list["BenchmarkResult"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "BenchmarkResult",
        back_populates="benchmark_run",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<BenchmarkRun id={self.id!r} name={self.name!r} status={self.status!r}>"
