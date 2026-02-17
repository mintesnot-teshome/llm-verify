"""Benchmark run API handlers — create, list, and inspect benchmark runs."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings, get_settings
from src.database import get_session
from src.schemas.benchmark import BenchmarkRunCreate, BenchmarkRunResponse
from src.services.benchmark_runner import BenchmarkRunnerService

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


@router.post("/", response_model=BenchmarkRunResponse, status_code=201)
async def create_benchmark(
    request: BenchmarkRunCreate,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> BenchmarkRunResponse:
    """Start a new benchmark run.

    Accepts model configurations and a prompt suite, then runs all prompts
    against all specified models concurrently.
    """
    service = BenchmarkRunnerService(session, settings.max_concurrent_calls)
    return await service.run_benchmark(request)


@router.get("/", response_model=list[BenchmarkRunResponse])
async def list_benchmarks(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> list[BenchmarkRunResponse]:
    """List all benchmark runs, newest first."""
    from src.repositories.benchmark_repo import BenchmarkRepository

    repo = BenchmarkRepository(session)
    runs = await repo.list_all(limit=limit, offset=offset)
    return [
        BenchmarkRunResponse(
            id=run.id,
            name=run.name,
            description=run.description,
            status=run.status,
            prompt_suite=run.prompt_suite,
            created_at=run.created_at,
            completed_at=run.completed_at,
            result_count=len(run.results) if hasattr(run, "results") and run.results else 0,
        )
        for run in runs
    ]


@router.get("/{run_id}", response_model=BenchmarkRunResponse)
async def get_benchmark(
    run_id: str,
    session: AsyncSession = Depends(get_session),
) -> BenchmarkRunResponse:
    """Get a specific benchmark run by ID."""
    from src.repositories.benchmark_repo import BenchmarkRepository

    repo = BenchmarkRepository(session)
    run = await repo.get_by_id(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Benchmark run {run_id!r} not found")

    return BenchmarkRunResponse(
        id=run.id,
        name=run.name,
        description=run.description,
        status=run.status,
        prompt_suite=run.prompt_suite,
        created_at=run.created_at,
        completed_at=run.completed_at,
        result_count=len(run.results) if run.results else 0,
    )
