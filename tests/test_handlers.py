"""Regression tests for API handler data loading and model scoping."""

import pytest
from fastapi import HTTPException

from src.handlers.benchmarks import list_benchmarks
from src.handlers.results import get_fingerprint
from src.repositories.benchmark_repo import BenchmarkRepository
from src.repositories.result_repo import ResultRepository


@pytest.mark.asyncio
async def test_list_benchmarks_eager_loads_result_counts(db_session) -> None:
    repo = BenchmarkRepository(db_session)
    await repo.create("Review run", "", "identity")
    await db_session.commit()
    db_session.expire_all()

    response = await list_benchmarks(session=db_session)

    assert response[0].result_count == 0


@pytest.mark.asyncio
async def test_fingerprint_requires_model_for_multi_model_run(db_session) -> None:
    benchmark_repo = BenchmarkRepository(db_session)
    result_repo = ResultRepository(db_session)
    run = await benchmark_repo.create("Multi-model", "", "identity")

    for model_name in ("model-a", "model-b"):
        await result_repo.create(
            benchmark_run_id=run.id,
            model_name=model_name,
            provider="generic",
            api_base_url="https://example.com/v1",
            prompt_category="identity",
            prompt_text="Who are you?",
            response_text=f"I am {model_name}.",
        )

    with pytest.raises(HTTPException) as exc_info:
        await get_fingerprint(run_id=run.id, session=db_session)

    assert exc_info.value.status_code == 400
    assert "model_name" in exc_info.value.detail

    fingerprint = await get_fingerprint(
        run_id=run.id,
        session=db_session,
        model_name="model-a",
    )
    assert fingerprint["metadata"]["total_results"] == 1
