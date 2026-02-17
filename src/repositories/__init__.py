"""Database repositories."""

from src.repositories.benchmark_repo import BenchmarkRepository  # noqa: F401
from src.repositories.result_repo import ResultRepository  # noqa: F401

__all__ = ["BenchmarkRepository", "ResultRepository"]
