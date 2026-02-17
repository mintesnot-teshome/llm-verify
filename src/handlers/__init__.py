"""API route handlers."""

from src.handlers.analysis import router as analysis_router  # noqa: F401
from src.handlers.benchmarks import router as benchmarks_router  # noqa: F401
from src.handlers.results import router as results_router  # noqa: F401

__all__ = ["analysis_router", "benchmarks_router", "results_router"]
