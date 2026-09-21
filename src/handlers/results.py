"""Results & comparison API handlers."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.repositories.result_repo import ResultRepository
from src.schemas.result import BenchmarkResultResponse, ComparisonRequest, ComparisonScore
from src.services.fingerprint import FingerprintService
from src.services.model_comparator import ModelComparatorService

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/{run_id}", response_model=list[BenchmarkResultResponse])
async def get_results(
    run_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    model_name: str | None = None,
) -> list[BenchmarkResultResponse]:
    """Get all results for a benchmark run, optionally filtered by model.

    Args:
        run_id: The benchmark run ID.
        model_name: Optional model name filter.
        session: Database session.
    """
    repo = ResultRepository(session)

    if model_name:
        results = await repo.get_by_run_and_model(run_id, model_name)
    else:
        results = await repo.get_by_run_id(run_id)

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No results found for run {run_id!r}",
        )

    return [BenchmarkResultResponse.model_validate(r) for r in results]


@router.post("/compare", response_model=ComparisonScore)
async def compare_runs(
    request: ComparisonRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ComparisonScore:
    """Compare two benchmark runs to detect model identity.

    Compares a trusted baseline run against a suspect run across
    multiple dimensions (latency, response length, token usage, error rate).
    """
    comparator = ModelComparatorService(session)
    return await comparator.compare(request)


@router.get("/{run_id}/fingerprint")
async def get_fingerprint(
    run_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    model_name: str | None = None,
) -> dict[str, object]:
    """Generate a behavioral fingerprint for a model from a benchmark run.

    Args:
        run_id: The benchmark run ID.
        model_name: Optional model name; required when a run contains multiple models.
        session: Database session.
    """
    repo = ResultRepository(session)

    if model_name:
        results = await repo.get_by_run_and_model(run_id, model_name)
    else:
        results = await repo.get_by_run_id(run_id)
        model_names = sorted({result.model_name for result in results})
        if len(model_names) > 1:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This run contains multiple models; provide the model_name query parameter. "
                    f"Available models: {', '.join(model_names)}"
                ),
            )

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No results found for run {run_id!r}",
        )

    fingerprinter = FingerprintService()
    return fingerprinter.generate_fingerprint(results)
