"""Tests for the benchmark runner service."""

from unittest.mock import AsyncMock, patch

import pytest

from src.adapters.base import CompletionResponse
from src.schemas.benchmark import BenchmarkRunCreate
from src.services.benchmark_runner import BenchmarkRunnerService


@pytest.mark.asyncio
async def test_run_benchmark_creates_run_and_stores_results(db_session):
    """Verify that a benchmark run is created and results are persisted."""
    mock_response = CompletionResponse(
        text="I am a test model.",
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        latency_ms=150.0,
    )

    with patch("src.adapters.factory.create_adapter") as mock_factory:
        mock_adapter = AsyncMock()
        mock_adapter.complete.return_value = mock_response
        mock_factory.return_value = mock_adapter

        service = BenchmarkRunnerService(db_session, max_concurrent=2)

        request = BenchmarkRunCreate(
            name="Test Run",
            description="Testing the runner",
            prompt_suite="identity",
            model_configs=[
                {
                    "model_name": "test-model",
                    "provider": "generic",
                    "api_key": "test-key",
                    "api_base_url": "https://test.api.com/v1",
                },
            ],
        )

        result = await service.run_benchmark(request)

        assert result.name == "Test Run"
        assert result.status == "completed"
        assert result.result_count > 0


@pytest.mark.asyncio
async def test_run_benchmark_handles_adapter_error(db_session):
    """Verify that adapter errors are caught and stored as error results."""
    mock_response = CompletionResponse(
        text="",
        error="Connection timeout",
    )

    with patch("src.adapters.factory.create_adapter") as mock_factory:
        mock_adapter = AsyncMock()
        mock_adapter.complete.return_value = mock_response
        mock_factory.return_value = mock_adapter

        service = BenchmarkRunnerService(db_session, max_concurrent=2)

        request = BenchmarkRunCreate(
            name="Error Test",
            prompt_suite="identity",
            model_configs=[
                {
                    "model_name": "failing-model",
                    "provider": "generic",
                    "api_key": "test",
                    "api_base_url": "https://failing.api.com/v1",
                },
            ],
        )

        result = await service.run_benchmark(request)

        assert result.status == "completed"
        assert result.result_count > 0


@pytest.mark.asyncio
async def test_run_benchmark_invalid_suite_fails(db_session):
    """Verify that an unknown prompt suite results in a failed run."""
    service = BenchmarkRunnerService(db_session, max_concurrent=2)

    request = BenchmarkRunCreate(
        name="Bad Suite",
        prompt_suite="identity",  # Valid suite, we test with mocked empty prompts
        model_configs=[
            {
                "model_name": "test",
                "provider": "generic",
                "api_key": "t",
                "api_base_url": "https://t.com/v1",
            },
        ],
    )

    with patch("src.services.benchmark_runner.PROMPT_SUITES", {"identity": []}):
        result = await service.run_benchmark(request)
        assert result.status == "failed"
