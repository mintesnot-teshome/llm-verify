"""Tests for the model comparator service."""

import pytest

from src.models.result import BenchmarkResult
from src.repositories.result_repo import ResultRepository
from src.schemas.result import ComparisonRequest
from src.services.model_comparator import ModelComparatorService


async def _create_results(
    repo: ResultRepository,
    run_id: str,
    model_name: str,
    count: int = 5,
    latency_base: float = 200.0,
    response_length: int = 500,
    error_count: int = 0,
) -> None:
    """Helper to create mock benchmark results for testing."""
    for i in range(count):
        is_error = i < error_count
        await repo.create(
            benchmark_run_id=run_id,
            model_name=model_name,
            provider="generic",
            api_base_url="https://test.com/v1",
            prompt_category="identity",
            prompt_text=f"Test prompt {i}",
            response_text="" if is_error else "x" * response_length,
            error_message="Error" if is_error else None,
            latency_ms=latency_base + (i * 10),
            prompt_tokens=50,
            completion_tokens=100,
            total_tokens=150,
        )


@pytest.mark.asyncio
async def test_compare_similar_runs_returns_match(db_session):
    """Two runs with similar metrics should return MATCH."""
    from src.repositories.benchmark_repo import BenchmarkRepository

    bench_repo = BenchmarkRepository(db_session)
    result_repo = ResultRepository(db_session)

    run1 = await bench_repo.create("Baseline", "", "identity")
    run2 = await bench_repo.create("Suspect", "", "identity")

    await _create_results(result_repo, run1.id, "gpt-4o", latency_base=200, response_length=500)
    await _create_results(
        result_repo, run2.id, "suspect-model", latency_base=210, response_length=490
    )

    comparator = ModelComparatorService(db_session)
    score = await comparator.compare(
        ComparisonRequest(baseline_run_id=run1.id, suspect_run_id=run2.id)
    )

    assert score.verdict == "MATCH"
    assert score.overall_similarity >= 0.80


@pytest.mark.asyncio
async def test_compare_different_runs_returns_mismatch(db_session):
    """Two runs with very different metrics should return MISMATCH."""
    from src.repositories.benchmark_repo import BenchmarkRepository

    bench_repo = BenchmarkRepository(db_session)
    result_repo = ResultRepository(db_session)

    run1 = await bench_repo.create("Baseline", "", "identity")
    run2 = await bench_repo.create("Suspect", "", "identity")

    await _create_results(result_repo, run1.id, "gpt-4o", latency_base=200, response_length=1000)
    await _create_results(
        result_repo,
        run2.id,
        "suspect-model",
        latency_base=2000,
        response_length=100,
        error_count=3,
    )

    comparator = ModelComparatorService(db_session)
    score = await comparator.compare(
        ComparisonRequest(baseline_run_id=run1.id, suspect_run_id=run2.id)
    )

    assert score.verdict == "MISMATCH"
    assert score.overall_similarity <= 0.50


@pytest.mark.asyncio
async def test_compare_empty_runs_returns_inconclusive(db_session):
    """Runs with no results should return INCONCLUSIVE."""
    comparator = ModelComparatorService(db_session)
    score = await comparator.compare(
        ComparisonRequest(baseline_run_id="nonexistent-1", suspect_run_id="nonexistent-2")
    )

    assert score.verdict == "INCONCLUSIVE"
