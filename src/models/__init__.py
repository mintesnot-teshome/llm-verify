"""SQLAlchemy ORM models."""

from src.models.benchmark import BenchmarkRun
from src.models.result import BenchmarkResult

__all__ = ["BenchmarkResult", "BenchmarkRun"]
