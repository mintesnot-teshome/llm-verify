"""SQLAlchemy ORM models."""

from src.models.benchmark import BenchmarkRun  # noqa: F401
from src.models.result import BenchmarkResult  # noqa: F401

__all__ = ["BenchmarkRun", "BenchmarkResult"]
