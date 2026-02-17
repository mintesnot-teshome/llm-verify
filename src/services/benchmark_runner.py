"""Benchmark runner service — orchestrates running prompt suites against model adapters."""

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.base import CompletionResponse, ModelAdapter
from src.adapters.factory import create_adapter
from src.prompts import PROMPT_SUITES
from src.repositories.benchmark_repo import BenchmarkRepository
from src.repositories.result_repo import ResultRepository
from src.schemas.benchmark import BenchmarkRunCreate, BenchmarkRunResponse
from src.schemas.result import ModelConfig

logger = logging.getLogger(__name__)


class BenchmarkRunnerService:
    """Orchestrates benchmark runs: loads prompts, calls adapters, stores results."""

    def __init__(self, session: AsyncSession, max_concurrent: int = 5) -> None:
        self._session = session
        self._bench_repo = BenchmarkRepository(session)
        self._result_repo = ResultRepository(session)
        self._max_concurrent = max_concurrent

    async def run_benchmark(self, request: BenchmarkRunCreate) -> BenchmarkRunResponse:
        """Execute a full benchmark run.

        Args:
            request: The benchmark configuration including models and prompt suite.

        Returns:
            BenchmarkRunResponse with status and result count.
        """
        run = await self._bench_repo.create(
            name=request.name,
            description=request.description,
            prompt_suite=request.prompt_suite.value,
        )
        await self._bench_repo.update_status(run.id, "running")

        prompts = PROMPT_SUITES.get(request.prompt_suite.value, [])
        if not prompts:
            await self._bench_repo.update_status(run.id, "failed")
            return self._build_response(run, result_count=0)

        try:
            result_count = await self._execute_all(run.id, request.model_configs, prompts)
            await self._bench_repo.update_status(run.id, "completed", datetime.now(UTC))
        except Exception:
            logger.exception("Benchmark run %s failed", run.id)
            await self._bench_repo.update_status(run.id, "failed")
            result_count = 0

        updated_run = await self._bench_repo.get_by_id(run.id)
        return self._build_response(updated_run or run, result_count)

    async def _execute_all(
        self,
        run_id: str,
        model_configs: list[ModelConfig],
        prompts: list[dict[str, str]],
    ) -> int:
        """Execute all prompts against all models with concurrency limiting.

        Args:
            run_id: The parent benchmark run ID.
            model_configs: List of model configurations.
            prompts: List of prompt dictionaries.

        Returns:
            Total number of results stored.
        """
        semaphore = asyncio.Semaphore(self._max_concurrent)
        tasks: list[asyncio.Task[None]] = []

        for config in model_configs:
            adapter = create_adapter(config)
            for prompt in prompts:
                task = asyncio.create_task(
                    self._execute_single(semaphore, run_id, adapter, config, prompt)
                )
                tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)
        return len(tasks)

    async def _execute_single(
        self,
        semaphore: asyncio.Semaphore,
        run_id: str,
        adapter: ModelAdapter,
        config: ModelConfig,
        prompt: dict[str, str],
    ) -> None:
        """Execute a single prompt against a single model.

        Args:
            semaphore: Concurrency limiter.
            run_id: The parent benchmark run ID.
            adapter: The model adapter to use.
            config: Model configuration.
            prompt: Prompt dictionary with 'category' and 'text'.
        """
        async with semaphore:
            response = await self._safe_complete(adapter, prompt["text"])
            await self._store_result(run_id, config, prompt, response)

    async def _safe_complete(
        self,
        adapter: ModelAdapter,
        prompt_text: str,
    ) -> CompletionResponse:
        """Call adapter.complete with error handling.

        Args:
            adapter: The model adapter.
            prompt_text: The prompt to send.

        Returns:
            A CompletionResponse (may contain an error).
        """
        try:
            return await adapter.complete(prompt_text)
        except Exception as exc:
            logger.warning("Adapter error for %s: %s", adapter.model_name, exc)
            return CompletionResponse(text="", error=str(exc))

    async def _store_result(
        self,
        run_id: str,
        config: ModelConfig,
        prompt: dict[str, str],
        response: CompletionResponse,
    ) -> None:
        """Persist a single result to the database.

        Args:
            run_id: The parent benchmark run ID.
            config: Model configuration.
            prompt: The prompt that was sent.
            response: The response received.
        """
        await self._result_repo.create(
            benchmark_run_id=run_id,
            model_name=config.model_name,
            provider=config.provider,
            api_base_url=config.api_base_url,
            prompt_category=prompt["category"],
            prompt_text=prompt["text"],
            response_text=response.text,
            error_message=response.error,
            latency_ms=response.latency_ms,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
        )

    def _build_response(self, run: object, result_count: int) -> BenchmarkRunResponse:
        """Build a BenchmarkRunResponse from a BenchmarkRun ORM object.

        Args:
            run: The BenchmarkRun ORM instance.
            result_count: Number of results collected.

        Returns:
            A Pydantic response schema.
        """
        return BenchmarkRunResponse.model_validate(
            {
                "id": getattr(run, "id"),
                "name": getattr(run, "name"),
                "description": getattr(run, "description"),
                "status": getattr(run, "status"),
                "prompt_suite": getattr(run, "prompt_suite"),
                "created_at": getattr(run, "created_at"),
                "completed_at": getattr(run, "completed_at"),
                "result_count": result_count,
            }
        )
