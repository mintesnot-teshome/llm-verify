"""Repository for BenchmarkResult CRUD operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.result import BenchmarkResult


class ResultRepository:
    """Database access layer for benchmark results."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        benchmark_run_id: str,
        model_name: str,
        provider: str,
        api_base_url: str,
        prompt_category: str,
        prompt_text: str,
        response_text: str,
        error_message: str | None = None,
        latency_ms: float | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> BenchmarkResult:
        """Store a single benchmark result.

        Args:
            benchmark_run_id: Parent benchmark run ID.
            model_name: Name of the model tested.
            provider: Provider type (openai, anthropic, etc.).
            api_base_url: API endpoint URL.
            prompt_category: Category of the prompt (identity, capability, fingerprint).
            prompt_text: The prompt that was sent.
            response_text: The model's response.
            error_message: Error message if the call failed.
            latency_ms: Response latency in milliseconds.
            prompt_tokens: Number of prompt tokens used.
            completion_tokens: Number of completion tokens used.
            total_tokens: Total tokens used.

        Returns:
            The created BenchmarkResult.
        """
        result = BenchmarkResult(
            benchmark_run_id=benchmark_run_id,
            model_name=model_name,
            provider=provider,
            api_base_url=api_base_url,
            prompt_category=prompt_category,
            prompt_text=prompt_text,
            response_text=response_text,
            error_message=error_message,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        self._session.add(result)
        await self._session.flush()
        return result

    async def get_by_run_id(self, benchmark_run_id: str) -> list[BenchmarkResult]:
        """Fetch all results for a specific benchmark run.

        Args:
            benchmark_run_id: The parent run ID.

        Returns:
            List of BenchmarkResult objects.
        """
        stmt = (
            select(BenchmarkResult)
            .where(BenchmarkResult.benchmark_run_id == benchmark_run_id)
            .order_by(BenchmarkResult.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_run_and_model(
        self,
        benchmark_run_id: str,
        model_name: str,
    ) -> list[BenchmarkResult]:
        """Fetch results for a specific model within a benchmark run.

        Args:
            benchmark_run_id: The parent run ID.
            model_name: Filter by this model name.

        Returns:
            Filtered list of BenchmarkResult objects.
        """
        stmt = (
            select(BenchmarkResult)
            .where(
                BenchmarkResult.benchmark_run_id == benchmark_run_id,
                BenchmarkResult.model_name == model_name,
            )
            .order_by(BenchmarkResult.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
