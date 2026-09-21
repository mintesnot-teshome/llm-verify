"""FastAPI application entry point."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import Depends, FastAPI

from src.database import init_db
from src.handlers.analysis import router as analysis_router
from src.handlers.benchmarks import router as benchmarks_router
from src.handlers.results import router as results_router
from src.security import require_api_access


def _configure_logging() -> None:
    """Set up structlog with standard library integration."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — initialize DB on startup."""
    _configure_logging()
    await init_db()
    yield


app = FastAPI(
    title="LLM Verify",
    description="Detect fake AI APIs — LLM fingerprinting toolkit to verify model identity and catch AI model fraud",
    version="0.1.0",
    lifespan=lifespan,
)

protected = [Depends(require_api_access)]
app.include_router(analysis_router, prefix="/api/v1", dependencies=protected)
app.include_router(benchmarks_router, prefix="/api/v1", dependencies=protected)
app.include_router(results_router, prefix="/api/v1", dependencies=protected)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "ok"}
