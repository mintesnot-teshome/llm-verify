"""API route handlers."""

from src.handlers.benchmarks import router as benchmarks_router  # noqa: F401
from src.handlers.results import router as results_router  # noqa: F401

__all__ = ["benchmarks_router", "results_router"]
